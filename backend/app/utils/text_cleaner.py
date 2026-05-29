"""Text cleaning utilities for email bodies."""

import re
from html import unescape

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def html_to_text(html: str | None) -> str:
    """Convert HTML email body to plain text."""
    if not html:
        return ""
    text = unescape(html)
    text = HTML_TAG_PATTERN.sub(" ", text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def clean_body_text(text: str | None) -> str:
    """Normalize whitespace in plain-text email bodies."""
    if not text:
        return ""
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """Truncate long email bodies for embedding and summarization."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
