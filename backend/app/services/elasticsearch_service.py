"""Elasticsearch indexing and search service."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from app.core.config import settings
from app.models.email import Email
from app.schemas.search import SearchHit
from app.utils.email_helpers import build_search_snippet

logger = logging.getLogger(__name__)

EMAIL_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "email_id": {"type": "keyword"},
            "archive_id": {"type": "keyword"},
            "thread_id": {"type": "keyword"},
            "sender": {"type": "keyword"},
            "receivers": {"type": "keyword"},
            "cc": {"type": "keyword"},
            "subject": {"type": "text", "analyzer": "english"},
            "body_text": {"type": "text", "analyzer": "english"},
            "summary": {"type": "text", "analyzer": "english"},
            "sent_at": {"type": "date"},
            "created_at": {"type": "date"},
        }
    }
}


class ElasticsearchService:
    """Manage Elasticsearch indexing and keyword search."""

    def __init__(self) -> None:
        self.client = AsyncElasticsearch(settings.elasticsearch_url)
        self.index_name = settings.elasticsearch_index

    async def connect(self) -> None:
        """Verify connectivity and ensure the index exists."""
        if not await self.client.ping():
            raise ConnectionError("Elasticsearch cluster is unreachable")
        await self.ensure_index()
        logger.info("Elasticsearch connected: index=%s", self.index_name)

    async def close(self) -> None:
        await self.client.close()

    async def ensure_index(self) -> None:
        exists = await self.client.indices.exists(index=self.index_name)
        if not exists:
            await self.client.indices.create(index=self.index_name, body=EMAIL_INDEX_MAPPING)
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
        }

    async def index_email(self, email: Email) -> str:
        document_id = str(email.id)
        await self.client.index(
            index=self.index_name,
            id=document_id,
            document=self._document(email),
            refresh=False,
        )
        return document_id

    async def bulk_index_emails(self, emails: list[Email]) -> None:
        if not emails:
            return

        operations: list[dict[str, Any]] = []
        for email in emails:
            document_id = str(email.id)
            operations.append({"index": {"_index": self.index_name, "_id": document_id}})
            operations.append(self._document(email))

        await self.client.bulk(operations=operations, refresh=False)

    async def delete_email(self, email_id: UUID) -> None:
        try:
            await self.client.delete(index=self.index_name, id=str(email_id))
        except NotFoundError:
            pass

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
                    "fields": ["subject^3", "body_text", "summary^2", "sender"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        filters: list[dict[str, Any]] = []
        if sender:
            filters.append({"wildcard": {"sender": f"*{sender.lower()}*"}})
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
                or highlight.get("subject", [None])[0]
                or build_search_snippet(source.get("body_text", ""), query)
            )
            results.append(
                SearchHit(
                    id=UUID(source["email_id"]),
                    subject=source.get("subject", ""),
                    sender=source.get("sender", ""),
                    sent_at=datetime.fromisoformat(source["sent_at"])
                    if source.get("sent_at")
                    else None,
                    summary=source.get("summary"),
                    snippet=snippet,
                    score=float(hit.get("_score") or 0.0),
                )
            )

        return results, total
