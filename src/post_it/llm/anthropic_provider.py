"""Anthropic (Claude) provider — the default LLM backend.

Uses the official ``anthropic`` SDK's structured-output parsing
(``messages.parse`` + a pydantic ``output_format``) so the 3 variants come back
as a validated object instead of free text that needs regex-scraping.
"""

from __future__ import annotations

from typing import ClassVar

from post_it.exceptions import LLMError
from post_it.llm import prompts
from post_it.llm.base import LLMProvider, VariantsOutput
from post_it.models import PostVariant, SourceResult


class AnthropicProvider(LLMProvider):
    name: ClassVar[str] = "anthropic"

    def generate_variants(
        self, source: SourceResult, *, platform: str, n: int = 3
    ) -> list[PostVariant]:
        # Imported lazily so the package imports without the SDK installed
        # (e.g. when only the draft path or another provider is used).
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - import guard
            raise LLMError(
                "The 'anthropic' package is required for the Anthropic provider."
            ) from exc

        client = Anthropic(api_key=self.api_key)
        try:
            # No temperature/top_p: those are removed on Opus 4.8 (they 400).
            # Variety comes from the three named angles in the prompt.
            response = client.messages.parse(
                model=self.model,
                max_tokens=2000,
                system=prompts.system_for(platform),
                messages=[{"role": "user", "content": prompts.user_for(source)}],
                output_format=VariantsOutput,
            )
        except Exception as exc:
            raise LLMError(f"Anthropic request failed: {exc}") from exc

        output = response.parsed_output
        if output is None or not output.variants:
            raise LLMError("Anthropic returned no variants.")
        return self._to_variants(output)
