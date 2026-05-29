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
