"""Settings: loaded from the environment, validated, secrets never shown."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import ConfigError, Settings, load_settings

from .conftest import STRONG, settings_kwargs


def test_valid_settings_load(make_settings) -> None:
    s = make_settings()
    assert s.env == "test"
    assert s.expose_api_docs is False  # docs off by default (ASVS V13.4.5)


def test_secrets_never_appear_in_repr_or_str(make_settings) -> None:
    s = make_settings()
    assert STRONG not in repr(s)
    assert STRONG not in str(s.model_dump())


def test_settings_are_frozen(make_settings) -> None:
    s = make_settings()
    with pytest.raises(ValidationError):
        s.env = "dev"  # type: ignore[misc]


@pytest.mark.parametrize("field, value", [
    ("openbao_token", "change-me"),
    ("openbao_token", "short"),
    ("s3_secret_key", "password"),
])
def test_placeholder_or_weak_secret_is_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="placeholder or shorter"):
        Settings(**settings_kwargs(**{field: value}))


def test_placeholder_inside_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match="change-me"):
        Settings(**settings_kwargs(database_url="postgresql+psycopg://pramaan_app:change-me@db:5432/pramaan"))


@pytest.mark.parametrize("field, value, message", [
    ("database_url", f"mysql://u:{STRONG}@db/x", "postgresql\\+psycopg"),
    ("valkey_url", f"http://:{STRONG}@valkey:6379", "redis://"),
    ("clamav_port", 70000, "less than or equal"),
    ("health_timeout_seconds", 0, "greater than"),
    ("build_commit", "abc; rm -rf /", "pattern"),
])
def test_malformed_values_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**settings_kwargs(**{field: value}))


def test_missing_environment_gives_clear_error_without_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(__import__("os").environ):
        if key.startswith("PRAMAAN_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("PRAMAAN_OPENBAO_TOKEN", "change-me")
    with pytest.raises(ConfigError) as exc:
        load_settings()
    text = str(exc.value)
    assert "PRAMAAN_DATABASE_URL" in text and "PRAMAAN_VALKEY_URL" in text
    assert "PRAMAAN_OPENBAO_TOKEN" in text
    assert "change-me" not in text  # the rejected value itself is never echoed


def test_environment_variables_are_read(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in settings_kwargs(env="demo", log_level="WARNING").items():
        monkeypatch.setenv(f"PRAMAAN_{k.upper()}", str(v))
    s = load_settings()
    assert s.env == "demo" and s.log_level == "WARNING"
