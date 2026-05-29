"""FastAPI dependency injection helpers."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.services import chroma_service, elasticsearch_service, ingestion_service
from app.services.analytics_service import AnalyticsService
from app.services.chroma_service import ChromaService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.ingestion_service import IngestionService
from app.services.similarity_service import SimilarityService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_ingestion_service() -> IngestionService:
    return ingestion_service


def get_elasticsearch_service() -> ElasticsearchService:
    return elasticsearch_service


def get_chroma_service() -> ChromaService:
    return chroma_service


def get_analytics_service(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsService:
    return AnalyticsService(session)


def get_similarity_service(
    session: AsyncSession = Depends(get_db_session),
) -> SimilarityService:
    return SimilarityService(session, chroma_service)
