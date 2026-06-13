"""OpenAI provider — optional alternative backend (proves the abstraction).

Mirrors :class:`AnthropicProvider`, returning the same :class:`PostVariant`
shape via OpenAI's structured-output (JSON schema) parsing. Lives behind the
``openai`` optional extra.
"""

from __future__ import annotations

from typing import ClassVar

from post_it.exceptions import LLMError
from post_it.llm import prompts
from post_it.llm.base import LLMProvider, VariantsOutput
from post_it.models import PostVariant, SourceResult


class OpenAIProvider(LLMProvider):
    name: ClassVar[str] = "openai"

    def generate_variants(
        self, source: SourceResult, *, platform: str, n: int = 3
    ) -> list[PostVariant]:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - import guard
            raise LLMError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install with: pip install 'post-it[openai]'"
            ) from exc

        client = OpenAI(api_key=self.api_key)
        try:
            completion = client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts.system_for(platform)},
                    {"role": "user", "content": prompts.user_for(source)},
                ],
                response_format=VariantsOutput,
            )
        except Exception as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        output = completion.choices[0].message.parsed
        if output is None or not output.variants:
            raise LLMError("OpenAI returned no variants.")
        return self._to_variants(output)
