#!/bin/bash
set -euo pipefail

echo "==> Waiting for PostgreSQL at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."

python <<'PY'
import asyncio
import os
import sys

import asyncpg

host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]
database = os.environ["POSTGRES_DB"]


async def ready() -> bool:
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=3,
        )
        await conn.close()
        return True
    except Exception:
        return False


async def main() -> None:
    for attempt in range(60):
        if await ready():
            print("PostgreSQL is ready.")
            return
        print(f"  attempt {attempt + 1}/60...")
        await asyncio.sleep(2)
    print("PostgreSQL did not become ready in time.", file=sys.stderr)
    sys.exit(1)


asyncio.run(main())
PY

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Starting application: $*"
exec "$@"
