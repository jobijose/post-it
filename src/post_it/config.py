"""Configuration and secret loading via pydantic-settings.

Values are read from environment variables (prefixed ``POSTIT_``) and an
optional ``.env`` file. Secrets are wrapped in :class:`SecretStr` so they don't
leak into logs or reprs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Where the LinkedIn token + cached author URN are persisted between runs.
CREDENTIALS_DIR = Path.home() / ".post-it"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"


class Settings(BaseSettings):
    """Runtime configuration for post-it."""

    model_config = SettingsConfigDict(
        env_prefix="POSTIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM selection
    default_provider: str = "anthropic"
    default_model: str = "claude-opus-4-8"

    # LLM keys
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # LinkedIn
    linkedin_client_id: str | None = None
    linkedin_client_secret: SecretStr | None = None
    linkedin_access_token: SecretStr | None = None
    linkedin_author_urn: str | None = None
    linkedin_api_version: str = "202505"

    # Output
    draft_dir: Path = Path("./drafts")

    def model_for(self, provider: str) -> str:
        """Return the model id to use for ``provider`` (currently global)."""
        return self.default_model


def load_settings() -> Settings:
    """Load settings, merging any persisted LinkedIn credentials.

    Persisted credentials (written by ``post-it auth linkedin``) act as a
    fallback so the token survives across runs without living in ``.env``.
    """
    settings = Settings()
    creds = _read_credentials()
    if creds:
        if not settings.linkedin_access_token and creds.get("access_token"):
            settings.linkedin_access_token = SecretStr(creds["access_token"])
        if not settings.linkedin_author_urn and creds.get("author_urn"):
            settings.linkedin_author_urn = creds["author_urn"]
    return settings


def _read_credentials() -> dict | None:
    try:
        with CREDENTIALS_FILE.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_credentials(*, access_token: str, author_urn: str | None = None) -> Path:
    """Persist LinkedIn credentials to ``~/.post-it/credentials.json`` (0600)."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    payload = _read_credentials() or {}
    payload["access_token"] = access_token
    if author_urn:
        payload["author_urn"] = author_urn
    CREDENTIALS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(CREDENTIALS_FILE, 0o600)
    return CREDENTIALS_FILE
