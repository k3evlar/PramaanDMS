"""Application settings, read from environment variables (prefix PRAMAAN_).

Values come from the environment only, normally from the git-ignored `.env` file that
`tools/setup_env.py` generates. Nothing secret is hard-coded. Secrets are pydantic
SecretStr values, so they never appear in logs, reprs or error messages.

Startup fails with a clear message (listing variable names, never values) when a value is
missing, malformed, or a weak placeholder such as "change-me".
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Values that must never reach a running system. `.env.example` uses "change-me".
WEAK_SECRETS = {"", "change-me", "changeme", "password", "admin", "secret", "test", "pramaan"}
MIN_SECRET_LENGTH = 16


def _check_secret(value: SecretStr, name: str) -> SecretStr:
    raw = value.get_secret_value()
    if raw.strip().lower() in WEAK_SECRETS or len(raw) < MIN_SECRET_LENGTH:
        raise ValueError(f"{name} is a placeholder or shorter than {MIN_SECRET_LENGTH} characters; "
                         "run tools/setup_env.py to generate real values")
    return value


def _check_url_password(value: SecretStr, name: str) -> SecretStr:
    """Connection URLs carry a password; reject URLs whose password is a placeholder."""
    raw = value.get_secret_value()
    if "change-me" in raw:
        raise ValueError(f"{name} still contains the placeholder 'change-me'; run tools/setup_env.py")
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRAMAAN_", extra="ignore", frozen=True)

    env: Literal["dev", "test", "demo"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    expose_api_docs: bool = Field(False, description="Serve /docs and /openapi.json (ASVS V13.4.5)")
    build_commit: str = Field("unknown", pattern=r"^[0-9a-zA-Z._-]{1,64}$")

    # Runtime database URL uses the least-privilege app role (threat T16).
    database_url: SecretStr
    # Migrations run as the schema owner in the one-shot migrate container only.
    migration_database_url: SecretStr | None = None
    valkey_url: SecretStr
    s3_endpoint: AnyHttpUrl
    s3_access_key: SecretStr
    s3_secret_key: SecretStr
    openbao_addr: AnyHttpUrl
    openbao_token: SecretStr
    clamav_host: str = Field("clamav", pattern=r"^[A-Za-z0-9.-]{1,253}$")
    clamav_port: int = Field(3310, ge=1, le=65535)
    health_timeout_seconds: float = Field(2.0, gt=0, le=10)

    # Evidence intake (Phase 5). Limits from REQUIREMENTS.md NFR-06 and section 4.4.
    s3_bucket: str = Field("pramaan-originals", pattern=r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
    retention_days: int = Field(3650, ge=1, le=36500, description="Object Lock compliance retention for originals")
    max_upload_bytes: int = Field(25 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    max_pages: int = Field(30, ge=1, le=500)
    max_image_pixels: int = Field(40_000_000, ge=1_000_000, le=200_000_000)
    # Temporary identity from request headers until real login exists (Phase 16, D82).
    # Refused outside the dev and test environments.
    dev_identity: bool = False

    @field_validator("s3_secret_key", "openbao_token")
    @classmethod
    def _strong_secret(cls, v: SecretStr, info) -> SecretStr:  # type: ignore[no-untyped-def]
        return _check_secret(v, f"PRAMAAN_{info.field_name.upper()}")

    @field_validator("database_url", "valkey_url", "migration_database_url")
    @classmethod
    def _no_placeholder_in_url(cls, v: SecretStr | None, info) -> SecretStr | None:  # type: ignore[no-untyped-def]
        if v is None:
            return v
        return _check_url_password(v, f"PRAMAAN_{info.field_name.upper()}")

    @field_validator("database_url", "migration_database_url")
    @classmethod
    def _postgres_url(cls, v: SecretStr | None, info) -> SecretStr | None:  # type: ignore[no-untyped-def]
        if v is not None and not v.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError(f"PRAMAAN_{info.field_name.upper()} must start with postgresql+psycopg://")
        return v

    @field_validator("valkey_url")
    @classmethod
    def _valkey_url(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().startswith(("redis://", "rediss://")):
            raise ValueError("PRAMAAN_VALKEY_URL must start with redis:// or rediss:// (Valkey speaks the same protocol)")
        return v


    @model_validator(mode="after")
    def _dev_identity_only_in_dev(self) -> "Settings":
        if self.dev_identity and self.env not in ("dev", "test"):
            raise ValueError("PRAMAAN_DEV_IDENTITY may only be true when PRAMAAN_ENV is dev or test")
        return self


class ConfigError(RuntimeError):
    """Raised with a readable message when the environment is not configured correctly."""


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        problems = []
        for err in e.errors():
            field = ".".join(str(p) for p in err["loc"]) or "settings"
            # Never echo input values: they may be secrets.
            problems.append(f"PRAMAAN_{field.upper()}: {err['msg']}")
        raise ConfigError("Invalid configuration:\n  " + "\n  ".join(problems)) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
