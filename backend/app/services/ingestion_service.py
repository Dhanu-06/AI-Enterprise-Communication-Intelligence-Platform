"""Email archive ingestion orchestration service."""

import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.email import Email
from app.models.email_archive import ArchiveStatus
from app.repositories.archive_repository import ArchiveRepository
from app.repositories.email_repository import EmailRepository
from app.services.chroma_service import ChromaService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.email_parser import EmailParserService
from app.services.summary_service import SummaryService
from app.services.thread_service import ThreadReconstructionService
from app.services.zip_extractor import ZipExtractorService

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrate ZIP upload processing end-to-end."""

    def __init__(
        self,
        elasticsearch_service: ElasticsearchService,
        chroma_service: ChromaService,
    ) -> None:
        self.elasticsearch_service = elasticsearch_service
        self.chroma_service = chroma_service
        self.zip_extractor = ZipExtractorService()
        self.email_parser = EmailParserService()
        self.summary_service = SummaryService()

    async def process_archive(self, archive_id: uuid.UUID) -> None:
        """Background task: extract, parse, store, index, and summarize emails."""
        async with async_session_factory() as session:
            archive_repo = ArchiveRepository(session)
            email_repo = EmailRepository(session)

            archive = await archive_repo.get_by_id(archive_id)
            if not archive:
                logger.error("Archive not found: %s", archive_id)
                return

            extract_dir = Path(settings.upload_dir) / "extracted" / str(archive_id)

            try:
                await archive_repo.update_status(archive, ArchiveStatus.PROCESSING)
                await session.commit()

                email_files = self.zip_extractor.extract(Path(archive.file_path), extract_dir)
                await archive_repo.update_status(archive, ArchiveStatus.PROCESSING, total_emails=len(email_files))
                await session.commit()

                persisted_emails: list[Email] = []
                for index, file_path in enumerate(email_files, start=1):
                    parsed = self.email_parser.parse_file(file_path)
                    if not parsed:
                        continue

                    summary = self.summary_service.summarize(parsed.subject, parsed.body_text)
                    email = await email_repo.create(
                        archive_id=archive.id,
                        message_id=parsed.message_id,
                        in_reply_to=parsed.in_reply_to,
                        references_header=parsed.references_header,
                        sender=parsed.sender,
                        receivers=parsed.receivers,
                        cc=parsed.cc,
                        subject=parsed.subject,
                        body_text=parsed.body_text,
                        body_html=parsed.body_html,
                        sent_at=parsed.sent_at,
                        summary=summary,
                        source_file=parsed.source_file,
                    )
                    persisted_emails.append(email)

                    if index % 10 == 0:
                        await archive_repo.update_status(
                            archive,
                            ArchiveStatus.PROCESSING,
                            processed_emails=index,
                        )
                        await session.commit()

                await session.commit()

                thread_service = ThreadReconstructionService(session)
                await thread_service.rebuild_threads_for_archive(archive.id)

                refreshed_emails = await email_repo.list_by_archive(archive.id)

                if settings.elasticsearch_enabled:
                    try:
                        if not self.elasticsearch_service.is_connected:
                            await self.elasticsearch_service.connect()
                        await self.elasticsearch_service.bulk_index_emails(refreshed_emails)
                    except Exception as exc:
                        logger.warning("Elasticsearch indexing skipped: %s", exc)

                if settings.chroma_enabled:
                    try:
                        if not self.chroma_service.is_connected:
                            self.chroma_service.connect()
                        self.chroma_service.bulk_index_emails(refreshed_emails)
                    except Exception as exc:
                        logger.warning("ChromaDB indexing skipped: %s", exc)

                for email in refreshed_emails:
                    await email_repo.update_index_ids(
                        email,
                        elasticsearch_id=str(email.id),
                        chroma_id=str(email.id),
                    )

                await archive_repo.update_status(
                    archive,
                    ArchiveStatus.COMPLETED,
                    total_emails=len(email_files),
                    processed_emails=len(persisted_emails),
                )
                await session.commit()
                logger.info(
                    "Archive %s processed: %s/%s emails",
                    archive_id,
                    len(persisted_emails),
                    len(email_files),
                )

            except Exception as exc:
                logger.exception("Archive processing failed: %s", archive_id)
                await session.rollback()
                archive = await archive_repo.get_by_id(archive_id)
                if archive:
                    await archive_repo.update_status(
                        archive,
                        ArchiveStatus.FAILED,
                        error_message=str(exc),
                    )
                    await session.commit()
            finally:
                self.zip_extractor.cleanup(extract_dir)

    async def save_upload(self, session: AsyncSession, filename: str, file_bytes: bytes) -> uuid.UUID:
        """Persist uploaded ZIP to disk and create archive record."""
        archive_id = uuid.uuid4()
        upload_dir = Path(settings.upload_dir) / "archives"
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(filename).name
        file_path = upload_dir / f"{archive_id}_{safe_name}"
        file_path.write_bytes(file_bytes)

        archive_repo = ArchiveRepository(session)
        archive = await archive_repo.create(filename=safe_name, file_path=str(file_path))
        await session.commit()
        return archive.id
