"""Search API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_chroma_service, get_db_session, get_elasticsearch_service, get_similarity_service
from app.repositories.email_repository import EmailRepository
from app.schemas.email import SimilarEmailResult
from app.schemas.search import (
    ChromaHealthResponse,
    ElasticsearchHealthResponse,
    KeywordSearchRequest,
    ReindexResponse,
    SearchResponse,
    SemanticSearchRequest,
)
from app.services.chroma_service import ChromaService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.similarity_service import SimilarityService

router = APIRouter()


@router.get("/chroma/health", response_model=ChromaHealthResponse)
async def chroma_health(
    chroma_service: ChromaService = Depends(get_chroma_service),
) -> ChromaHealthResponse:
    """Return ChromaDB collection health and vector count."""
    health = chroma_service.health_check()
    return ChromaHealthResponse(
        status=str(health.get("status", "unknown")),
        collection=str(health.get("collection", chroma_service.collection_name)),
        mode=str(health.get("mode", "unknown")),
        document_count=health.get("document_count"),  # type: ignore[arg-type]
        embedding_model=health.get("embedding_model"),  # type: ignore[arg-type]
        persist_dir=health.get("persist_dir"),  # type: ignore[arg-type]
        host=health.get("host"),  # type: ignore[arg-type]
        port=health.get("port"),  # type: ignore[arg-type]
        error=health.get("error"),  # type: ignore[arg-type]
    )


@router.post("/chroma/reindex", response_model=ReindexResponse)
async def reindex_chroma(
    chroma_service: ChromaService = Depends(get_chroma_service),
    session: AsyncSession = Depends(get_db_session),
) -> ReindexResponse:
    """Rebuild ChromaDB vectors from all emails stored in PostgreSQL."""
    try:
        if not chroma_service.is_connected:
            chroma_service.connect()

        email_repo = EmailRepository(session)
        emails = await email_repo.list_all()
        indexed = chroma_service.reindex_all(emails)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ChromaDB reindex failed: {exc}",
        ) from exc

    return ReindexResponse(
        index=chroma_service.collection_name,
        indexed=indexed,
        message=f"Successfully reindexed {indexed} email vectors",
    )


@router.get("/similar/{email_id}", response_model=list[SimilarEmailResult])
async def find_similar_emails(
    email_id: uuid.UUID,
    top_k: int = Query(default=5, ge=1, le=20),
    similarity_service: SimilarityService = Depends(get_similarity_service),
    session: AsyncSession = Depends(get_db_session),
) -> list[SimilarEmailResult]:
    """Return semantically similar email recommendations for a given email."""
    email_repo = EmailRepository(session)
    if not await email_repo.get_by_id(email_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    try:
        return await similarity_service.get_similar_emails(email_id, top_k=top_k)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Similar email search unavailable: {exc}",
        ) from exc


@router.get("/elasticsearch/health", response_model=ElasticsearchHealthResponse)
async def elasticsearch_health(
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service),
) -> ElasticsearchHealthResponse:
    """Return Elasticsearch cluster and index health."""
    health = await elasticsearch_service.health_check()
    return ElasticsearchHealthResponse(
        status=str(health.get("status", "unknown")),
        index=str(health.get("index", elasticsearch_service.index_name)),
        cluster_name=health.get("cluster_name"),  # type: ignore[arg-type]
        cluster_status=health.get("cluster_status"),  # type: ignore[arg-type]
        number_of_nodes=health.get("number_of_nodes"),  # type: ignore[arg-type]
        document_count=health.get("document_count"),  # type: ignore[arg-type]
        error=health.get("error"),  # type: ignore[arg-type]
    )


@router.post("/elasticsearch/reindex", response_model=ReindexResponse)
async def reindex_elasticsearch(
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service),
    session: AsyncSession = Depends(get_db_session),
) -> ReindexResponse:
    """Rebuild the Elasticsearch index from all emails stored in PostgreSQL."""
    try:
        if not elasticsearch_service.is_connected:
            await elasticsearch_service.connect()

        email_repo = EmailRepository(session)
        emails = await email_repo.list_all()
        indexed = await elasticsearch_service.reindex_all(emails)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Elasticsearch reindex failed: {exc}",
        ) from exc

    return ReindexResponse(
        index=elasticsearch_service.index_name,
        indexed=indexed,
        message=f"Successfully reindexed {indexed} emails",
    )


@router.post("/keyword", response_model=SearchResponse)
async def keyword_search(
    payload: KeywordSearchRequest,
    elasticsearch_service: ElasticsearchService = Depends(get_elasticsearch_service),
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """Full-text keyword search powered by Elasticsearch."""
    try:
        results, total = await elasticsearch_service.search(
            payload.query,
            page=payload.page,
            page_size=payload.page_size,
            sender=payload.sender,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Elasticsearch search unavailable: {exc}",
        ) from exc

    email_repo = EmailRepository(session)
    enriched_results = []
    for hit in results:
        email = await email_repo.get_by_id(hit.id)
        if email and email.summary and not hit.summary:
            hit.summary = email.summary
        enriched_results.append(hit)

    return SearchResponse(query=payload.query, total=total, results=enriched_results)


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    payload: SemanticSearchRequest,
    chroma_service: ChromaService = Depends(get_chroma_service),
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """Semantic vector search powered by ChromaDB embeddings."""
    try:
        results = chroma_service.semantic_search(
            payload.query,
            top_k=payload.top_k,
            min_score=payload.min_score,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Semantic search unavailable: {exc}",
        ) from exc

    email_repo = EmailRepository(session)
    enriched_results = []
    for hit in results:
        email = await email_repo.get_by_id(hit.id)
        if email:
            if email.summary and not hit.summary:
                hit.summary = email.summary
            if not hit.snippet:
                hit.snippet = email.body_text[:200]
        enriched_results.append(hit)

    return SearchResponse(
        query=payload.query,
        total=len(enriched_results),
        results=enriched_results,
    )
