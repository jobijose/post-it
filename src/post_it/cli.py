"""Typer CLI: argument parsing + the interactive review/approve flow only.

All business logic lives in :mod:`post_it.orchestrator` so a future web UI can
reuse it directly.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from post_it import orchestrator
from post_it.config import load_settings, save_credentials
from post_it.exceptions import PostItError
from post_it.models import ApprovedPost
from post_it.registry import LLM_PROVIDERS, PUBLISHERS, SOURCES

app = typer.Typer(help="Turn web content into ready-to-publish social posts.")
console = Console()


@app.command()
def run(
    source: str | None = typer.Option(
        None, "--source", "-s", help=f"Input source: {', '.join(SOURCES)}"
    ),
    source_input: str | None = typer.Option(
        None, "--input", "-i", help="Path to URL .txt file, or a topic/URL."
    ),
    provider: str | None = typer.Option(
        None, "--provider", "-p", help=f"LLM provider: {', '.join(LLM_PROVIDERS)}"
    ),
    platform: str = typer.Option("linkedin", "--platform", help="Target platform."),
    mode: str | None = typer.Option(
        None, "--mode", "-m", help=f"Publish mode: {', '.join(PUBLISHERS)}"
    ),
) -> None:
    """Generate 3 post variants, pick one, and publish it."""
    settings = load_settings()

    source = source or _choose("Input source", list(SOURCES))
    if not source_input:
        prompt = (
            "Path to .txt file of URLs"
            if source == "url-file"
            else "Topic or a URL to write about"
        )
        source_input = typer.prompt(prompt)
    provider = provider or settings.default_provider

    try:
        with console.status("Generating variants..."):
            generated = orchestrator.generate(
                source_name=source,
                raw_input=source_input,
                provider_name=provider,
                platform=platform,
                settings=settings,
            )
    except PostItError as exc:
        _fail(str(exc))

    if generated.source.failed_urls:
        console.print(
            f"[yellow]Skipped URLs that yielded no content:[/] "
            f"{', '.join(generated.source.failed_urls)}"
        )

    for v in generated.variants:
        console.print(
            Panel(
                v.text,
                title=f"[bold]Option {v.index}[/] · {v.angle} · {v.char_count} chars",
                border_style="cyan",
            )
        )

    choice = typer.prompt("Select a variant", type=int)
    selected = next((v for v in generated.variants if v.index == choice), None)
    if selected is None:
        _fail(f"No variant numbered {choice}.")

    if not typer.confirm(f"Approve and publish option {choice}?"):
        console.print("Aborted — nothing published.")
        raise typer.Exit()

    mode = mode or _choose("Publish mode", list(PUBLISHERS))
    approved = ApprovedPost(variant=selected, platform=platform)

    try:
        result = orchestrator.publish(approved=approved, mode=mode, settings=settings)
    except PostItError as exc:
        _fail(str(exc))

    console.print(f"[green]✓[/] {result.detail}")
    if result.location:
        console.print(f"  {result.location}")


@app.command()
def auth(platform: str = typer.Argument(..., help="Platform to authenticate (linkedin).")) -> None:
    """Run a one-time OAuth flow and store the access token."""
    if platform != "linkedin":
        _fail(f"Unsupported auth platform: {platform}")

    from post_it.publishers.linkedin_oauth import fetch_author_urn, run_local_auth_flow

    settings = load_settings()
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        _fail("Set POSTIT_LINKEDIN_CLIENT_ID and POSTIT_LINKEDIN_CLIENT_SECRET first.")

    try:
        token = run_local_auth_flow(
            client_id=settings.linkedin_client_id,
            client_secret=settings.linkedin_client_secret.get_secret_value(),
        )
        urn = fetch_author_urn(token)
    except PostItError as exc:
        _fail(str(exc))

    path = save_credentials(access_token=token, author_urn=urn)
    console.print(f"[green]✓[/] Saved LinkedIn credentials to {path}")


def _choose(label: str, options: list[str]) -> str:
    console.print(f"{label}:")
    for i, opt in enumerate(options, 1):
        console.print(f"  {i}. {opt}")
    idx = typer.prompt(f"Choose {label.lower()}", type=int)
    if not 1 <= idx <= len(options):
        _fail(f"Invalid choice: {idx}")
    return options[idx - 1]


def _fail(message: str) -> None:
    console.print(f"[red]Error:[/] {message}")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
