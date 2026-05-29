"""Analytics dashboard Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class SenderStats(BaseModel):
    """Email volume per sender."""

    sender: str
    count: int


class DailyVolume(BaseModel):
    """Emails sent on a given day."""

    date: str
    count: int


class SubjectKeyword(BaseModel):
    """Frequent subject terms."""

    keyword: str
    count: int


class AnalyticsOverview(BaseModel):
    """High-level communication analytics."""

    total_emails: int
    total_threads: int
    total_archives: int
    unique_senders: int
    unique_receivers: int
    emails_with_summary: int
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None


class AnalyticsDashboard(BaseModel):
    """Full analytics payload for the dashboard."""

    overview: AnalyticsOverview
    top_senders: list[SenderStats]
    daily_volume: list[DailyVolume]
    top_subjects: list[SubjectKeyword]
    thread_size_distribution: dict[str, int]
