"""Exception hierarchy for post-it.

All user-facing failures should raise a :class:`PostItError` (or a subclass) so
the CLI can present a clean message instead of a traceback.
"""

from __future__ import annotations


class PostItError(Exception):
    """Base class for all post-it errors."""


class ConfigError(PostItError):
    """Missing or invalid configuration (e.g. an API key that isn't set)."""


class SourceError(PostItError):
    """A content source failed to produce any usable content."""


class LLMError(PostItError):
    """An LLM provider failed to generate variants."""


class PublishError(PostItError):
    """A publisher failed to publish an approved post."""


class AuthError(PublishError):
    """Authentication/authorization failure when talking to a platform."""
