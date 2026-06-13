"""Data layer for post-it.

Pydantic v2 models so the same objects validate inputs at I/O boundaries and
serialize cleanly to JSON for a future web UI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal["url_file", "ai_direct_topic", "ai_direct_link"]
PublishMode = Literal["draft", "linkedin"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ScrapedContent(BaseModel):
    """The result of fetching and extracting a single web page.

    On failure, ``error`` is set and ``text`` is empty rather than raising, so a
    single bad URL never aborts a batch.
    """

    url: str
    title: str | None = None
    text: str = ""
    fetched_at: datetime = Field(default_factory=_utcnow)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text.strip())


class SourceResult(BaseModel):
    """Normalized output of a :class:`~post_it.sources.base.ContentSource`."""

    kind: SourceKind
    scraped: list[ScrapedContent] = Field(default_factory=list)
    topic: str | None = None
    combined_text: str = ""

    @property
    def failed_urls(self) -> list[str]:
        return [c.url for c in self.scraped if not c.ok]


class PostVariant(BaseModel):
    """One of the generated post options the user chooses between."""

    index: int
    angle: str
    text: str
    char_count: int = 0

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.char_count:
            self.char_count = len(self.text)


class GeneratedPost(BaseModel):
    """The full set of generated variants for one run."""

    source: SourceResult
    provider: str
    platform: str
    variants: list[PostVariant]


class ApprovedPost(BaseModel):
    """A single variant the user selected and approved for publishing."""

    variant: PostVariant
    platform: str


class PublishResult(BaseModel):
    """Outcome of a publish attempt."""

    mode: PublishMode
    success: bool
    location: str | None = None
    detail: str | None = None
