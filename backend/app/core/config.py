"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(value: str) -> List[str]:
    """Parse comma-separated CORS origins from environment variables."""
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Central configuration for the backend service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Enterprise Communication Intelligence Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Stored as comma-separated string in .env (avoids pydantic-settings JSON list parsing)
    cors_origins_env: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ORIGINS",
    )

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "comm_intel"
    postgres_password: str = "comm_intel_secret"
    postgres_db: str = "comm_intel_db"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "emails"
    elasticsearch_index_template: str = "comm_intel_emails_template"
    elasticsearch_enabled: bool = True
    elasticsearch_timeout: int = 30
    elasticsearch_max_retries: int = 3
    elasticsearch_username: str | None = None
    elasticsearch_password: str | None = None

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "email_embeddings"
    chroma_persist_dir: str = "chroma_data"
    chroma_mode: str = "http"  # http (recommended) | persistent
    chroma_enabled: bool = True

    # AI / Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 64
    summary_model: str = "google/flan-t5-base"

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 500

    @property
    def cors_origins(self) -> List[str]:
        return _parse_cors_origins(self.cors_origins_env)

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync SQLAlchemy connection URL (Alembic migrations)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
