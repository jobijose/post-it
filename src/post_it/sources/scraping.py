"""Shared web fetch + main-text extraction helpers.

A single failed URL must never abort a batch, so :func:`fetch_and_extract`
captures network/parse errors into the returned :class:`ScrapedContent` rather
than raising.
"""

from __future__ import annotations

import httpx
import trafilatura

from post_it.models import ScrapedContent

_USER_AGENT = (
    "Mozilla/5.0 (compatible; post-it/0.1; +https://github.com/jobijose/post-it)"
)
_DEFAULT_TIMEOUT = 15.0


def make_client(timeout: float = _DEFAULT_TIMEOUT) -> httpx.Client:
    """Create an httpx client configured for scraping."""
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    )


def fetch_and_extract(url: str, *, client: httpx.Client) -> ScrapedContent:
    """Fetch ``url`` and extract its main text. Never raises for one bad URL."""
    try:
        resp = client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        return ScrapedContent(url=url, error=f"fetch failed: {exc}")

    html = resp.text
    try:
        text = trafilatura.extract(html, include_comments=False, include_tables=False)
        title = _extract_title(html)
    except Exception as exc:  # trafilatura can raise on malformed input
        return ScrapedContent(url=url, error=f"extraction failed: {exc}")

    if not text or not text.strip():
        return ScrapedContent(url=url, title=title, error="no main text extracted")

    return ScrapedContent(url=url, title=title, text=text.strip())


def _extract_title(html: str) -> str | None:
    meta = trafilatura.extract_metadata(html)
    if meta and getattr(meta, "title", None):
        return meta.title
    return None
