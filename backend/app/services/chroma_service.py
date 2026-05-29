"""ChromaDB embedding and semantic search service."""

import logging
from datetime import datetime
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.email import Email
from app.schemas.search import SearchHit
from app.utils.text_cleaner import truncate_text

logger = logging.getLogger(__name__)


class ChromaService:
    """Manage vector embeddings and semantic search in ChromaDB."""

    def __init__(self) -> None:
        self._client: chromadb.ClientAPI | None = None
        self._collection = None
        self._embedder: SentenceTransformer | None = None
        self.collection_name = settings.chroma_collection

    def connect(self) -> None:
        """Initialize persistent Chroma client and embedding model."""
        persist_dir = settings.chroma_persist_dir
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB connected: collection=%s path=%s", self.collection_name, persist_dir)

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            logger.info("Loading embedding model: %s", settings.embedding_model)
            self._embedder = SentenceTransformer(settings.embedding_model)
        return self._embedder

    @property
    def collection(self):
        if self._collection is None:
            self.connect()
        return self._collection

    def _embedding_text(self, email: Email) -> str:
        parts = [
            f"Subject: {email.subject}",
            f"From: {email.sender}",
            f"Body: {truncate_text(email.body_text, max_chars=3000)}",
        ]
        if email.summary:
            parts.append(f"Summary: {email.summary}")
        return "\n".join(parts)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def index_email(self, email: Email) -> str:
        document_id = str(email.id)
        text = self._embedding_text(email)
        embedding = self._embed([text])[0]

        self.collection.upsert(
            ids=[document_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "email_id": document_id,
                    "sender": email.sender,
                    "subject": email.subject[:500],
                    "sent_at": email.sent_at.isoformat() if email.sent_at else "",
                }
            ],
        )
        return document_id

    def bulk_index_emails(self, emails: list[Email]) -> None:
        if not emails:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for email in emails:
            ids.append(str(email.id))
            documents.append(self._embedding_text(email))
            metadatas.append(
                {
                    "email_id": str(email.id),
                    "sender": email.sender,
                    "subject": email.subject[:500],
                    "sent_at": email.sent_at.isoformat() if email.sent_at else "",
                }
            )

        embeddings = self._embed(documents)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def delete_email(self, email_id: UUID) -> None:
        self.collection.delete(ids=[str(email_id)])

    def semantic_search(
        self,
        query: str,
        *,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[SearchHit]:
        query_embedding = self._embed([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

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

    def find_similar_emails(self, email: Email, *, top_k: int = 5) -> list[tuple[UUID, float]]:
        text = self._embedding_text(email)
        query_embedding = self._embed([text])[0]
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
