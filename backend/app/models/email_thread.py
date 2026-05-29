"""Conversation thread model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailThread(Base):
    """Groups related emails into a reconstructed conversation thread."""

    __tablename__ = "email_threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_normalized: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    root_message_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    participant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    email_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_email_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_email_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        "Email", back_populates="thread"
    )
