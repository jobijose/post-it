"""Abstract base for content sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from post_it.models import SourceResult


class ContentSource(ABC):
    """A way of turning raw user input into normalized :class:`SourceResult`.

    Concrete sources are registered by ``name`` in
    :mod:`post_it.registry` so the CLI can select them by string.
    """

    name: ClassVar[str]

    @abstractmethod
    def collect(self, raw_input: str) -> SourceResult:
        """Produce a :class:`SourceResult` from ``raw_input``.

        ``raw_input`` is a path to a ``.txt`` file (Option A) or a topic/link
        string (Option B), depending on the concrete source.
        """
        raise NotImplementedError
