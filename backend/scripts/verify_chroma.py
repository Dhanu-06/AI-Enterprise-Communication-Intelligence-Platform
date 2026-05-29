"""Verify ChromaDB connectivity and collection state."""

from __future__ import annotations

import argparse
import sys

from app.core.services import chroma_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ChromaDB setup")
    parser.parse_args()

    health = chroma_service.health_check()
    print(f"Status: {health.get('status')}")
    print(f"Collection: {health.get('collection')}")
    print(f"Mode: {health.get('mode')}")

    if health.get("status") == "connected":
        print(f"Documents: {health.get('document_count')}")
        print(f"Embedding model: {health.get('embedding_model')}")
        return 0

    if health.get("status") == "disabled":
        return 0

    print(f"Error: {health.get('error')}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
