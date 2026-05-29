"""ChromaDB embedding and semantic search service."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.email import Email
from app.schemas.search import SearchHit
from app.search.chroma_config import COLLECTION_METADATA
from app.services.embedding_service import EmbeddingService
from app.utils.text_cleaner import truncate_text

logger = logging.getLogger(__name__)

ChromaMode = Literal["persistent", "http"]


class ChromaService:
    """Manage vector embeddings and semantic search in ChromaDB."""

    def __init__(self) -> None:
        self._client: chromadb.ClientAPI | None = None
        self._collection = None
        self._embedding_service = EmbeddingService()
        self.collection_name = settings.chroma_collection
        self._connected = False

    def connect(self) -> None:
        """Initialize Chroma client, collection, and embedding model."""
        if not settings.chroma_enabled:
            logger.info("ChromaDB integration disabled via configuration")
            return

        self._connect_with_retry()
        self._connected = True

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=15))
    def _connect_with_retry(self) -> None:
        if settings.chroma_mode == "http":
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            location = f"http://{settings.chroma_host}:{settings.chroma_port}"
        else:
            Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            location = settings.chroma_persist_dir

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata=COLLECTION_METADATA,
        )
        logger.info(
            "ChromaDB connected: mode=%s collection=%s location=%s",
            settings.chroma_mode,
            self.collection_name,
            location,
        )

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def collection(self):
        if self._collection is None:
            self.connect()
        return self._collection

    def health_check(self) -> dict[str, object]:
        """Return ChromaDB collection health metadata."""
        if not settings.chroma_enabled:
            return {
                "status": "disabled",
                "collection": self.collection_name,
                "mode": settings.chroma_mode,
            }

        try:
            if not self._connected:
                self.connect()

            document_count = self.collection.count()
            return {
                "status": "connected",
                "collection": self.collection_name,
                "mode": settings.chroma_mode,
                "document_count": document_count,
                "embedding_model": settings.embedding_model,
                "persist_dir": settings.chroma_persist_dir
                if settings.chroma_mode == "persistent"
                else None,
                "host": settings.chroma_host if settings.chroma_mode == "http" else None,
                "port": settings.chroma_port if settings.chroma_mode == "http" else None,
            }
        except Exception as exc:
            return {
                "status": "error",
                "collection": self.collection_name,
                "mode": settings.chroma_mode,
                "error": str(exc),
            }

    def _embedding_text(self, email: Email) -> str:
        parts = [
            f"Subject: {email.subject}",
            f"From: {email.sender}",
            f"Body: {truncate_text(email.body_text, max_chars=3000)}",
        ]
        if email.summary:
            parts.append(f"Summary: {email.summary}")
        return "\n".join(parts)

    def _build_metadata(self, email: Email) -> dict[str, str]:
        return {
            "email_id": str(email.id),
            "archive_id": str(email.archive_id),
            "thread_id": str(email.thread_id) if email.thread_id else "",
            "sender": email.sender,
            "subject": email.subject[:500],
            "sent_at": email.sent_at.isoformat() if email.sent_at else "",
        }

    def index_email(self, email: Email) -> str:
        document_id = str(email.id)
        text = self._embedding_text(email)
        embedding = self._embedding_service.embed_query(text)

        self.collection.upsert(
            ids=[document_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[self._build_metadata(email)],
        )
        return document_id

    def bulk_index_emails(self, emails: list[Email]) -> int:
        if not emails:
            return 0

        indexed = 0
        batch_size = settings.embedding_batch_size

        for start in range(0, len(emails), batch_size):
            batch = emails[start : start + batch_size]
            ids = [str(email.id) for email in batch]
            documents = [self._embedding_text(email) for email in batch]
            metadatas = [self._build_metadata(email) for email in batch]
            embeddings = self._embedding_service.embed_documents(documents)

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            indexed += len(batch)

        return indexed

    def reindex_all(self, emails: list[Email]) -> int:
        """Replace all vectors in the collection with emails from PostgreSQL."""
        if self._client is None:
            self.connect()

        try:
            self._client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata=COLLECTION_METADATA,
        )
        return self.bulk_index_emails(emails)

    def delete_email(self, email_id: UUID) -> None:
        self.collection.delete(ids=[str(email_id)])

    def delete_by_archive(self, archive_id: UUID) -> None:
        """Delete all embeddings belonging to an archive."""
        self.collection.delete(where={"archive_id": str(archive_id)})

    def semantic_search(
        self,
        query: str,
        *,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[SearchHit]:
        query_embedding = self._embedding_service.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return self._results_to_hits(results, min_score=min_score)

    def find_similar_emails(self, email: Email, *, top_k: int = 5) -> list[tuple[UUID, float]]:
        text = self._embedding_text(email)
        query_embedding = self._embedding_service.embed_query(text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k + 1,
            include=["metadatas", "distances"],
        )

        similar: list[tuple[UUID, float]] = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for idx, document_id in enumerate(ids):
            if document_id == str(email.id):
                continue
            distance = distances[idx] if idx < len(distances) else 1.0
            score = max(0.0, 1.0 - distance)
            similar.append((UUID(document_id), score))

        return similar[:top_k]

    def _results_to_hits(self, results: dict, *, min_score: float) -> list[SearchHit]:
        hits: list[SearchHit] = []
        ids = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for idx, document_id in enumerate(ids):
            distance = distances[idx] if idx < len(distances) else 1.0
            score = max(0.0, 1.0 - distance)
            if score < min_score:
                continue

            metadata = metadatas[idx] if idx < len(metadatas) else {}
            snippet = documents[idx][:200] if idx < len(documents) else ""

            sent_at = None
            if metadata.get("sent_at"):
                try:
                    sent_at = datetime.fromisoformat(metadata["sent_at"])
                except ValueError:
                    sent_at = None

            hits.append(
                SearchHit(
                    id=UUID(document_id),
                    subject=metadata.get("subject", ""),
                    sender=metadata.get("sender", ""),
                    sent_at=sent_at,
                    snippet=snippet,
                    score=score,
                )
            )

        return hits
