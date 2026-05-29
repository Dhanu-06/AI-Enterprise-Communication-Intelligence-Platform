"""Email repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.email import Email
from app.models.email_thread import EmailThread


class EmailRepository:
    """Data access for parsed email records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Email:
        email = Email(**kwargs)
        self.session.add(email)
        await self.session.flush()
        await self.session.refresh(email)
        return email

    async def bulk_create(self, emails: list[Email]) -> list[Email]:
        self.session.add_all(emails)
        await self.session.flush()
        for email in emails:
            await self.session.refresh(email)
        return emails

    async def get_by_id(self, email_id: uuid.UUID) -> Email | None:
        result = await self.session.execute(select(Email).where(Email.id == email_id))
        return result.scalar_one_or_none()

    async def get_by_ids(self, email_ids: list[uuid.UUID]) -> list[Email]:
        if not email_ids:
            return []
        result = await self.session.execute(select(Email).where(Email.id.in_(email_ids)))
        emails = list(result.scalars().all())
        email_map = {email.id: email for email in emails}
        return [email_map[email_id] for email_id in email_ids if email_id in email_map]

    async def get_by_message_id(self, message_id: str) -> Email | None:
        result = await self.session.execute(
            select(Email).where(Email.message_id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_emails(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        sender: str | None = None,
        thread_id: uuid.UUID | None = None,
    ) -> list[Email]:
        query = select(Email).order_by(Email.sent_at.desc().nullslast(), Email.created_at.desc())

        if sender:
            query = query.where(Email.sender.ilike(f"%{sender}%"))
        if thread_id:
            query = query.where(Email.thread_id == thread_id)

        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(
        self,
        *,
        sender: str | None = None,
        thread_id: uuid.UUID | None = None,
    ) -> int:
        query = select(func.count()).select_from(Email)
        if sender:
            query = query.where(Email.sender.ilike(f"%{sender}%"))
        if thread_id:
            query = query.where(Email.thread_id == thread_id)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_with_summary(self) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Email)
            .where(Email.summary.is_not(None), Email.summary != "")
        )
        return int(result.scalar_one())

    async def count_unique_senders(self) -> int:
        result = await self.session.execute(select(func.count(func.distinct(Email.sender))))
        return int(result.scalar_one())

    async def count_unique_receivers(self) -> int:
        result = await self.session.execute(
            select(func.unnest(Email.receivers).label("receiver")).distinct()
        )
        return len(result.scalars().all())

    async def get_date_range(self) -> tuple[datetime | None, datetime | None]:
        result = await self.session.execute(
            select(func.min(Email.sent_at), func.max(Email.sent_at))
        )
        start, end = result.one()
        return start, end

    async def top_senders(self, limit: int = 10) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(Email.sender, func.count())
            .group_by(Email.sender)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [(sender, int(count)) for sender, count in result.all()]

    async def daily_volume(self, limit: int = 30) -> list[tuple[str, int]]:
        day = func.date_trunc("day", Email.sent_at).label("day")
        result = await self.session.execute(
            select(day, func.count())
            .where(Email.sent_at.is_not(None))
            .group_by(day)
            .order_by(day.desc())
            .limit(limit)
        )
        rows = result.all()
        return [(row[0].date().isoformat(), int(row[1])) for row in rows if row[0]]

    async def top_subjects(self, limit: int = 10) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(Email.subject, func.count())
            .where(Email.subject != "")
            .group_by(Email.subject)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [(subject, int(count)) for subject, count in result.all()]

    async def update_thread_id(self, email: Email, thread_id: uuid.UUID) -> Email:
        email.thread_id = thread_id
        await self.session.flush()
        return email

    async def update_summary(self, email: Email, summary: str) -> Email:
        email.summary = summary
        await self.session.flush()
        return email

    async def update_index_ids(
        self,
        email: Email,
        *,
        elasticsearch_id: str | None = None,
        chroma_id: str | None = None,
    ) -> Email:
        if elasticsearch_id is not None:
            email.elasticsearch_id = elasticsearch_id
        if chroma_id is not None:
            email.chroma_id = chroma_id
        await self.session.flush()
        return email

    async def list_by_archive(self, archive_id: uuid.UUID) -> list[Email]:
        result = await self.session.execute(
            select(Email)
            .where(Email.archive_id == archive_id)
            .order_by(Email.sent_at.asc().nullsfirst())
        )
        return list(result.scalars().all())

    async def list_all_for_threading(self) -> list[Email]:
        result = await self.session.execute(
            select(Email).order_by(Email.sent_at.asc().nullsfirst(), Email.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Email]:
        """Return all emails (used for bulk reindex operations)."""
        result = await self.session.execute(
            select(Email).order_by(Email.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_with_thread(self, email_id: uuid.UUID) -> tuple[Email | None, EmailThread | None]:
        result = await self.session.execute(
            select(Email)
            .options(selectinload(Email.thread))
            .where(Email.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            return None, None
        return email, email.thread
