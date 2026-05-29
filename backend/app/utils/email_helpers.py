"""Email parsing and normalization helpers."""

import re
from email.utils import parseaddr, parsedate_to_datetime


REPLY_PREFIX_PATTERN = re.compile(r"^(re|fwd|fw):\s*", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")


def extract_email_address(raw: str | None) -> str:
    """Return normalized email address from a header value."""
    if not raw:
        return ""
    _, address = parseaddr(raw.strip())
    return address.lower()


def extract_email_list(raw_values: list[str] | str | None) -> list[str]:
    """Parse one or more header values into a deduplicated address list."""
    if not raw_values:
        return []

    if isinstance(raw_values, str):
        raw_values = [raw_values]

    addresses: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        for part in re.split(r"[,;]", value):
            address = extract_email_address(part)
            if address and address not in seen:
                seen.add(address)
                addresses.append(address)
    return addresses


def normalize_subject(subject: str | None) -> str:
    """Strip reply/forward prefixes for thread grouping."""
    normalized = (subject or "").strip()
    while True:
        updated = REPLY_PREFIX_PATTERN.sub("", normalized).strip()
        if updated == normalized:
            break
        normalized = updated
    return WHITESPACE_PATTERN.sub(" ", normalized)


def parse_email_datetime(value: str | None):
    """Safely parse RFC 2822 date headers."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def clean_message_id(value: str | None) -> str | None:
    """Normalize Message-ID header values."""
    if not value:
        return None
    cleaned = value.strip().strip("<>").strip()
    return cleaned or None


def build_search_snippet(text: str, query: str, max_length: int = 200) -> str:
    """Build a contextual snippet around query terms."""
    if not text:
        return ""

    lowered_text = text.lower()
    lowered_query = query.lower()
    index = lowered_text.find(lowered_query)

    if index == -1:
        snippet = text[:max_length]
    else:
        start = max(0, index - 60)
        end = min(len(text), index + len(query) + 60)
        snippet = text[start:end]

    snippet = WHITESPACE_PATTERN.sub(" ", snippet).strip()
    if len(snippet) > max_length:
        snippet = snippet[: max_length - 3].rstrip() + "..."
    return snippet
