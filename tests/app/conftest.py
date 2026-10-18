"""Shared helpers for backend tests. Every secret here is a test-only random-looking value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.custody.models import CustodyEvent
from app.db import make_session_factory
from app.evidence.storage import InMemoryObjectStore
from app.main import create_app
from app.models import Base

STRONG = "t3st-only-value-0123456789abcdef"


def settings_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "env": "test",
        "database_url": f"postgresql+psycopg://pramaan_app:{STRONG}@localhost:5432/pramaan",
        "valkey_url": f"redis://:{STRONG}@localhost:6379/0",
        "s3_endpoint": "http://localhost:8333",
        "s3_access_key": "PRMTESTACCESSKEY0001",
        "s3_secret_key": STRONG,
        "openbao_addr": "http://localhost:8200",
        "openbao_token": STRONG,
        "clamav_host": "localhost",
        "clamav_port": 3310,
        "health_timeout_seconds": 0.5,
    }
    base.update(overrides)
    return base


@pytest.fixture
def make_settings():
    def _make(**overrides: Any) -> Settings:
        return Settings(**settings_kwargs(**overrides))
    return _make


@dataclass
class Api:
    """The real app wired to SQLite in memory and the in-memory write-once store."""

    client: TestClient
    store: InMemoryObjectStore
    sf: sessionmaker[Session]

    def as_user(self, user: str, role: str) -> dict[str, str]:
        return {"X-Pramaan-User": user, "X-Pramaan-Role": role}

    def events(self, event_type: str | None = None) -> list[CustodyEvent]:
        with self.sf() as s:
            q = select(CustodyEvent).order_by(CustodyEvent.id)
            if event_type:
                q = q.where(CustodyEvent.event_type == event_type)
            return list(s.scalars(q))


def sqlite_sessions() -> sessionmaker[Session]:
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk(conn, _):  # type: ignore[no-untyped-def]
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return make_session_factory(engine)


@pytest.fixture
def make_api(make_settings):  # type: ignore[no-untyped-def]
    def _make(**overrides: Any) -> Api:
        overrides.setdefault("dev_identity", True)
        overrides.setdefault("max_upload_bytes", 256 * 1024)
        overrides.setdefault("max_pages", 3)
        overrides.setdefault("max_image_pixels", 1_000_000)
        store, sf = InMemoryObjectStore(), sqlite_sessions()
        app = create_app(make_settings(**overrides), checks={}, session_factory=sf, object_store=store)
        return Api(TestClient(app, raise_server_exceptions=False), store, sf)
    return _make
