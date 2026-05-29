"""Conversation thread reconstruction service."""

import logging
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email
from app.repositories.email_repository import EmailRepository
from app.repositories.thread_repository import ThreadRepository
from app.services.summary_service import SummaryService
from app.utils.email_helpers import normalize_subject

logger = logging.getLogger(__name__)


class ThreadReconstructionService:
    """Rebuild email conversation threads from headers and subject heuristics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.email_repo = EmailRepository(session)
        self.thread_repo = ThreadRepository(session)
        self.summary_service = SummaryService()

    async def rebuild_all_threads(self) -> int:
        """Reconstruct threads for all emails in the database."""
        emails = await self.email_repo.list_all_for_threading()
        if not emails:
            return 0

        message_map = {
            email.message_id: email for email in emails if email.message_id
        }
        groups: dict[str, list[Email]] = defaultdict(list)
        assigned: set[uuid.UUID] = set()

        for email in emails:
            parent_id = email.in_reply_to
            root_id = self._resolve_root_message_id(email, message_map)
            if root_id:
                groups[f"msg:{root_id}"].append(email)
                assigned.add(email.id)
            elif parent_id and parent_id in message_map:
                groups[f"msg:{parent_id}"].append(email)
                assigned.add(email.id)

        subject_groups: dict[str, list[Email]] = defaultdict(list)
        for email in emails:
            if email.id in assigned:
                continue
            if email.subject:
                subject_groups[normalize_subject(email.subject)].append(email)

        for subject, subject_emails in subject_groups.items():
            if subject_emails:
                groups[f"subject:{subject}"].extend(subject_emails)

        thread_count = 0
        for key, group_emails in groups.items():
            if group_emails:
                await self._persist_thread(group_emails, key)
                thread_count += 1

        await self.session.commit()
        logger.info("Reconstructed %s conversation threads", thread_count)
        return thread_count

    async def rebuild_threads_for_archive(self, archive_id: uuid.UUID) -> int:
        """Reconstruct threads for emails belonging to a single archive."""
        emails = await self.email_repo.list_by_archive(archive_id)
        if not emails:
            return 0

        subject_groups: dict[str, list[Email]] = defaultdict(list)
        for email in emails:
            subject_key = normalize_subject(email.subject) or f"archive-{archive_id}"
            subject_groups[subject_key].append(email)

        thread_count = 0
        for subject, group_emails in subject_groups.items():
            await self._persist_thread(group_emails, f"subject:{subject}")
            thread_count += 1

        await self.session.commit()
        return thread_count

    async def _persist_thread(self, emails: list[Email], group_key: str) -> None:
        emails = sorted(
            emails,
            key=lambda item: (item.sent_at or datetime.min, item.created_at),
        )

        root_message_id = None
        for email in emails:
            if email.message_id and not email.in_reply_to:
                root_message_id = email.message_id
                break
        if not root_message_id and emails[0].message_id:
            root_message_id = emails[0].message_id

        subject_normalized = normalize_subject(emails[0].subject) or group_key
        participants = set()
        for email in emails:
            if email.sender:
                participants.add(email.sender)
            participants.update(email.receivers)
            participants.update(email.cc)

        first_at = next((email.sent_at for email in emails if email.sent_at), None)
        last_at = next((email.sent_at for email in reversed(emails) if email.sent_at), None)

        thread = await self.thread_repo.get_by_root_message_id(root_message_id) if root_message_id else None
        if not thread:
            thread = await self.thread_repo.get_by_normalized_subject(subject_normalized)

        if not thread:
            thread = await self.thread_repo.create(
                subject_normalized=subject_normalized,
                root_message_id=root_message_id,
                participant_count=len(participants),
                email_count=len(emails),
                first_email_at=first_at,
                last_email_at=last_at,
            )
        else:
            thread = await self.thread_repo.update_stats(
                thread,
                participant_count=len(participants),
                email_count=len(emails),
                first_email_at=first_at,
                last_email_at=last_at,
            )

        for email in emails:
            await self.email_repo.update_thread_id(email, thread.id)

        if len(emails) > 1:
            thread_summary = self.summary_service.summarize_thread(
                [email.subject for email in emails],
                [email.body_text for email in emails],
            )
            await self.thread_repo.update_stats(
                thread,
                participant_count=len(participants),
                email_count=len(emails),
                first_email_at=first_at,
                last_email_at=last_at,
                summary=thread_summary,
            )

    @staticmethod
    def _resolve_root_message_id(email: Email, message_map: dict[str, Email]) -> str | None:
        if email.references_header:
            refs = email.references_header.replace("\n", " ").split()
            for ref in refs:
                cleaned = ref.strip("<>")
                if cleaned in message_map:
                    return cleaned

        if email.in_reply_to and email.in_reply_to in message_map:
            parent = message_map[email.in_reply_to]
            return parent.message_id or email.in_reply_to

        return email.message_id
