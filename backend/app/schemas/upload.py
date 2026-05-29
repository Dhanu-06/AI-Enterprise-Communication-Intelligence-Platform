"""Upload archive Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from app.models.email_archive import ArchiveStatus
from app.schemas.common import ORMModel


class ArchiveResponse(ORMModel):
    """Uploaded archive metadata."""

    id: UUID
    filename: str
    status: ArchiveStatus
    total_emails: int
    processed_emails: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadResponse(ORMModel):
    """Response after accepting a ZIP upload."""

    archive: ArchiveResponse
    message: str
