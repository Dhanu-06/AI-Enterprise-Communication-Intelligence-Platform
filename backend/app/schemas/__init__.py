"""Pydantic request/response schemas."""

from app.schemas.analytics import (
    AnalyticsDashboard,
    AnalyticsOverview,
    DailyVolume,
    SenderStats,
    SubjectKeyword,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.email import (
    EmailDetailResponse,
    EmailListItem,
    EmailResponse,
    ParsedEmailData,
    SimilarEmailResult,
    ThreadResponse,
)
from app.schemas.search import (
    KeywordSearchRequest,
    SearchHit,
    SearchResponse,
    SemanticSearchRequest,
)
from app.schemas.upload import ArchiveResponse, UploadResponse

__all__ = [
    "AnalyticsDashboard",
    "AnalyticsOverview",
    "ArchiveResponse",
    "DailyVolume",
    "EmailDetailResponse",
    "EmailListItem",
    "EmailResponse",
    "KeywordSearchRequest",
    "MessageResponse",
    "PaginatedResponse",
    "ParsedEmailData",
    "SearchHit",
    "SearchResponse",
    "SemanticSearchRequest",
    "SenderStats",
    "SimilarEmailResult",
    "SubjectKeyword",
    "ThreadResponse",
    "UploadResponse",
]
