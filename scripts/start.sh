#!/usr/bin/env bash
# Start the full platform with Docker Compose
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Building and starting all services (first run may take 10-15 minutes)..."
docker compose up -d --build

echo ""
echo "Platform URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/api/v1/health"
echo ""
echo "View logs:  docker compose logs -f backend"
echo "Stop:       docker compose down"
