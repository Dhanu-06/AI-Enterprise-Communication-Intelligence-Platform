"""AI-generated email summary service."""

import logging
import threading

from app.core.config import settings
from app.utils.text_cleaner import truncate_text

logger = logging.getLogger(__name__)


class SummaryService:
    """Generate concise summaries for email content."""

    _lock = threading.Lock()
    _pipeline = None

    def __init__(self) -> None:
        self.model_name = settings.summary_model

    def _get_pipeline(self):
        with self._lock:
            if self._pipeline is None:
                try:
                    from transformers import pipeline

                    logger.info("Loading summarization model: %s", self.model_name)
                    self._pipeline = pipeline(
                        "summarization",
                        model=self.model_name,
                        tokenizer=self.model_name,
                    )
                except Exception as exc:
                    logger.warning("Could not load summarization model: %s", exc)
                    self._pipeline = False
            return self._pipeline if self._pipeline is not False else None

    def summarize(self, subject: str, body_text: str) -> str:
        """Return an AI summary or extractive fallback."""
        content = truncate_text(f"{subject}. {body_text}".strip(), max_chars=3000)
        if not content:
            return "Empty email with no content."

        pipeline = self._get_pipeline()
        if pipeline is not None:
            try:
                result = pipeline(
                    content,
                    max_length=130,
                    min_length=30,
                    do_sample=False,
                    truncation=True,
                )
                summary = result[0]["summary_text"].strip()
                if summary:
                    return summary
            except Exception as exc:
                logger.warning("Summarization pipeline failed: %s", exc)

        return self._extractive_fallback(content)

    def summarize_thread(self, subjects: list[str], bodies: list[str]) -> str:
        """Summarize an entire conversation thread."""
        combined_parts = []
        for subject, body in zip(subjects, bodies):
            combined_parts.append(f"{subject}: {truncate_text(body, max_chars=500)}")
        combined = " | ".join(combined_parts)
        return self.summarize("Thread conversation", combined)

    @staticmethod
    def _extractive_fallback(text: str) -> str:
        """Simple extractive summary when the transformer model is unavailable."""
        sentences = [part.strip() for part in text.replace("\n", " ").split(".") if part.strip()]
        if not sentences:
            return truncate_text(text, max_chars=200)
        preview = ". ".join(sentences[:2])
        if len(preview) > 250:
            preview = preview[:247].rstrip() + "..."
        return preview + ("." if not preview.endswith(".") else "")
