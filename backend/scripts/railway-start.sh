#!/bin/bash
set -euo pipefail

echo "==> Waiting for PostgreSQL..."

python <<'PY'
import asyncio
import os
import sys
from urllib.parse import unquote, urlparse

import asyncpg


def connection_params() -> dict:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        params = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": (parsed.path or "/").lstrip("/") or "postgres",
            "timeout": 3,
        }
        if "sslmode=" in (parsed.query or "") or "ssl=" in (parsed.query or ""):
            params["ssl"] = "require"
        elif parsed.hostname and "railway" in parsed.hostname:
            params["ssl"] = "require"
        return params

    return {
        "host": os.environ.get("POSTGRES_HOST") or os.environ.get("PGHOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT") or os.environ.get("PGPORT", "5432")),
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "database": os.environ["POSTGRES_DB"],
        "timeout": 3,
    }


async def ready(params: dict) -> bool:
    try:
        conn = await asyncpg.connect(**params)
        await conn.close()
        return True
    except Exception:
        return False


async def main() -> None:
    params = connection_params()
    for attempt in range(60):
        if await ready(params):
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

PORT="${PORT:-8000}"
echo "==> Starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
