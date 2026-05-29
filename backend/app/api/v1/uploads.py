"""Upload archive API routes."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_ingestion_service
from app.core.config import settings
from app.repositories.archive_repository import ArchiveRepository
from app.schemas.common import PaginatedResponse
from app.schemas.upload import ArchiveResponse, UploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_archive(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> UploadResponse:
    """Upload a ZIP email archive for asynchronous processing."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip archives are supported",
        )

    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    archive_id = await ingestion_service.save_upload(session, file.filename, contents)
    background_tasks.add_task(ingestion_service.process_archive, archive_id)

    archive_repo = ArchiveRepository(session)
    archive = await archive_repo.get_by_id(archive_id)
    if not archive:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed")

    return UploadResponse(
        archive=ArchiveResponse.model_validate(archive),
        message="Archive accepted for processing",
    )


@router.get("", response_model=PaginatedResponse[ArchiveResponse])
async def list_archives(
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ArchiveResponse]:
    """List uploaded archives with pagination."""
    archive_repo = ArchiveRepository(session)
    skip = (page - 1) * page_size
    archives = await archive_repo.list_all(skip=skip, limit=page_size)
    total = await archive_repo.count()
    total_pages = (total + page_size - 1) // page_size if total else 0

    return PaginatedResponse(
        items=[ArchiveResponse.model_validate(archive) for archive in archives],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{archive_id}", response_model=ArchiveResponse)
async def get_archive(
    archive_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ArchiveResponse:
    """Get archive processing status by ID."""
    archive_repo = ArchiveRepository(session)
    archive = await archive_repo.get_by_id(archive_id)
    if not archive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archive not found")
    return ArchiveResponse.model_validate(archive)
