"""Tests for LLM providers (SDK client faked)."""

from __future__ import annotations

import pytest

from post_it.exceptions import LLMError
from post_it.llm.anthropic_provider import AnthropicProvider
from post_it.llm.base import VariantsOutput, _Variant


class _FakeMessages:
    def __init__(self, output, captured):
        self._output = output
        self._captured = captured

    def parse(self, **kwargs):
        self._captured.update(kwargs)

        class _Resp:
            parsed_output = self._output

        return _Resp()


class _FakeClient:
    def __init__(self, output, captured):
        self.messages = _FakeMessages(output, captured)


def test_anthropic_returns_three_variants(monkeypatch, source_result):
    captured: dict = {}
    output = VariantsOutput(
        variants=[
            _Variant(angle="insightful", text="A"),
            _Variant(angle="punchy", text="B"),
            _Variant(angle="story-driven", text="C"),
        ]
    )
    monkeypatch.setattr(
        "anthropic.Anthropic", lambda **kw: _FakeClient(output, captured)
    )

    provider = AnthropicProvider(model="claude-opus-4-8", api_key="k")
    variants = provider.generate_variants(source_result, platform="linkedin")

    assert len(variants) == 3
    assert [v.index for v in variants] == [1, 2, 3]
    # temperature/top_p must never be sent on Opus 4.8.
    assert "temperature" not in captured
    assert "top_p" not in captured
    assert captured["model"] == "claude-opus-4-8"


def test_anthropic_empty_raises(monkeypatch, source_result):
    output = VariantsOutput(variants=[])
    monkeypatch.setattr(
        "anthropic.Anthropic", lambda **kw: _FakeClient(output, {})
    )
    provider = AnthropicProvider(model="claude-opus-4-8", api_key="k")
    with pytest.raises(LLMError):
        provider.generate_variants(source_result, platform="linkedin")
