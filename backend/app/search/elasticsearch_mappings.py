"""Elasticsearch index definitions and templates."""

from typing import Any

INDEX_TEMPLATE_NAME = "comm_intel_emails_template"
INDEX_TEMPLATE_PATTERN = "emails*"

EMAIL_INDEX_SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "analyzer": {
            "email_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding", "porter_stem"],
            }
        }
    },
}

EMAIL_INDEX_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "email_id": {"type": "keyword"},
        "archive_id": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "sender": {
            "type": "keyword",
            "fields": {"text": {"type": "text", "analyzer": "email_analyzer"}},
        },
        "receivers": {"type": "keyword"},
        "cc": {"type": "keyword"},
        "subject": {
            "type": "text",
            "analyzer": "email_analyzer",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 1024}},
        },
        "body_text": {"type": "text", "analyzer": "email_analyzer"},
        "summary": {"type": "text", "analyzer": "email_analyzer"},
        "sent_at": {"type": "date"},
        "created_at": {"type": "date"},
        "source_file": {"type": "keyword"},
    },
}


def build_index_template() -> dict[str, Any]:
    """Return composable index template body for Elasticsearch."""
    return {
        "index_patterns": [INDEX_TEMPLATE_PATTERN],
        "template": {
            "settings": EMAIL_INDEX_SETTINGS,
            "mappings": EMAIL_INDEX_MAPPINGS,
        },
        "priority": 200,
        "_meta": {"description": "Email archive full-text search index template"},
    }


def build_index_body() -> dict[str, Any]:
    """Return index creation body when templates are unavailable."""
    return {
        "settings": EMAIL_INDEX_SETTINGS,
        "mappings": EMAIL_INDEX_MAPPINGS,
    }
