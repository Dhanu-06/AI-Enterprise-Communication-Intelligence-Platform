"""Elasticsearch indexing and search service."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk

from app.core.config import settings
from app.models.email import Email
from app.schemas.search import SearchHit
from app.search.elasticsearch_mappings import (
    INDEX_TEMPLATE_NAME,
    build_index_body,
    build_index_template,
)
from app.utils.email_helpers import build_search_snippet

logger = logging.getLogger(__name__)

BULK_BATCH_SIZE = 500


class ElasticsearchService:
    """Manage Elasticsearch indexing and keyword search."""

    def __init__(self) -> None:
        client_kwargs: dict[str, Any] = {
            "hosts": [settings.elasticsearch_url],
            "request_timeout": settings.elasticsearch_timeout,
            "retry_on_timeout": True,
            "max_retries": settings.elasticsearch_max_retries,
        }

        if settings.elasticsearch_username and settings.elasticsearch_password:
            client_kwargs["basic_auth"] = (
                settings.elasticsearch_username,
                settings.elasticsearch_password,
            )

        self.client = AsyncElasticsearch(**client_kwargs)
        self.index_name = settings.elasticsearch_index
        self._connected = False

    async def connect(self) -> None:
        """Verify connectivity, install templates, and ensure the index exists."""
        if not settings.elasticsearch_enabled:
            logger.info("Elasticsearch integration disabled via configuration")
            return

        if not await self.client.ping():
            raise ConnectionError("Elasticsearch cluster is unreachable")

        await self.ensure_index_template()
        await self.ensure_index()
        self._connected = True
        logger.info("Elasticsearch connected: index=%s", self.index_name)

    async def close(self) -> None:
        await self.client.close()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def health_check(self) -> dict[str, object]:
        """Return Elasticsearch cluster health metadata."""
        if not settings.elasticsearch_enabled:
            return {"status": "disabled", "index": self.index_name}

        try:
            if not await self.client.ping():
                return {"status": "disconnected", "index": self.index_name}

            cluster = await self.client.cluster.health()
            index_exists = await self.client.indices.exists(index=self.index_name)
            document_count = 0
            if index_exists:
                stats = await self.client.count(index=self.index_name)
                document_count = int(stats.get("count", 0))

            return {
                "status": "connected",
                "index": self.index_name,
                "cluster_name": cluster.get("cluster_name"),
                "cluster_status": cluster.get("status"),
                "number_of_nodes": cluster.get("number_of_nodes"),
                "document_count": document_count,
            }
        except Exception as exc:
            return {
                "status": "error",
                "index": self.index_name,
                "error": str(exc),
            }

    async def ensure_index_template(self) -> None:
        """Install or update the composable index template."""
        template_body = build_index_template()
        await self.client.indices.put_index_template(
            name=INDEX_TEMPLATE_NAME,
            body=template_body,
        )
        logger.info("Ensured Elasticsearch index template: %s", INDEX_TEMPLATE_NAME)

    async def ensure_index(self) -> None:
        exists = await self.client.indices.exists(index=self.index_name)
        if not exists:
            await self.client.indices.create(index=self.index_name, body=build_index_body())
            logger.info("Created Elasticsearch index: %s", self.index_name)

    def _document(self, email: Email) -> dict[str, Any]:
        return {
            "email_id": str(email.id),
            "archive_id": str(email.archive_id),
            "thread_id": str(email.thread_id) if email.thread_id else None,
            "sender": email.sender,
            "receivers": email.receivers,
            "cc": email.cc,
            "subject": email.subject,
            "body_text": email.body_text,
            "summary": email.summary,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "created_at": email.created_at.isoformat() if email.created_at else None,
            "source_file": email.source_file,
        }

    def _bulk_actions(self, emails: list[Email]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for email in emails:
            actions.append(
                {
                    "_op_type": "index",
                    "_index": self.index_name,
                    "_id": str(email.id),
                    "_source": self._document(email),
                }
            )
        return actions

    async def index_email(self, email: Email, *, refresh: bool = False) -> str:
        document_id = str(email.id)
        await self.client.index(
            index=self.index_name,
            id=document_id,
            document=self._document(email),
            refresh=refresh,
        )
        return document_id

    async def bulk_index_emails(self, emails: list[Email], *, refresh: bool = False) -> int:
        if not emails:
            return 0

        indexed = 0
        for start in range(0, len(emails), BULK_BATCH_SIZE):
            batch = emails[start : start + BULK_BATCH_SIZE]
            success, errors = await async_bulk(
                self.client,
                self._bulk_actions(batch),
                refresh=refresh,
                raise_on_error=False,
            )
            indexed += success
            if errors:
                logger.warning(
                    "Elasticsearch bulk indexing reported %s errors in batch starting at %s",
                    len(errors),
                    start,
                )

        return indexed

    async def reindex_all(self, emails: list[Email]) -> int:
        """Replace all documents in the index with emails from PostgreSQL."""
        await self.client.indices.delete(index=self.index_name, ignore_unavailable=True)
        await self.ensure_index()
        return await self.bulk_index_emails(emails, refresh=True)

    async def delete_email(self, email_id: UUID) -> None:
        try:
            await self.client.delete(index=self.index_name, id=str(email_id))
        except NotFoundError:
            pass

    async def delete_by_archive(self, archive_id: UUID) -> int:
        """Delete all indexed emails belonging to an archive."""
        response = await self.client.delete_by_query(
            index=self.index_name,
            body={"query": {"term": {"archive_id": str(archive_id)}}},
            refresh=True,
        )
        return int(response.get("deleted", 0))

    async def search(
        self,
        query: str,
        *,
        page: int = 1,
        page_size: int = 20,
        sender: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[SearchHit], int]:
        must: list[dict[str, Any]] = [
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "subject^4",
                        "body_text",
                        "summary^2",
                        "sender.text",
                        "sender",
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        filters: list[dict[str, Any]] = []
        if sender:
            filters.append(
                {
                    "bool": {
                        "should": [
                            {"wildcard": {"sender": f"*{sender.lower()}*"}},
                            {"match": {"sender.text": sender}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
        if date_from or date_to:
            range_filter: dict[str, Any] = {"range": {"sent_at": {}}}
            if date_from:
                range_filter["range"]["sent_at"]["gte"] = date_from.isoformat()
            if date_to:
                range_filter["range"]["sent_at"]["lte"] = date_to.isoformat()
            filters.append(range_filter)

        body: dict[str, Any] = {
            "query": {"bool": {"must": must, "filter": filters}},
            "from": (page - 1) * page_size,
            "size": page_size,
            "highlight": {
                "fields": {
                    "body_text": {"fragment_size": 150, "number_of_fragments": 1},
                    "subject": {},
                    "summary": {"fragment_size": 120, "number_of_fragments": 1},
                }
            },
        }

        response = await self.client.search(index=self.index_name, body=body)
        hits = response["hits"]["hits"]
        total = int(response["hits"]["total"]["value"])

        results: list[SearchHit] = []
        for hit in hits:
            source = hit["_source"]
            highlight = hit.get("highlight", {})
            snippet = (
                highlight.get("body_text", [None])[0]
                or highlight.get("summary", [None])[0]
                or highlight.get("subject", [None])[0]
                or build_search_snippet(source.get("body_text", ""), query)
            )
            sent_at_raw = source.get("sent_at")
            results.append(
                SearchHit(
                    id=UUID(source["email_id"]),
                    subject=source.get("subject", ""),
                    sender=source.get("sender", ""),
                    sent_at=datetime.fromisoformat(sent_at_raw) if sent_at_raw else None,
                    summary=source.get("summary"),
                    snippet=snippet,
                    score=float(hit.get("_score") or 0.0),
                )
            )

        return results, total
