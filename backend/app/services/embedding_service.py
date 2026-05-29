"""LangChain-powered embedding service."""

import logging
import threading

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate text embeddings using LangChain and Sentence Transformers."""

    _lock = threading.Lock()
    _embeddings: HuggingFaceEmbeddings | None = None

    @classmethod
    def get_embeddings(cls) -> HuggingFaceEmbeddings:
        with cls._lock:
            if cls._embeddings is None:
                logger.info("Loading LangChain embedding model: %s", settings.embedding_model)
                cls._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.embedding_model,
                    encode_kwargs={"normalize_embeddings": True},
                )
            return cls._embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""
        if not texts:
            return []
        return self.get_embeddings().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        return self.get_embeddings().embed_query(text)

    def embed_in_batches(self, texts: list[str], batch_size: int) -> list[list[float]]:
        """Embed large document sets in configurable batches."""
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            vectors.extend(self.embed_documents(batch))
        return vectors
