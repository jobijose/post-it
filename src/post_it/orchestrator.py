"""The reusable core: source -> LLM -> publisher.

The CLI (and any future web UI) calls only :func:`generate` and :func:`publish`,
handling the interactive review/selection in between. No I/O-bound interactive
logic lives here.
"""

from __future__ import annotations

from post_it.config import Settings
from post_it.models import ApprovedPost, GeneratedPost, PublishResult
from post_it.registry import make_provider, make_publisher, make_source


def generate(
    *,
    source_name: str,
    raw_input: str,
    provider_name: str,
    platform: str,
    settings: Settings,
    n: int = 3,
) -> GeneratedPost:
    """Collect content and produce ``n`` post variants."""
    source = make_source(source_name)
    result = source.collect(raw_input)

    provider = make_provider(provider_name, settings)
    variants = provider.generate_variants(result, platform=platform, n=n)

    return GeneratedPost(
        source=result, provider=provider_name, platform=platform, variants=variants
    )


def publish(
    *, approved: ApprovedPost, mode: str, settings: Settings
) -> PublishResult:
    """Publish an approved post via the chosen mode (draft / linkedin)."""
    publisher = make_publisher(mode, settings)
    return publisher.publish(approved)
