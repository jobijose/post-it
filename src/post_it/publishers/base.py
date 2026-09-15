"""Abstract base for social publishers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from post_it.exceptions import PublishError
from post_it.models import ApprovedPost, PublishResult

# Per-platform max length for the post body. Add a key for a new platform.
PLATFORM_MAX_LENGTH: dict[str, int] = {
    "linkedin": 3000,
}


class SocialPublisher(ABC):
    """Publishes an approved post to a destination.

    Concrete publishers are registered by ``name`` in :mod:`post_it.registry`.
    """

    name: ClassVar[str]

    @abstractmethod
    def publish(self, approved: ApprovedPost) -> PublishResult:
        """Publish ``approved`` and return a :class:`PublishResult`."""
        raise NotImplementedError

    def validate(self, text: str, *, platform: str) -> None:
        """Reject empty or over-length posts before attempting to publish."""
        if not text.strip():
            raise PublishError("Refusing to publish an empty post.")
        limit = PLATFORM_MAX_LENGTH.get(platform)
        if limit and len(text) > limit:
            raise PublishError(
                f"Post is {len(text)} chars, over the {platform} limit of {limit}."
            )
