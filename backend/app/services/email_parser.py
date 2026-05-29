"""Email file parsing service."""

import email
import logging
from email import policy
from pathlib import Path

import mailparser

from app.schemas.email import ParsedEmailData
from app.utils.email_helpers import (
    clean_message_id,
    extract_email_address,
    extract_email_list,
    parse_email_datetime,
)
from app.utils.text_cleaner import clean_body_text, html_to_text

logger = logging.getLogger(__name__)


class EmailParserService:
    """Parse raw email files into structured metadata."""

    def parse_file(self, file_path: Path) -> ParsedEmailData | None:
        """Parse a single email file on disk."""
        try:
            raw_bytes = file_path.read_bytes()
            return self.parse_bytes(raw_bytes, source_file=str(file_path.name))
        except Exception as exc:
            logger.warning("Failed to parse email file %s: %s", file_path, exc)
            return None

    def parse_bytes(self, raw_bytes: bytes, *, source_file: str | None = None) -> ParsedEmailData | None:
        """Parse raw email bytes using mail-parser with stdlib fallback."""
        try:
            parsed = mailparser.parse_from_bytes(raw_bytes)
            if parsed.from_:
                sender_list = parsed.from_
            else:
                sender_list = []

            sender = extract_email_address(sender_list[0][1] if sender_list else "")
            receivers = extract_email_list([addr[1] for addr in (parsed.to or [])])
            cc = extract_email_list([addr[1] for addr in (parsed.cc or [])])

            body_text = clean_body_text(parsed.text_plain[0] if parsed.text_plain else "")
            body_html = parsed.text_html[0] if parsed.text_html else None
            if not body_text and body_html:
                body_text = html_to_text(body_html)

            return ParsedEmailData(
                message_id=clean_message_id(parsed.message_id),
                in_reply_to=clean_message_id(parsed.in_reply_to),
                references_header=(parsed.references or [None])[0],
                sender=sender or "unknown@local",
                receivers=receivers,
                cc=cc,
                subject=(parsed.subject or "").strip(),
                body_text=body_text,
                body_html=body_html,
                sent_at=parse_email_datetime(parsed.date),
                source_file=source_file,
            )
        except Exception as mailparser_error:
            logger.debug("mail-parser failed, falling back to stdlib: %s", mailparser_error)
            return self._parse_with_stdlib(raw_bytes, source_file=source_file)

    def _parse_with_stdlib(
        self, raw_bytes: bytes, *, source_file: str | None = None
    ) -> ParsedEmailData | None:
        """Fallback parser using Python's built-in email module."""
        try:
            message = email.message_from_bytes(raw_bytes, policy=policy.default)

            sender = extract_email_address(message.get("From"))
            receivers = extract_email_list(message.get("To", ""))
            cc = extract_email_list(message.get("Cc", ""))

            body_text = ""
            body_html = None
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and not body_text:
                        body_text = clean_body_text(part.get_content())
                    elif content_type == "text/html" and not body_html:
                        body_html = part.get_content()
            else:
                content = message.get_content()
                if message.get_content_type() == "text/html":
                    body_html = content
                    body_text = html_to_text(content)
                else:
                    body_text = clean_body_text(content)

            return ParsedEmailData(
                message_id=clean_message_id(message.get("Message-ID")),
                in_reply_to=clean_message_id(message.get("In-Reply-To")),
                references_header=message.get("References"),
                sender=sender or "unknown@local",
                receivers=receivers,
                cc=cc,
                subject=(message.get("Subject") or "").strip(),
                body_text=body_text,
                body_html=body_html,
                sent_at=parse_email_datetime(message.get("Date")),
                source_file=source_file,
            )
        except Exception as exc:
            logger.warning("stdlib email parser failed: %s", exc)
            return None
