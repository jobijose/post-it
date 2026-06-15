"""Option A: a ``.txt`` file containing one or more website URLs."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from post_it.exceptions import SourceError
from post_it.models import ScrapedContent, SourceResult
from post_it.sources.base import ContentSource
from post_it.sources.scraping import fetch_and_extract, make_client


class UrlFileSource(ContentSource):
    """Read URLs from a text file (one per line) and scrape each page.

    Blank lines and lines starting with ``#`` are ignored. Failed URLs are
    recorded but skipped from the combined text fed to the LLM.
    """

    name: ClassVar[str] = "url-file"

    def collect(self, raw_input: str) -> SourceResult:
        path = Path(raw_input)
        if not path.is_file():
            raise SourceError(f"URL file not found: {path}")

        urls = self._read_urls(path)
        if not urls:
            raise SourceError(f"No URLs found in {path}")

        scraped: list[ScrapedContent] = []
        with make_client() as client:
            for url in urls:
                scraped.append(fetch_and_extract(url, client=client))

        if not any(c.ok for c in scraped):
            failed = ", ".join(c.url for c in scraped)
            raise SourceError(f"All URLs failed to scrape: {failed}")

        return SourceResult(
            kind="url_file",
            scraped=scraped,
            combined_text=self._combine(scraped),
        )

    @staticmethod
    def _read_urls(path: Path) -> list[str]:
        urls: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
        return urls

    @staticmethod
    def _combine(scraped: list[ScrapedContent]) -> str:
        parts: list[str] = []
        for c in scraped:
            if not c.ok:
                continue
            header = c.title or c.url
            parts.append(f"## {header}\n{c.text}")
        return "\n\n".join(parts)
