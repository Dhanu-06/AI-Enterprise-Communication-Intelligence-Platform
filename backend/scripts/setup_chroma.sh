#!/usr/bin/env bash
# Start ChromaDB server and verify connectivity.
# Usage (from project root):
#   bash backend/scripts/setup_chroma.sh [persistent|http]

set -euo pipefail

MODE="${1:-http}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${BACKEND_ROOT}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "Ensuring Docker network exists..."
if ! docker network inspect comm_intel_network >/dev/null 2>&1; then
  docker network create comm_intel_network
  echo "Created network: comm_intel_network"
fi

if [[ "${MODE}" == "http" ]]; then
  echo "Starting ChromaDB server container..."
  docker compose -f docker/docker-compose.chroma.yml up -d

  echo "Waiting for ChromaDB to become healthy..."
  for i in {1..30}; do
    health="$(docker inspect --format='{{.State.Health.Status}}' comm_intel_chromadb 2>/dev/null || true)"
    if [[ "${health}" == "healthy" ]]; then
      echo "ChromaDB is healthy."
      break
    fi
    sleep 2
    if [[ "${i}" -eq 30 ]]; then
      echo "ChromaDB did not become healthy in time." >&2
      exit 1
    fi
  done
else
  echo "Using persistent ChromaDB mode (local directory)."
  mkdir -p "${BACKEND_ROOT}/chroma_data"
fi

cd "${BACKEND_ROOT}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example"
fi

if grep -q "^CHROMA_MODE=" .env; then
  sed -i.bak "s/^CHROMA_MODE=.*/CHROMA_MODE=${MODE}/" .env && rm -f .env.bak
else
  echo "CHROMA_MODE=${MODE}" >> .env
fi
echo "Set CHROMA_MODE=${MODE} in backend/.env"

echo "Verifying ChromaDB..."
python scripts/verify_chroma.py

echo "ChromaDB setup complete."
