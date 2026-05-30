"""Email archive upload batch model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ArchiveStatus(str, enum.Enum):
    """Processing lifecycle for an uploaded ZIP archive."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailArchive(Base):
    """Represents a uploaded ZIP file containing email exports."""

    __tablename__ = "email_archives"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[ArchiveStatus] = mapped_column(
        Enum(
            ArchiveStatus,
            name="archive_status",
            values_callable=lambda statuses: [s.value for s in statuses],
        ),
        default=ArchiveStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    emails: Mapped[list["Email"]] = relationship(  # noqa: F821
        "Email", back_populates="archive", cascade="all, delete-orphan"
    )
