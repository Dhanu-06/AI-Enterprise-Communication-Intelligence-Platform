"""Archive repository."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_archive import ArchiveStatus, EmailArchive


class ArchiveRepository:
    """Data access for email archive uploads."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, filename: str, file_path: str) -> EmailArchive:
        archive = EmailArchive(filename=filename, file_path=file_path)
        self.session.add(archive)
        await self.session.flush()
        await self.session.refresh(archive)
        return archive

    async def get_by_id(self, archive_id: uuid.UUID) -> EmailArchive | None:
        result = await self.session.execute(
            select(EmailArchive).where(EmailArchive.id == archive_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[EmailArchive]:
        result = await self.session.execute(
            select(EmailArchive)
            .order_by(EmailArchive.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(EmailArchive))
        return int(result.scalar_one())

    async def update_status(
        self,
        archive: EmailArchive,
        status: ArchiveStatus,
        *,
        total_emails: int | None = None,
        processed_emails: int | None = None,
        error_message: str | None = None,
    ) -> EmailArchive:
        archive.status = status
        if total_emails is not None:
            archive.total_emails = total_emails
        if processed_emails is not None:
            archive.processed_emails = processed_emails
        if error_message is not None:
            archive.error_message = error_message
        await self.session.flush()
        await self.session.refresh(archive)
        return archive
