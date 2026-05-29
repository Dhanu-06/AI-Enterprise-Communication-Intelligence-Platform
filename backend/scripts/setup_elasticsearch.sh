#!/usr/bin/env bash
# Start Elasticsearch and initialize index template + index.
# Usage (from project root):
#   bash backend/scripts/setup_elasticsearch.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${BACKEND_ROOT}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "Ensuring Docker network exists..."
if ! docker network inspect comm_intel_network >/dev/null 2>&1; then
  docker network create comm_intel_network
  echo "Created network: comm_intel_network"
fi

echo "Starting Elasticsearch container..."
docker compose -f docker/docker-compose.elasticsearch.yml up -d

echo "Waiting for Elasticsearch to become healthy..."
for i in {1..40}; do
  health="$(docker inspect --format='{{.State.Health.Status}}' comm_intel_elasticsearch 2>/dev/null || true)"
  if [[ "${health}" == "healthy" ]]; then
    echo "Elasticsearch is healthy."
    break
  fi
  sleep 3
  if [[ "${i}" -eq 40 ]]; then
    echo "Elasticsearch did not become healthy in time." >&2
    exit 1
  fi
done

cd "${BACKEND_ROOT}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example"
fi

echo "Initializing Elasticsearch index template and index..."
python scripts/verify_elasticsearch.py --template

echo "Elasticsearch setup complete."
