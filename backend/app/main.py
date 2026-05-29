"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db
from app.core.services import chroma_service, elasticsearch_service

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle hooks."""
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    if settings.chroma_mode == "persistent":
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", upload_path.resolve())

    if settings.debug:
        logger.info(
            "Debug mode enabled. Run 'alembic upgrade head' to apply database migrations."
        )

    try:
        await elasticsearch_service.connect()
    except Exception as exc:
        logger.warning("Elasticsearch unavailable at startup: %s", exc)

    try:
        chroma_service.connect()
    except Exception as exc:
        logger.warning("ChromaDB unavailable at startup: %s", exc)

    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    yield

    await elasticsearch_service.close()
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise platform for email archive ingestion, semantic search, "
        "AI summaries, thread reconstruction, and communication analytics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with service metadata."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
