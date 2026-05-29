"""Search-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class KeywordSearchRequest(BaseModel):
    """Full-text keyword search via Elasticsearch."""

    query: str = Field(..., min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sender: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class SemanticSearchRequest(BaseModel):
    """Semantic vector search via ChromaDB."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SearchHit(ORMModel):
    """Unified search result item."""

    id: UUID
    subject: str
    sender: str
    sent_at: datetime | None = None
    summary: str | None = None
    snippet: str = ""
    score: float = 0.0


class SearchResponse(BaseModel):
    """Paginated or ranked search results."""

    query: str
    total: int
    results: list[SearchHit]


class ElasticsearchHealthResponse(BaseModel):
    """Elasticsearch cluster health snapshot."""

    status: str
    index: str
    cluster_name: str | None = None
    cluster_status: str | None = None
    number_of_nodes: int | None = None
    document_count: int | None = None
    error: str | None = None


class ReindexResponse(BaseModel):
    """Result of a full Elasticsearch reindex operation."""

    index: str
    indexed: int
    message: str


class ChromaHealthResponse(BaseModel):
    """ChromaDB collection health snapshot."""

    status: str
    collection: str
    mode: str
    document_count: int | None = None
    embedding_model: str | None = None
    persist_dir: str | None = None
    host: str | None = None
    port: int | None = None
    error: str | None = None
