"""Communication analytics service."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.archive_repository import ArchiveRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.thread_repository import ThreadRepository
from app.schemas.analytics import (
    AnalyticsDashboard,
    AnalyticsOverview,
    DailyVolume,
    SenderStats,
    SubjectKeyword,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Aggregate communication metrics for the dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.email_repo = EmailRepository(session)
        self.thread_repo = ThreadRepository(session)
        self.archive_repo = ArchiveRepository(session)

    async def get_dashboard(self) -> AnalyticsDashboard:
        date_start, date_end = await self.email_repo.get_date_range()
        unique_receivers = await self._count_unique_receivers()

        overview = AnalyticsOverview(
            total_emails=await self.email_repo.count(),
            total_threads=await self.thread_repo.count(),
            total_archives=await self.archive_repo.count(),
            unique_senders=await self.email_repo.count_unique_senders(),
            unique_receivers=unique_receivers,
            emails_with_summary=await self.email_repo.count_with_summary(),
            date_range_start=date_start,
            date_range_end=date_end,
        )

        top_senders = [
            SenderStats(sender=sender, count=count)
            for sender, count in await self.email_repo.top_senders(limit=10)
        ]
        daily_volume = [
            DailyVolume(date=day, count=count)
            for day, count in reversed(await self.email_repo.daily_volume(limit=30))
        ]
        top_subjects = [
            SubjectKeyword(keyword=subject, count=count)
            for subject, count in await self.email_repo.top_subjects(limit=10)
        ]
        thread_distribution = await self.thread_repo.thread_size_distribution()

        return AnalyticsDashboard(
            overview=overview,
            top_senders=top_senders,
            daily_volume=daily_volume,
            top_subjects=top_subjects,
            thread_size_distribution=thread_distribution,
        )

    async def _count_unique_receivers(self) -> int:
        result = await self.session.execute(
            text("SELECT COUNT(DISTINCT receiver) FROM emails, unnest(receivers) AS receiver")
        )
        value = result.scalar_one()
        return int(value or 0)
