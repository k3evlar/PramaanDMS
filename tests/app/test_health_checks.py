"""Individual dependency checks against fake servers (no real services needed)."""

from __future__ import annotations

import socket
import threading

import httpx
import pytest

from app import health


def _fake_clamd(reply: bytes) -> tuple[int, threading.Thread]:
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve() -> None:
        conn, _ = srv.accept()
        with conn:
            assert conn.recv(16) == b"zPING\0"
            conn.sendall(reply)
        srv.close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    return port, t


def test_clamav_check_accepts_pong(make_settings) -> None:
    port, t = _fake_clamd(b"PONG\0")
    health.check_clamav(make_settings(clamav_host="127.0.0.1", clamav_port=port))
    t.join(2)


def test_clamav_check_rejects_wrong_reply(make_settings) -> None:
    port, t = _fake_clamd(b"ERROR\0")
    with pytest.raises(RuntimeError, match="no PONG"):
        health.check_clamav(make_settings(clamav_host="127.0.0.1", clamav_port=port))
    t.join(2)


def test_clamav_check_fails_when_nothing_listens(make_settings) -> None:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    with pytest.raises(OSError):
        health.check_clamav(make_settings(clamav_host="127.0.0.1", clamav_port=port))


@pytest.mark.parametrize("status, should_pass", [(200, True), (429, False), (503, False)])
def test_openbao_check_needs_200(make_settings, monkeypatch: pytest.MonkeyPatch, status: int, should_pass: bool) -> None:
    seen = {}

    def fake_get(url: str, timeout: float) -> httpx.Response:
        seen["url"] = url
        return httpx.Response(status, request=httpx.Request("GET", url))

    monkeypatch.setattr(health.httpx, "get", fake_get)
    s = make_settings()
    if should_pass:
        health.check_openbao(s)
    else:
        with pytest.raises(RuntimeError):
            health.check_openbao(s)
    assert seen["url"].endswith("/v1/sys/health")


def test_seaweedfs_check_uses_healthz(make_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> httpx.Response:
        assert url.endswith("/healthz")
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(health.httpx, "get", fake_get)
    with pytest.raises(httpx.HTTPStatusError):
        health.check_seaweedfs(make_settings())


def test_default_checks_cover_every_backing_service() -> None:
    assert set(health.DEFAULT_CHECKS) == {"postgres", "valkey", "seaweedfs", "openbao", "clamav"}
