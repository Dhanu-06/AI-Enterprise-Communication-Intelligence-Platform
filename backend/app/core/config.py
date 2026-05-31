"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List
from urllib.parse import quote_plus, unquote, urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(value: str) -> List[str]:
    """Parse comma-separated CORS origins from environment variables."""
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _should_use_ssl(host: str, query: str) -> bool:
    """Enable SSL for managed cloud databases, not local Docker services."""
    if "ssl=" in query or "sslmode=" in query:
        return False
    if host in {"localhost", "127.0.0.1", "postgres", "host.docker.internal"}:
        return False
    return "railway" in host or "amazonaws.com" in host or "neon.tech" in host


def _build_sqlalchemy_url(raw_url: str, driver: str) -> str:
    """Convert a postgres/postgresql URL into a SQLAlchemy connection URL."""
    parsed = urlparse(raw_url.strip())
    scheme = parsed.scheme.lower()

    if scheme in {"postgres", "postgresql", "postgresql+asyncpg", "postgresql+psycopg2"}:
        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        database = (parsed.path or "/").lstrip("/") or "postgres"
        auth = f"{quote_plus(user)}:{quote_plus(password)}"
        base = f"{driver}://{auth}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database URL scheme: {parsed.scheme}")

    query = parsed.query
    if _should_use_ssl(host, query):
        if driver == "postgresql+asyncpg":
            query = f"{query}&ssl=require" if query else "ssl=require"
        elif driver == "postgresql+psycopg2":
            query = f"{query}&sslmode=require" if query else "sslmode=require"

    return f"{base}?{query}" if query else base


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

    # Server (Railway injects PORT)
    host: str = "0.0.0.0"
    port: int = Field(default=8000, validation_alias="PORT")

    # Stored as comma-separated string in .env (avoids pydantic-settings JSON list parsing)
    cors_origins_env: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ORIGINS",
    )

    # PostgreSQL — Railway injects DATABASE_URL and/or PG* variables
    database_url_env: str | None = Field(default=None, validation_alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_user: str = Field(default="comm_intel", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="comm_intel_secret",
        validation_alias="POSTGRES_PASSWORD",
    )
    postgres_db: str = Field(default="comm_intel_db", validation_alias="POSTGRES_DB")

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

    @model_validator(mode="before")
    @classmethod
    def apply_railway_postgres_vars(cls, data: object) -> object:
        """Map Railway PG* variables when individual POSTGRES_* vars are unset."""
        if not isinstance(data, dict):
            return data

        pg_map = {
            "PGHOST": "POSTGRES_HOST",
            "PGPORT": "POSTGRES_PORT",
            "PGUSER": "POSTGRES_USER",
            "PGPASSWORD": "POSTGRES_PASSWORD",
            "PGDATABASE": "POSTGRES_DB",
        }
        normalized = dict(data)
        for pg_key, postgres_key in pg_map.items():
            if pg_key in normalized and postgres_key not in normalized:
                normalized[postgres_key] = normalized[pg_key]
        return normalized

    @property
    def cors_origins(self) -> List[str]:
        return _parse_cors_origins(self.cors_origins_env)

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy connection URL."""
        if self.database_url_env:
            return _build_sqlalchemy_url(self.database_url_env, "postgresql+asyncpg")
        return (
            f"postgresql+asyncpg://{quote_plus(self.postgres_user)}:"
            f"{quote_plus(self.postgres_password)}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync SQLAlchemy connection URL (Alembic migrations)."""
        if self.database_url_env:
            return _build_sqlalchemy_url(self.database_url_env, "postgresql+psycopg2")
        return (
            f"postgresql+psycopg2://{quote_plus(self.postgres_user)}:"
            f"{quote_plus(self.postgres_password)}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
