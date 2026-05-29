"""Shared application singletons for external services."""

from app.services.chroma_service import ChromaService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.ingestion_service import IngestionService

elasticsearch_service = ElasticsearchService()
chroma_service = ChromaService()
ingestion_service = IngestionService(elasticsearch_service, chroma_service)
