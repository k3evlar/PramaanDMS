"""Alembic environment.

Migrations run as the schema owner (PRAMAAN_MIGRATION_DATABASE_URL), in the one-shot
`migrate` container only. The API and worker use the least-privilege app role
(PRAMAAN_DATABASE_URL), which cannot change the schema (threat T16).
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import create_engine, pool

# Every model, so autogenerate and tests can compare migrations with the models.
from app.models import Base  # noqa: E402

target_metadata = Base.metadata


def _url() -> str:
    url = os.environ.get("PRAMAAN_MIGRATION_DATABASE_URL", "")
    if not url:
        raise SystemExit("PRAMAAN_MIGRATION_DATABASE_URL is not set (schema owner connection for migrations)")
    if "change-me" in url:
        raise SystemExit("PRAMAAN_MIGRATION_DATABASE_URL still contains 'change-me'; run tools/setup_env.py")
    return url


def run_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
