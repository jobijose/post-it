"""Abstract base for LLM providers plus the shared structured-output schema."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from post_it.models import PostVariant, SourceResult


class _Variant(BaseModel):
    """One generated variant as returned by the model (structured output)."""

    angle: str
    text: str


class VariantsOutput(BaseModel):
    """The structured object every provider asks the model to return."""

    variants: list[_Variant]


class LLMProvider(ABC):
    """Generates distinct post variants from collected source content.

    Concrete providers are registered by ``name`` in :mod:`post_it.registry`.
    """

    name: ClassVar[str]

    def __init__(self, *, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def generate_variants(
        self, source: SourceResult, *, platform: str, n: int = 3
    ) -> list[PostVariant]:
        """Return ``n`` distinct :class:`PostVariant` objects for ``platform``."""
        raise NotImplementedError

    @staticmethod
    def _to_variants(output: VariantsOutput) -> list[PostVariant]:
        return [
            PostVariant(index=i + 1, angle=v.angle, text=v.text.strip())
            for i, v in enumerate(output.variants)
        ]
