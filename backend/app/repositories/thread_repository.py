"""Thread repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.email import Email
from app.models.email_thread import EmailThread


class ThreadRepository:
    """Data access for conversation threads."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> EmailThread:
        thread = EmailThread(**kwargs)
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def get_by_id(self, thread_id: uuid.UUID) -> EmailThread | None:
        result = await self.session.execute(
            select(EmailThread).where(EmailThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def get_with_emails(self, thread_id: uuid.UUID) -> EmailThread | None:
        result = await self.session.execute(
            select(EmailThread)
            .options(selectinload(EmailThread.emails))
            .where(EmailThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def get_by_root_message_id(self, root_message_id: str) -> EmailThread | None:
        result = await self.session.execute(
            select(EmailThread).where(EmailThread.root_message_id == root_message_id)
        )
        return result.scalar_one_or_none()

    async def get_by_normalized_subject(self, subject_normalized: str) -> EmailThread | None:
        result = await self.session.execute(
            select(EmailThread).where(EmailThread.subject_normalized == subject_normalized)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(EmailThread))
        return int(result.scalar_one())

    async def list_threads(self, skip: int = 0, limit: int = 20) -> list[EmailThread]:
        result = await self.session.execute(
            select(EmailThread)
            .order_by(EmailThread.last_email_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_stats(
        self,
        thread: EmailThread,
        *,
        participant_count: int,
        email_count: int,
        first_email_at: datetime | None,
        last_email_at: datetime | None,
        summary: str | None = None,
    ) -> EmailThread:
        thread.participant_count = participant_count
        thread.email_count = email_count
        thread.first_email_at = first_email_at
        thread.last_email_at = last_email_at
        if summary is not None:
            thread.summary = summary
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def thread_size_distribution(self) -> dict[str, int]:
        """Bucket thread sizes for analytics charts."""
        result = await self.session.execute(
            select(EmailThread.email_count).order_by(EmailThread.email_count)
        )
        counts = [int(value) for value in result.scalars().all()]

        distribution = {"1": 0, "2-5": 0, "6-10": 0, "11+": 0}
        for count in counts:
            if count <= 1:
                distribution["1"] += 1
            elif count <= 5:
                distribution["2-5"] += 1
            elif count <= 10:
                distribution["6-10"] += 1
            else:
                distribution["11+"] += 1
        return distribution

    async def emails_in_thread(self, thread_id: uuid.UUID) -> list[Email]:
        result = await self.session.execute(
            select(Email)
            .where(Email.thread_id == thread_id)
            .order_by(Email.sent_at.asc().nullsfirst(), Email.created_at.asc())
        )
        return list(result.scalars().all())
