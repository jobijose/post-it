"""Shared fixtures."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from post_it.config import Settings
from post_it.models import PostVariant, SourceResult


@pytest.fixture
def settings(tmp_path):
    return Settings(
        anthropic_api_key=SecretStr("test-key"),
        openai_api_key=SecretStr("test-key"),
        linkedin_access_token=SecretStr("test-token"),
        linkedin_author_urn="urn:li:person:abc123",
        draft_dir=tmp_path / "drafts",
    )


@pytest.fixture
def source_result():
    return SourceResult(kind="ai_direct_topic", topic="AI agents", combined_text="AI agents")


@pytest.fixture
def variants():
    return [
        PostVariant(index=i, angle=a, text=f"Variant {i} text")
        for i, a in enumerate(["insightful", "punchy", "story-driven"], 1)
    ]
