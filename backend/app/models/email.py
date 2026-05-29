"""Parsed email message model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Email(Base):
    """A single parsed email extracted from an archive."""

    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    archive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_archives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    in_reply_to: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    references_header: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    receivers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    cc: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    subject: Mapped[str] = mapped_column(String(1024), default="", nullable=False, index=True)
    body_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    elasticsearch_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chroma_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_file: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    archive: Mapped["EmailArchive"] = relationship(  # noqa: F821
        "EmailArchive", back_populates="emails"
    )
    thread: Mapped["EmailThread | None"] = relationship(  # noqa: F821
        "EmailThread", back_populates="emails"
    )
