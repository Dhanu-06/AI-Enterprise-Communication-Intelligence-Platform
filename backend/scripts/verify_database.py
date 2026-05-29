"""Database connection verification and migration helpers."""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text

from app.core.config import settings
from app.core.database import close_db, engine

REQUIRED_TABLES = {"email_archives", "email_threads", "emails"}


async def run_checks(include_schema: bool) -> int:
    """Verify PostgreSQL connectivity and optionally required tables."""
    print(f"Connecting to: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    try:
        async with engine.connect() as connection:
            version = await connection.scalar(text("SELECT version()"))
            db_name = await connection.scalar(text("SELECT current_database()"))
            table_count = await connection.scalar(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    """
                )
            )

        print("Status: CONNECTED")
        print(f"Database: {db_name}")
        print(f"PostgreSQL: {version}")
        print(f"Public tables: {table_count}")

        if not include_schema:
            return 0

        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    """
                )
            )
            existing = {row[0] for row in result.fetchall()}

        missing = REQUIRED_TABLES - existing
        if missing:
            print("Schema: INCOMPLETE")
            print(f"Missing tables: {', '.join(sorted(missing))}")
            return 1

        print("Schema: OK")
        print(f"Found tables: {', '.join(sorted(existing & REQUIRED_TABLES))}")
        return 0

    except Exception as exc:
        print("Status: FAILED")
        print(f"Error: {exc}")
        return 1
    finally:
        await close_db()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify PostgreSQL database setup")
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Also verify required application tables exist",
    )
    args = parser.parse_args()
    return asyncio.run(run_checks(include_schema=args.schema))


if __name__ == "__main__":
    sys.exit(main())
