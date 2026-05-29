"""Root router for API v1 endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.database import check_database_connection

from app.api.v1 import analytics, emails, search, uploads

api_router = APIRouter()

api_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@api_router.get("/health", tags=["Health"])
async def health_check() -> dict[str, object]:
    """Verify the API and PostgreSQL database are reachable."""
    try:
        database = await check_database_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "database": "disconnected", "error": str(exc)},
        ) from exc

    return {
        "status": "ok",
        "database": database,
    }
