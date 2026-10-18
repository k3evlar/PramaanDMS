"""API skeleton: health endpoints, request IDs, safe errors, docs exposure."""

from __future__ import annotations

import json
import logging
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def ok(_s) -> None:
    return None


def leaks_secret(_s) -> None:
    raise ValueError("password=super-secret-value in connection string")


def slow(_s) -> None:
    time.sleep(5)


@pytest.fixture
def client_factory(make_settings):
    def _make(checks=None, **settings):
        app = create_app(make_settings(**settings), checks=checks or {"postgres": ok, "valkey": ok})
        return TestClient(app, raise_server_exceptions=False)
    return _make


def test_live_endpoint(client_factory) -> None:
    r = client_factory().get("/health/live")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_health_ok_when_all_dependencies_pass(client_factory) -> None:
    r = client_factory({"postgres": ok, "valkey": ok, "seaweedfs": ok, "openbao": ok, "clamav": ok}).get("/health")
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ok"
    assert set(body["checks"]) == {"postgres", "valkey", "seaweedfs", "openbao", "clamav"}
    assert body["time"].endswith("Z") and "version" in body and "commit" in body


def test_health_degraded_names_failure_without_leaking_details(client_factory) -> None:
    r = client_factory({"postgres": ok, "valkey": leaks_secret}).get("/health")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "degraded"
    assert body["checks"]["valkey"] == {"status": "fail", "latency_ms": body["checks"]["valkey"]["latency_ms"],
                                        "error": "ValueError"}
    assert "super-secret" not in r.text and "password" not in r.text


def test_slow_dependency_times_out_instead_of_hanging(client_factory) -> None:
    # Keep one event loop open, and time only the request (not the test client's shutdown).
    with client_factory({"slow": slow}, health_timeout_seconds=0.2) as c:
        start = time.perf_counter()
        r = c.get("/health")
        elapsed = time.perf_counter() - start
    assert r.status_code == 503 and r.json()["checks"]["slow"]["error"] == "TimeoutError"
    assert elapsed < 3


def test_request_id_is_generated_and_safe_ones_are_kept(client_factory) -> None:
    c = client_factory()
    assert len(c.get("/health/live").headers["x-request-id"]) == 32
    assert c.get("/health/live", headers={"X-Request-ID": "abc-12345678"}).headers["x-request-id"] == "abc-12345678"
    bad = c.get("/health/live", headers={"X-Request-ID": "x" * 200})
    assert bad.headers["x-request-id"] != "x" * 200


def test_unexpected_error_returns_generic_message(client_factory) -> None:
    c = client_factory()

    @c.app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("internal detail: /srv/app/secret.py line 42")

    r = c.get("/boom")
    assert r.status_code == 500
    assert r.json()["error"] == "internal_error" and r.json()["request_id"]
    assert "internal detail" not in r.text and "Traceback" not in r.text


def test_api_docs_hidden_by_default_and_shown_when_enabled(client_factory) -> None:
    hidden = client_factory()
    assert hidden.get("/docs").status_code == 404 and hidden.get("/openapi.json").status_code == 404
    shown = client_factory(expose_api_docs=True)
    assert shown.get("/openapi.json").status_code == 200


def test_unknown_route_is_404(client_factory) -> None:
    assert client_factory().get("/no/such/route").status_code == 404


def test_request_log_has_path_but_not_query_string(client_factory, caplog: pytest.LogCaptureFixture) -> None:
    c = client_factory()
    with caplog.at_level(logging.INFO, logger="pramaan.api"):
        c.get("/health/live?token=should-not-be-logged")
    records = [r for r in caplog.records if r.getMessage() == "request"]
    assert records and records[-1].path == "/health/live"
    assert "should-not-be-logged" not in json.dumps([vars(r) for r in records], default=str)
