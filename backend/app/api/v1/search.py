"""Search API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_chroma_service, get_db_session, get_elasticsearch_service
from app.repositories.email_repository import EmailRepository
from app.schemas.search import KeywordSearchRequest, SearchResponse, SemanticSearchRequest
from app.services.chroma_service import ChromaService
from app.services.elasticsearch_service import ElasticsearchService

router = APIRouter()


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
