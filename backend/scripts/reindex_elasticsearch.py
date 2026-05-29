"""Reindex all emails from PostgreSQL into Elasticsearch."""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.database import async_session_factory, close_db
from app.core.services import elasticsearch_service
from app.repositories.email_repository import EmailRepository


async def reindex() -> int:
    try:
        await elasticsearch_service.connect()
    except Exception as exc:
        print(f"Failed to connect to Elasticsearch: {exc}")
        return 1

    async with async_session_factory() as session:
        email_repo = EmailRepository(session)
        emails = await email_repo.list_all()

    print(f"Reindexing {len(emails)} emails into index '{elasticsearch_service.index_name}'...")
    indexed = await elasticsearch_service.reindex_all(emails)
    await elasticsearch_service.close()
    await close_db()

    print(f"Reindex complete. Indexed documents: {indexed}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Elasticsearch email index from PostgreSQL")
    parser.parse_args()
    return asyncio.run(reindex())


if __name__ == "__main__":
    sys.exit(main())
