"""Email and thread API routes."""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_similarity_service
from app.repositories.email_repository import EmailRepository
from app.repositories.thread_repository import ThreadRepository
from app.schemas.common import PaginatedResponse
from app.schemas.email import EmailDetailResponse, EmailListItem, EmailResponse, ThreadResponse
from app.services.similarity_service import SimilarityService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EmailListItem])
async def list_emails(
    page: int = 1,
    page_size: int = 20,
    sender: str | None = None,
    thread_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[EmailListItem]:
    """List parsed emails with optional filters."""
    email_repo = EmailRepository(session)
    skip = (page - 1) * page_size
    emails = await email_repo.list_emails(skip=skip, limit=page_size, sender=sender, thread_id=thread_id)
    total = await email_repo.count(sender=sender, thread_id=thread_id)
    total_pages = math.ceil(total / page_size) if total else 0

    return PaginatedResponse(
        items=[EmailListItem.model_validate(email) for email in emails],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/threads", response_model=PaginatedResponse[ThreadResponse])
async def list_threads(
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ThreadResponse]:
    """List reconstructed conversation threads."""
    thread_repo = ThreadRepository(session)
    skip = (page - 1) * page_size
    threads = await thread_repo.list_threads(skip=skip, limit=page_size)
    total = await thread_repo.count()
    total_pages = math.ceil(total / page_size) if total else 0

    items: list[ThreadResponse] = []
    for thread in threads:
        emails = await thread_repo.emails_in_thread(thread.id)
        items.append(
            ThreadResponse(
                id=thread.id,
                subject_normalized=thread.subject_normalized,
                participant_count=thread.participant_count,
                email_count=thread.email_count,
                first_email_at=thread.first_email_at,
                last_email_at=thread.last_email_at,
                summary=thread.summary,
                emails=[EmailListItem.model_validate(email) for email in emails],
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ThreadResponse:
    """Get a single conversation thread with all emails."""
    thread_repo = ThreadRepository(session)
    thread = await thread_repo.get_with_emails(thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    emails = sorted(
        thread.emails,
        key=lambda item: (item.sent_at or item.created_at),
    )
    return ThreadResponse(
        id=thread.id,
        subject_normalized=thread.subject_normalized,
        participant_count=thread.participant_count,
        email_count=thread.email_count,
        first_email_at=thread.first_email_at,
        last_email_at=thread.last_email_at,
        summary=thread.summary,
        emails=[EmailListItem.model_validate(email) for email in emails],
    )


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(
    email_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    similarity_service: SimilarityService = Depends(get_similarity_service),
) -> EmailDetailResponse:
    """Get email details with similar email recommendations."""
    email_repo = EmailRepository(session)
    email, thread = await email_repo.get_with_thread(email_id)
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    similar = await similarity_service.get_similar_emails(email_id, top_k=5)
    response = EmailDetailResponse.model_validate(email)
    response.thread_subject = thread.subject_normalized if thread else None
    response.similar_emails = similar
    return response


@router.get("/{email_id}/summary", response_model=EmailResponse)
async def get_email_summary(
    email_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> EmailResponse:
    """Get email with AI-generated summary."""
    email_repo = EmailRepository(session)
    email = await email_repo.get_by_id(email_id)
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return EmailResponse.model_validate(email)
