"""Email-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class EmailBase(ORMModel):
    """Shared email fields."""

    sender: str
    receivers: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    subject: str = ""
    body_text: str = ""
    sent_at: datetime | None = None
    summary: str | None = None


class EmailResponse(EmailBase):
    """Full email record returned by the API."""

    id: UUID
    archive_id: UUID
    thread_id: UUID | None = None
    message_id: str | None = None
    in_reply_to: str | None = None
    source_file: str | None = None
    created_at: datetime


class EmailListItem(ORMModel):
    """Lightweight email for list views."""

    id: UUID
    sender: str
    subject: str
    sent_at: datetime | None = None
    summary: str | None = None
    thread_id: UUID | None = None


class SimilarEmailResult(ORMModel):
    """Similar email recommendation."""

    id: UUID
    subject: str
    sender: str
    sent_at: datetime | None = None
    similarity_score: float
    summary: str | None = None


class EmailDetailResponse(EmailResponse):
    """Email with thread context and recommendations."""

    thread_subject: str | None = None
    similar_emails: list[SimilarEmailResult] = Field(default_factory=list)


class ThreadResponse(ORMModel):
    """Reconstructed conversation thread."""

    id: UUID
    subject_normalized: str
    participant_count: int
    email_count: int
    first_email_at: datetime | None = None
    last_email_at: datetime | None = None
    summary: str | None = None
    emails: list[EmailListItem] = Field(default_factory=list)


class ParsedEmailData(ORMModel):
    """Intermediate parsed email before persistence."""

    message_id: str | None = None
    in_reply_to: str | None = None
    references_header: str | None = None
    sender: str = ""
    receivers: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    subject: str = ""
    body_text: str = ""
    body_html: str | None = None
    sent_at: datetime | None = None
    source_file: str | None = None
