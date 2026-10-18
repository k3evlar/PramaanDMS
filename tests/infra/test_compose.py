"""Static checks of docker-compose.yml and the Dockerfiles.

These run without Docker. They prove the stack is described safely (pinned images, health
checks, no default secrets, internal networks, hardened app containers). Whether the
containers actually become healthy is checked with Docker (see PROGRESS.md, Phase 3).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
SERVICES = COMPOSE["services"]
LONG_RUNNING = ["frontend", "api", "worker", "postgres", "seaweedfs", "valkey", "openbao", "clamav"]
APP_SERVICES = ["api", "worker", "frontend"]
ONE_SHOT = ["migrate", "storage-init"]
BACKING = ["postgres", "valkey", "seaweedfs", "openbao"]
ENV_EXAMPLE = {line.split("=", 1)[0] for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
               if line and not line.startswith("#") and "=" in line}


def test_exactly_the_planned_services() -> None:
    assert set(SERVICES) == set(LONG_RUNNING) | set(ONE_SHOT)
    assert len(LONG_RUNNING) == 8


@pytest.mark.parametrize("name", LONG_RUNNING)
def test_every_long_running_service_has_a_health_check(name: str) -> None:
    hc = SERVICES[name].get("healthcheck")
    assert hc and hc.get("test"), name
    assert SERVICES[name].get("restart") == "unless-stopped"


@pytest.mark.parametrize("name", [n for n in SERVICES if "image" in SERVICES[n] and "build" not in SERVICES[n] and n not in APP_SERVICES + ONE_SHOT])
def test_third_party_images_are_pinned(name: str) -> None:
    image = SERVICES[name]["image"]
    repo, _, tag = image.rpartition(":")
    assert repo and tag and tag != "latest" and re.search(r"\d+\.\d+", tag), image


@pytest.mark.parametrize("dockerfile", ["docker/api.Dockerfile", "frontend/Dockerfile"])
def test_dockerfile_base_images_are_pinned(dockerfile: str) -> None:
    froms = re.findall(r"^FROM\s+(\S+)", (ROOT / dockerfile).read_text(encoding="utf-8"), re.M)
    assert froms
    for f in froms:
        assert re.search(r":\d+\.\d+\.\d+", f), f


def test_api_image_runs_as_non_root() -> None:
    text = (ROOT / "docker/api.Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"^USER\s+pramaan\s*$", text, re.M)
    assert "nginx-unprivileged" in (ROOT / "frontend/Dockerfile").read_text(encoding="utf-8")


def test_only_the_frontend_publishes_a_port_on_localhost_by_default() -> None:
    published = {n for n, s in SERVICES.items() if s.get("ports")}
    assert published == {"frontend"}
    assert SERVICES["frontend"]["ports"] == ["${PRAMAAN_HTTP_BIND:-127.0.0.1}:${PRAMAAN_HTTP_PORT:-8080}:8080"]


def test_backing_services_have_no_internet() -> None:
    assert COMPOSE["networks"]["backend"]["internal"] is True
    for name in BACKING:
        assert SERVICES[name]["networks"] == ["backend"], name
    assert "egress" in SERVICES["clamav"]["networks"]  # signature downloads only
    assert "egress" not in SERVICES["api"]["networks"] and "egress" not in SERVICES["worker"]["networks"]


@pytest.mark.parametrize("name", APP_SERVICES)
def test_app_containers_are_hardened(name: str) -> None:
    s = SERVICES[name]
    assert s["read_only"] is True and s["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in s["security_opt"]


def test_every_variable_is_in_env_example_and_secrets_are_required() -> None:
    lines = (ROOT / "docker-compose.yml").read_text(encoding="utf-8").splitlines()
    text = "\n".join(line for line in lines if not line.lstrip().startswith("#"))  # skip comments
    refs = re.findall(r"\$\{([A-Z0-9_]+)(:[-?][^}]*)?\}", text)
    assert refs
    for name, modifier in refs:
        assert name in ENV_EXAMPLE, f"{name} missing from .env.example"
        if re.search(r"PASSWORD|TOKEN|SECRET|ACCESS_KEY", name):
            assert modifier.startswith(":?"), f"{name} must be required (${{VAR:?...}})"


def test_no_literal_secrets_in_compose() -> None:
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k, v
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
    for key, value in walk(COMPOSE):
        if isinstance(key, str) and re.search(r"PASSWORD|TOKEN|SECRET", key) and isinstance(value, str):
            assert "${" in value, f"{key} has a literal value"


def test_startup_order_and_migrations() -> None:
    assert SERVICES["migrate"]["command"] == ["alembic", "upgrade", "head"]
    assert SERVICES["migrate"]["restart"] == "no"
    assert SERVICES["api"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    for dep in BACKING:
        assert SERVICES["api"]["depends_on"][dep]["condition"] == "service_healthy"
    # The app connects as the least-privilege role; only migrate knows the owner password.
    assert "pramaan_app:" in SERVICES["api"]["environment"]["PRAMAAN_DATABASE_URL"]
    assert "pramaan_owner:" in SERVICES["migrate"]["environment"]["PRAMAAN_MIGRATION_DATABASE_URL"]
    assert "PRAMAAN_MIGRATION_DATABASE_URL" not in SERVICES["api"]["environment"]


def test_worker_uses_the_json_only_celery_app() -> None:
    assert SERVICES["worker"]["command"][:3] == ["celery", "-A", "app.worker.celery_app"]


def test_nginx_hides_detailed_health_and_version() -> None:
    conf = (ROOT / "frontend/nginx.conf").read_text(encoding="utf-8")
    assert "server_tokens off;" in conf
    assert re.search(r"location = /api/health \{\s*return 404;", conf)
    assert "proxy_pass http://api:8000/;" in conf


def test_dockerignore_keeps_secrets_and_git_out_of_images() -> None:
    lines = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    for entry in (".git", ".env", "docker/secrets", ".venv", ".tools"):
        assert entry in lines, entry


def test_gitignore_keeps_local_secrets_and_tools_out_of_git() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in (".env", "docker/secrets/", ".tools/", "frontend/node_modules/", ".venv/"):
        assert entry in lines, entry


def test_storage_init_runs_before_the_api_with_admin_keys_only() -> None:
    si = SERVICES["storage-init"]
    assert si["command"] == ["python", "-m", "app.evidence.storage_init"] and si["restart"] == "no"
    assert si["depends_on"]["seaweedfs"]["condition"] == "service_healthy"
    assert SERVICES["api"]["depends_on"]["storage-init"]["condition"] == "service_completed_successfully"
    assert "PRAMAAN_S3_ADMIN_SECRET_KEY" in si["environment"]
    # The runtime services never see the admin identity.
    for name in ("api", "worker"):
        assert not any("ADMIN" in k or "ADMIN" in str(v) for k, v in SERVICES[name]["environment"].items()), name
    assert si["read_only"] is True and si["cap_drop"] == ["ALL"] and si["networks"] == ["backend"]


def test_dev_identity_is_off_by_default() -> None:
    assert SERVICES["api"]["environment"]["PRAMAAN_DEV_IDENTITY"] == "${PRAMAAN_DEV_IDENTITY:-false}"
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert re.search(r"^PRAMAAN_DEV_IDENTITY=false$", env, re.M)
