"""Database engine, declarative base and sessions.

The engine is created from settings for the running stack (PostgreSQL, app role). Tests
pass their own engine (SQLite in memory), so the same repository code runs in both.
Types are chosen to work on both: JSON becomes JSONB on PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import JSON, DateTime, Engine, MetaData, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from .config import Settings

# Stable constraint names, so migrations and models agree on every database.
NAMING = {"ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
          "ck": "ck_%(table_name)s_%(constraint_name)s",
          "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", "pk": "pk_%(table_name)s"}

JSONType = JSON().with_variant(JSONB(), "postgresql")


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware UTC timestamps on every database (SQLite drops the timezone)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:  # type: ignore[no-untyped-def]
        if value is not None and value.tzinfo is None:
            raise ValueError("naive datetime: use datetime.now(timezone.utc)")
        return value.astimezone(timezone.utc) if value is not None else None

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:  # type: ignore[no-untyped-def]
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@lru_cache(maxsize=4)
def _engine_for(url: str, timeout: float) -> Engine:
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5,
                         connect_args={"connect_timeout": max(1, int(timeout))})


def get_engine(s: Settings) -> Engine:
    return _engine_for(s.database_url.get_secret_value(), s.health_timeout_seconds)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
