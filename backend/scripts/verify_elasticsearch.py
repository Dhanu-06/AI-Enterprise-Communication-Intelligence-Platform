"""Verify Elasticsearch connectivity, template, and index state."""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.config import settings
from app.core.services import elasticsearch_service


async def run_checks(include_template: bool) -> int:
    if not settings.elasticsearch_enabled:
        print("Elasticsearch integration is disabled (ELASTICSEARCH_ENABLED=false)")
        return 0

    print(f"Connecting to: {settings.elasticsearch_url}")
    print(f"Target index: {settings.elasticsearch_index}")

    try:
        await elasticsearch_service.connect()
        health = await elasticsearch_service.health_check()
        print(f"Status: {health.get('status')}")

        if health.get("status") != "connected":
            print(f"Details: {health}")
            return 1

        print(f"Cluster: {health.get('cluster_name')} ({health.get('cluster_status')})")
        print(f"Nodes: {health.get('number_of_nodes')}")
        print(f"Documents in index: {health.get('document_count')}")

        if include_template:
            template = await elasticsearch_service.client.indices.get_index_template(
                name=settings.elasticsearch_index_template
            )
            template_names = [
                item.get("name")
                for item in template.get("index_templates", [])
            ]
            if settings.elasticsearch_index_template in template_names:
                print(f"Index template: OK ({settings.elasticsearch_index_template})")
            else:
                print(f"Index template: MISSING ({settings.elasticsearch_index_template})")
                return 1

        return 0
    except Exception as exc:
        print(f"Status: FAILED")
        print(f"Error: {exc}")
        return 1
    finally:
        await elasticsearch_service.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Elasticsearch setup")
    parser.add_argument(
        "--template",
        action="store_true",
        help="Verify the composable index template exists",
    )
    args = parser.parse_args()
    return asyncio.run(run_checks(include_template=args.template))


if __name__ == "__main__":
    sys.exit(main())
