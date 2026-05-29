"""Data access layer (repository pattern)."""

from app.repositories.archive_repository import ArchiveRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.thread_repository import ThreadRepository

__all__ = [
    "ArchiveRepository",
    "EmailRepository",
    "ThreadRepository",
]
