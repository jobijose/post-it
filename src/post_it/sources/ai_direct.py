"""Option B: AI-direct input — a free-text topic OR a single web link."""

from __future__ import annotations

from typing import ClassVar
from urllib.parse import urlparse

from post_it.exceptions import SourceError
from post_it.models import SourceResult
from post_it.sources.base import ContentSource
from post_it.sources.scraping import fetch_and_extract, make_client


class AiDirectSource(ContentSource):
    """Take either a topic prompt or a single URL and feed it to the LLM.

    If ``raw_input`` parses as an ``http(s)`` URL it is scraped; otherwise it is
    treated as a free-text topic passed straight through to the LLM.
    """

    name: ClassVar[str] = "ai"

    def collect(self, raw_input: str) -> SourceResult:
        value = raw_input.strip()
        if not value:
            raise SourceError("AI-direct input is empty; provide a topic or a URL.")

        if self._is_url(value):
            with make_client() as client:
                content = fetch_and_extract(value, client=client)
            if not content.ok:
                raise SourceError(f"Failed to read {value}: {content.error}")
            return SourceResult(
                kind="ai_direct_link",
                scraped=[content],
                combined_text=content.text,
            )

        return SourceResult(kind="ai_direct_topic", topic=value, combined_text=value)

    @staticmethod
    def _is_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
