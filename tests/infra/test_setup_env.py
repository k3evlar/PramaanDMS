"""tools/setup_env.py: generates strong, consistent local secrets and never overwrites by accident."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.config import Settings
from tools import setup_env

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    shutil.copy(ROOT / ".env.example", tmp_path / ".env.example")
    return tmp_path


def _env(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#"))


def test_every_placeholder_is_replaced_with_a_unique_strong_value(root: Path) -> None:
    setup_env.build(root)
    env = _env(root / ".env")
    assert "change-me" not in env.values()  # comments copied from the template may mention it
    secret_keys = [k for k in env if k.endswith(("PASSWORD", "TOKEN", "SECRET_KEY"))]
    assert len(secret_keys) == 7  # 4 passwords, 2 S3 secret keys, 1 OpenBao token
    values = [env[k] for k in secret_keys]
    assert len(set(values)) == len(values)
    assert all(len(v) >= 40 for v in values)
    assert env["PRAMAAN_HTTP_BIND"] == "127.0.0.1"  # non-secret defaults are kept


def test_generated_values_pass_the_app_validation(root: Path) -> None:
    setup_env.build(root)
    env = _env(root / ".env")
    # Build the same URLs docker-compose.yml builds, then validate them like the app does.
    Settings(
        database_url=f"postgresql+psycopg://pramaan_app:{env['PRAMAAN_DB_APP_PASSWORD']}@postgres:5432/pramaan",
        valkey_url=f"redis://:{env['VALKEY_PASSWORD']}@valkey:6379/0",
        s3_endpoint="http://seaweedfs:8333",
        s3_access_key=env["PRAMAAN_S3_APP_ACCESS_KEY"],
        s3_secret_key=env["PRAMAAN_S3_APP_SECRET_KEY"],
        openbao_addr="http://openbao:8200",
        openbao_token=env["PRAMAAN_OPENBAO_TOKEN"],
    )


def test_service_secret_files_match_env(root: Path) -> None:
    setup_env.build(root)
    env = _env(root / ".env")
    conf = (root / "docker/secrets/valkey.conf").read_text(encoding="utf-8")
    assert f"requirepass {env['VALKEY_PASSWORD']}" in conf
    s3 = json.loads((root / "docker/secrets/seaweedfs_s3.json").read_text(encoding="utf-8"))
    by_name = {i["name"]: i for i in s3["identities"]}
    assert by_name["pramaan_app"]["credentials"][0]["accessKey"] == env["PRAMAAN_S3_APP_ACCESS_KEY"]
    assert "Admin" not in by_name["pramaan_app"]["actions"]  # least privilege for the runtime identity
    assert "Admin" in by_name["pramaan_admin"]["actions"]


def test_refuses_to_overwrite_without_force(root: Path) -> None:
    setup_env.build(root)
    first = (root / ".env").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError, match="--force"):
        setup_env.build(root)
    assert (root / ".env").read_text(encoding="utf-8") == first
    setup_env.build(root, force=True)
    assert (root / ".env").read_text(encoding="utf-8") != first


def test_cli_exit_codes_and_no_secret_output(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert setup_env.main(["--root", str(root)]) == 0
    out = capsys.readouterr().out
    env = _env(root / ".env")
    assert env["PRAMAAN_OPENBAO_TOKEN"] not in out
    assert setup_env.main(["--root", str(root)]) == 1


def test_bad_template_line_is_reported(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("THIS LINE IS BROKEN\n", encoding="utf-8")
    with pytest.raises(ValueError, match="bad line"):
        setup_env.build(tmp_path)
