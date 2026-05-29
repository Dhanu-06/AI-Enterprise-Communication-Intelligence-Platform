"""Similar email recommendation service."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.email_repository import EmailRepository
from app.schemas.email import SimilarEmailResult
from app.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class SimilarityService:
    """Find semantically similar emails using ChromaDB vectors."""

    def __init__(self, session: AsyncSession, chroma_service: ChromaService) -> None:
        self.session = session
        self.email_repo = EmailRepository(session)
        self.chroma_service = chroma_service

    async def get_similar_emails(
        self,
        email_id: uuid.UUID,
        *,
        top_k: int = 5,
    ) -> list[SimilarEmailResult]:
        email = await self.email_repo.get_by_id(email_id)
        if not email:
            return []

        similar = self.chroma_service.find_similar_emails(email, top_k=top_k)
        if not similar:
            return []

        similar_ids = [item[0] for item in similar]
        score_map = {item[0]: item[1] for item in similar}
        emails = await self.email_repo.get_by_ids(similar_ids)

        results: list[SimilarEmailResult] = []
        for matched in emails:
            results.append(
                SimilarEmailResult(
                    id=matched.id,
                    subject=matched.subject,
                    sender=matched.sender,
                    sent_at=matched.sent_at,
                    similarity_score=score_map.get(matched.id, 0.0),
                    summary=matched.summary,
                )
            )

        results.sort(key=lambda item: item.similarity_score, reverse=True)
        return results
