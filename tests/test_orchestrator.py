"""End-to-end orchestrator wiring with all I/O faked."""

from __future__ import annotations

from post_it import orchestrator
from post_it.models import ApprovedPost


def test_generate_and_publish_draft(monkeypatch, settings, variants):
    # Fake the LLM provider so no network/key is needed.
    class _FakeProvider:
        def generate_variants(self, source, *, platform, n=3):
            return variants

    monkeypatch.setattr(
        "post_it.orchestrator.make_provider", lambda name, s: _FakeProvider()
    )

    generated = orchestrator.generate(
        source_name="ai",
        raw_input="AI agents",
        provider_name="anthropic",
        platform="linkedin",
        settings=settings,
    )
    assert len(generated.variants) == 3
    assert generated.platform == "linkedin"

    approved = ApprovedPost(variant=generated.variants[0], platform="linkedin")
    result = orchestrator.publish(approved=approved, mode="draft", settings=settings)
    assert result.success
    assert result.mode == "draft"
