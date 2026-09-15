"""Central wiring: map config strings to source / provider / publisher classes.

Adding a new source, LLM provider, or social platform is a one-line entry here
— the CLI and orchestrator stay unchanged.
"""

from __future__ import annotations

from post_it.config import Settings
from post_it.exceptions import ConfigError
from post_it.llm.anthropic_provider import AnthropicProvider
from post_it.llm.base import LLMProvider
from post_it.llm.openai_provider import OpenAIProvider
from post_it.publishers.base import SocialPublisher
from post_it.publishers.draft import DraftPublisher
from post_it.publishers.linkedin import LinkedInPublisher
from post_it.sources.ai_direct import AiDirectSource
from post_it.sources.base import ContentSource
from post_it.sources.url_file import UrlFileSource

SOURCES: dict[str, type[ContentSource]] = {
    UrlFileSource.name: UrlFileSource,
    AiDirectSource.name: AiDirectSource,
}

LLM_PROVIDERS: dict[str, type[LLMProvider]] = {
    AnthropicProvider.name: AnthropicProvider,
    OpenAIProvider.name: OpenAIProvider,
}

PUBLISHERS = (DraftPublisher.name, LinkedInPublisher.name)


def make_source(name: str) -> ContentSource:
    try:
        return SOURCES[name]()
    except KeyError as exc:
        raise ConfigError(
            f"Unknown source '{name}'. Choices: {', '.join(SOURCES)}"
        ) from exc


def make_provider(name: str, settings: Settings) -> LLMProvider:
    try:
        cls = LLM_PROVIDERS[name]
    except KeyError as exc:
        raise ConfigError(
            f"Unknown provider '{name}'. Choices: {', '.join(LLM_PROVIDERS)}"
        ) from exc

    key_attr = f"{name}_api_key"
    secret = getattr(settings, key_attr, None)
    if secret is None:
        raise ConfigError(f"Missing API key: set POSTIT_{key_attr.upper()}.")
    return cls(model=settings.model_for(name), api_key=secret.get_secret_value())


def make_publisher(mode: str, settings: Settings) -> SocialPublisher:
    if mode == DraftPublisher.name:
        return DraftPublisher(draft_dir=settings.draft_dir)
    if mode == LinkedInPublisher.name:
        token = settings.linkedin_access_token
        return LinkedInPublisher(
            access_token=token.get_secret_value() if token else "",
            author_urn=settings.linkedin_author_urn,
            api_version=settings.linkedin_api_version,
        )
    raise ConfigError(f"Unknown publish mode '{mode}'. Choices: {', '.join(PUBLISHERS)}")
