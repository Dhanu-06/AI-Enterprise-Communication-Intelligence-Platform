#!/usr/bin/env bash
# Start PostgreSQL and run Alembic migrations.
# Usage (from project root):
#   bash backend/scripts/setup_database.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

echo "Starting PostgreSQL container..."
docker compose -f docker/docker-compose.postgres.yml up -d

echo "Waiting for PostgreSQL to become healthy..."
for i in {1..30}; do
  health="$(docker inspect --format='{{.State.Health.Status}}' comm_intel_postgres 2>/dev/null || true)"
  if [[ "${health}" == "healthy" ]]; then
    echo "PostgreSQL is healthy."
    break
  fi
  sleep 2
  if [[ "${i}" -eq 30 ]]; then
    echo "PostgreSQL did not become healthy in time." >&2
    exit 1
  fi
done

cd "${PROJECT_ROOT}/backend"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example"
fi

echo "Running Alembic migrations..."
alembic upgrade head

echo "Verifying database connection..."
python scripts/verify_database.py --schema

echo "Database setup complete."
