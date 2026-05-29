"""Reindex all emails from PostgreSQL into ChromaDB."""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.database import async_session_factory, close_db
from app.core.services import chroma_service
from app.repositories.email_repository import EmailRepository


async def reindex() -> int:
    chroma_service.connect()

    async with async_session_factory() as session:
        email_repo = EmailRepository(session)
        emails = await email_repo.list_all()

    print(
        f"Reindexing {len(emails)} emails into Chroma collection "
        f"'{chroma_service.collection_name}'..."
    )
    indexed = chroma_service.reindex_all(emails)
    await close_db()

    print(f"Reindex complete. Indexed vectors: {indexed}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild ChromaDB vectors from PostgreSQL")
    parser.parse_args()
    return asyncio.run(reindex())


if __name__ == "__main__":
    sys.exit(main())
