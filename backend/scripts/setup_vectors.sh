#!/usr/bin/env bash
# Recommended vector store setup: HTTP Docker ChromaDB + reindex.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/setup_chroma.sh" http
cd "${SCRIPT_DIR}/.."
python scripts/reindex_chroma.py
echo "Vector store setup complete (HTTP Docker mode)."
