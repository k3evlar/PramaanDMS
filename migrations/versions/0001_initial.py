"""Initial empty revision.

Phase 3 sets up Alembic only. It creates no tables: the first schema (cases, documents,
versions, storage objects, fingerprints, verdicts, custody events) arrives in Phase 5.
Database roles are created by docker/postgres/init/01-roles.sh, not by migrations,
because the migration role must not be able to create roles.

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""
from __future__ import annotations

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
