"""Worker configuration and the Alembic setup."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.worker import make_celery

from .conftest import STRONG

ROOT = Path(__file__).resolve().parents[2]


def test_worker_accepts_json_only(make_settings) -> None:
    app = make_celery(make_settings())
    assert app.conf.task_serializer == "json" and app.conf.result_serializer == "json"
    assert list(app.conf.accept_content) == ["json"]
    assert "pickle" not in app.conf.accept_content and "pickle" not in app.conf.result_accept_content
    assert app.conf.enable_utc is True and app.conf.task_time_limit > 0


def test_worker_has_ping_task(make_settings) -> None:
    app = make_celery(make_settings())
    assert "pramaan.ping" in app.tasks
    assert app.tasks["pramaan.ping"].run() == "pong"


def _alembic() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    return cfg


def test_revisions_form_one_line() -> None:
    script = ScriptDirectory.from_config(_alembic())
    revs = list(script.walk_revisions())
    assert [r.revision for r in revs] == ["0002", "0001"]
    assert revs[0].down_revision == "0001" and revs[1].down_revision is None
    assert script.get_heads() == ["0002"]


def test_migrations_match_the_models_and_downgrade_cleanly(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Upgrade an empty SQLite database, compare it with the models, then go back down."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine, inspect

    from app.models import Base

    url = f"sqlite:///{(tmp_path / 'm.db').as_posix()}"
    monkeypatch.setenv("PRAMAAN_MIGRATION_DATABASE_URL", url)
    command.upgrade(_alembic(), "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], diff
    assert set(inspect(engine).get_table_names()) >= {"cases", "case_members", "documents", "document_versions",
                                                       "storage_objects", "fingerprints", "verdicts", "custody_events"}
    command.downgrade(_alembic(), "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    engine.dispose()


def test_offline_upgrade_produces_version_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_MIGRATION_DATABASE_URL", f"postgresql+psycopg://pramaan_owner:{STRONG}@db:5432/pramaan")
    buf = io.StringIO()
    cfg = _alembic()
    cfg.output_buffer = buf
    with redirect_stdout(buf):
        command.upgrade(cfg, "head", sql=True)
    sql = buf.getvalue()
    assert "CREATE TABLE alembic_version" in sql
    assert "INSERT INTO alembic_version (version_num) VALUES ('0001')" in sql
    assert "UPDATE alembic_version SET version_num='0002'" in sql
    assert STRONG not in sql


def test_postgres_migration_makes_evidence_rows_append_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_MIGRATION_DATABASE_URL", f"postgresql+psycopg://pramaan_owner:{STRONG}@db:5432/pramaan")
    buf = io.StringIO()
    cfg = _alembic()
    cfg.output_buffer = buf
    with redirect_stdout(buf):
        command.upgrade(cfg, "head", sql=True)
    sql = buf.getvalue()
    assert "REVOKE UPDATE, DELETE, TRUNCATE ON custody_events, document_versions, storage_objects FROM pramaan_app" in sql
    assert "CHECK ((verdict = 'Tampered') = (severity <> 'None'))" in sql
    assert "JSONB" in sql


@pytest.mark.parametrize("url, message", [("", "not set"), ("postgresql+psycopg://o:change-me@db/p", "change-me")])
def test_migrations_refuse_missing_or_placeholder_url(monkeypatch: pytest.MonkeyPatch, url: str, message: str) -> None:
    monkeypatch.setenv("PRAMAAN_MIGRATION_DATABASE_URL", url)
    with pytest.raises(SystemExit, match=message):
        command.upgrade(_alembic(), "head", sql=True)


def test_database_roles_script_is_least_privilege() -> None:
    sql = (ROOT / "docker/postgres/init/01-roles.sh").read_text(encoding="utf-8")
    assert "set -eu" in sql and "ON_ERROR_STOP=1" in sql
    for role in ("pramaan_owner", "pramaan_app"):
        assert f"CREATE ROLE {role}" in sql
    assert sql.count("NOSUPERUSER NOCREATEDB NOCREATEROLE") == 2
    # Passwords go in as psql variables, never pasted into SQL text.
    assert "PASSWORD :'owner_pw'" in sql and "PASSWORD :'app_pw'" in sql
    assert "<<'SQL'" in sql  # quoted heredoc: the shell does not expand anything inside
    assert "GRANT ALL" not in sql.upper()
    assert "REVOKE CREATE ON SCHEMA public FROM PUBLIC" in sql
