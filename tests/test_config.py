"""Config and credential-storage tests."""

from __future__ import annotations

import json

from post_it import config as config_mod
from post_it.config import Settings, save_credentials


def test_secrets_are_masked(monkeypatch):
    monkeypatch.setenv("POSTIT_ANTHROPIC_API_KEY", "super-secret")
    settings = Settings()
    assert "super-secret" not in repr(settings)
    assert settings.anthropic_api_key.get_secret_value() == "super-secret"


def test_save_and_load_credentials(monkeypatch, tmp_path):
    creds = tmp_path / "credentials.json"
    monkeypatch.setattr(config_mod, "CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CREDENTIALS_FILE", creds)

    save_credentials(access_token="tok123", author_urn="urn:li:person:x")
    data = json.loads(creds.read_text())
    assert data["access_token"] == "tok123"
    assert data["author_urn"] == "urn:li:person:x"
    # 0600 perms
    assert oct(creds.stat().st_mode)[-3:] == "600"
