"""Search integrations."""

from app.search.chroma_config import COLLECTION_METADATA, EMBEDDING_BATCH_SIZE
from app.search.elasticsearch_mappings import (
    EMAIL_INDEX_MAPPINGS,
    EMAIL_INDEX_SETTINGS,
    INDEX_TEMPLATE_NAME,
    INDEX_TEMPLATE_PATTERN,
    build_index_body,
    build_index_template,
)

__all__ = [
    "COLLECTION_METADATA",
    "EMAIL_INDEX_MAPPINGS",
    "EMAIL_INDEX_SETTINGS",
    "EMBEDDING_BATCH_SIZE",
    "INDEX_TEMPLATE_NAME",
    "INDEX_TEMPLATE_PATTERN",
    "build_index_body",
    "build_index_template",
]
