"""Tests against the real services in Docker. They skip themselves when Docker is not on.

How to run them (needs Docker Desktop):

    python tools/setup_env.py
    docker compose -f docker-compose.yml -f docker/compose.integration.yml up -d --build --wait
    PRAMAAN_IT=1 python -m pytest tests/integration -v

The overlay publishes PostgreSQL on 127.0.0.1:55432 and the SeaweedFS S3 port on
127.0.0.1:58333, and turns on the development identity for the API. Passwords and keys
are read from the git-ignored .env file; nothing secret is in this repository.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKIP_REASON = ("needs Docker: start the stack with `docker compose -f docker-compose.yml -f "
               "docker/compose.integration.yml up -d --build --wait`, then set PRAMAAN_IT=1")
PG = "127.0.0.1:55432"
S3 = "http://127.0.0.1:58333"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("PRAMAAN_IT") == "1":
        return
    skip = pytest.mark.skip(reason=SKIP_REASON)
    for item in items:
        if Path(str(item.fspath)).resolve().is_relative_to(Path(__file__).parent):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        pytest.fail(".env is missing: run python tools/setup_env.py before the Docker tests")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


@pytest.fixture(scope="session")
def owner_url(dotenv: dict[str, str]) -> str:
    return f"postgresql+psycopg://pramaan_owner:{dotenv['PRAMAAN_DB_OWNER_PASSWORD']}@{PG}/pramaan"


@pytest.fixture(scope="session")
def app_url(dotenv: dict[str, str]) -> str:
    return f"postgresql+psycopg://pramaan_app:{dotenv['PRAMAAN_DB_APP_PASSWORD']}@{PG}/pramaan"


def s3_client(access: str, secret: str):  # type: ignore[no-untyped-def]
    import boto3
    from botocore.config import Config

    return boto3.client("s3", endpoint_url=S3, region_name="us-east-1", aws_access_key_id=access,
                        aws_secret_access_key=secret,
                        config=Config(s3={"addressing_style": "path"}, request_checksum_calculation="when_required",
                                      response_checksum_validation="when_required"))


@pytest.fixture(scope="session")
def s3_admin(dotenv: dict[str, str]):  # type: ignore[no-untyped-def]
    return s3_client(dotenv["PRAMAAN_S3_ADMIN_ACCESS_KEY"], dotenv["PRAMAAN_S3_ADMIN_SECRET_KEY"])


@pytest.fixture(scope="session")
def s3_app(dotenv: dict[str, str]):  # type: ignore[no-untyped-def]
    return s3_client(dotenv["PRAMAAN_S3_APP_ACCESS_KEY"], dotenv["PRAMAAN_S3_APP_SECRET_KEY"])
