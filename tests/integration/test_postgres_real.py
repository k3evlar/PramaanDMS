"""Real PostgreSQL: the migration ran, and the app role cannot change evidence rows.

Every write here happens inside one transaction that is rolled back at the end, so the
test leaves no rows behind (custody rows could not be deleted afterwards).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError


def test_schema_is_at_the_latest_revision(app_url: str) -> None:
    engine = create_engine(app_url)
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
        assert conn.scalar(text("SELECT data_type FROM information_schema.columns WHERE table_name = "
                                "'custody_events' AND column_name = 'details'")) == "jsonb"
    engine.dispose()


@pytest.mark.parametrize("table", ["custody_events", "document_versions", "storage_objects"])
def test_app_role_has_no_update_or_delete_on_evidence_tables(app_url: str, table: str) -> None:
    engine = create_engine(app_url)
    with engine.connect() as conn:
        for priv in ("UPDATE", "DELETE", "TRUNCATE"):
            assert conn.scalar(text("SELECT has_table_privilege(current_user, :t, :p)"),
                               {"t": table, "p": priv}) is False, (table, priv)
        assert conn.scalar(text("SELECT has_table_privilege(current_user, :t, 'INSERT')"), {"t": table}) is True
    engine.dispose()


def test_app_role_cannot_rewrite_a_custody_event(app_url: str) -> None:
    engine = create_engine(app_url)
    case_id = uuid.uuid4()
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(text("INSERT INTO cases (id, case_number, title, created_by, created_at) "
                              "VALUES (:id, :n, 'it test', 'it.user', now())"), {"id": case_id, "n": f"IT-{case_id.hex[:8]}"})
            event_id = conn.scalar(text(
                "INSERT INTO custody_events (event_type, actor_id, actor_role, case_id, details, occurred_at) "
                "VALUES ('case.created', 'it.user', 'IO', :c, '{}'::jsonb, now()) RETURNING id"), {"c": case_id})
            for stmt in ("UPDATE custody_events SET actor_id = 'someone.else' WHERE id = :i",
                         "DELETE FROM custody_events WHERE id = :i"):
                sp = conn.begin_nested()
                with pytest.raises(ProgrammingError, match="permission denied"):
                    conn.execute(text(stmt), {"i": event_id})
                sp.rollback()
            sp = conn.begin_nested()
            with pytest.raises(ProgrammingError, match="permission denied"):
                conn.execute(text("CREATE TABLE sneaky (id int)"))
            sp.rollback()
        finally:
            tx.rollback()
    engine.dispose()


def test_database_rejects_inconsistent_verdicts(owner_url: str) -> None:
    engine = create_engine(owner_url)
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            checks = conn.scalars(text("SELECT conname FROM pg_constraint WHERE conrelid = 'verdicts'::regclass "
                                       "AND contype = 'c'")).all()
            assert "ck_verdicts_severity_matches_verdict" in checks
        finally:
            tx.rollback()
    engine.dispose()
