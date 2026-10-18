"""Health checks for every service the API depends on.

/health/live   process is up (used by the container health check).
/health        checks PostgreSQL, Valkey, SeaweedFS, OpenBao and ClamAV in parallel, each
               with a timeout. Returns 200 when all pass, 503 otherwise.

Responses name the failing service and the error class only. They never include
connection strings, hostnames with credentials, or exception messages that might carry
secrets. Full details go to the server log. nginx does not expose /health to browsers
(REQUIREMENTS.md 4.7, ASVS V13.4.5); use `python -m app.health_cli` inside the stack.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import redis
from sqlalchemy import text

from .config import Settings
from .db import get_engine
from .version import APP_VERSION

log = logging.getLogger("pramaan.health")

Check = Callable[[Settings], None]  # raises on failure


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    latency_ms: float
    error: str | None = None


def check_postgres(s: Settings) -> None:
    with get_engine(s).connect() as conn:
        if conn.execute(text("SELECT 1")).scalar_one() != 1:
            raise RuntimeError("unexpected result")


def check_valkey(s: Settings) -> None:
    client = redis.Redis.from_url(s.valkey_url.get_secret_value(), socket_timeout=s.health_timeout_seconds,
                                  socket_connect_timeout=s.health_timeout_seconds)
    try:
        if not client.ping():
            raise RuntimeError("no PONG")
    finally:
        client.close()


def check_seaweedfs(s: Settings) -> None:
    # SeaweedFS's S3 gateway serves GET /healthz without credentials (weed/s3api/s3api_server.go).
    r = httpx.get(f"{str(s.s3_endpoint).rstrip('/')}/healthz", timeout=s.health_timeout_seconds)
    r.raise_for_status()


def check_openbao(s: Settings) -> None:
    # /v1/sys/health returns 200 only when initialized, unsealed and active.
    r = httpx.get(f"{str(s.openbao_addr).rstrip('/')}/v1/sys/health", timeout=s.health_timeout_seconds)
    if r.status_code != 200:
        raise RuntimeError(f"status {r.status_code}")


def check_clamav(s: Settings) -> None:
    # clamd protocol: "zPING\0" must be answered with "PONG\0".
    with socket.create_connection((s.clamav_host, s.clamav_port), timeout=s.health_timeout_seconds) as sock:
        sock.sendall(b"zPING\0")
        reply = sock.recv(16)
    if not reply.startswith(b"PONG"):
        raise RuntimeError("no PONG")


DEFAULT_CHECKS: dict[str, Check] = {
    "postgres": check_postgres,
    "valkey": check_valkey,
    "seaweedfs": check_seaweedfs,
    "openbao": check_openbao,
    "clamav": check_clamav,
}


async def _run_one(name: str, check: Check, s: Settings) -> CheckResult:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(asyncio.to_thread(check, s), timeout=s.health_timeout_seconds + 1)
        return CheckResult(name, True, round((time.perf_counter() - start) * 1000, 1))
    except Exception as e:  # noqa: BLE001 - every failure must become a result, never a crash
        elapsed = round((time.perf_counter() - start) * 1000, 1)
        log.warning("health check failed", extra={"check": name, "error_type": type(e).__name__})
        return CheckResult(name, False, elapsed, type(e).__name__)


async def run_checks(s: Settings, checks: dict[str, Check]) -> tuple[bool, dict]:
    results = await asyncio.gather(*(_run_one(n, c, s) for n, c in checks.items()))
    ok = all(r.ok for r in results)
    body = {
        "status": "ok" if ok else "degraded",
        "version": APP_VERSION,
        "commit": s.build_commit,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "checks": {r.name: ({"status": "ok", "latency_ms": r.latency_ms} if r.ok
                            else {"status": "fail", "latency_ms": r.latency_ms, "error": r.error})
                   for r in results},
    }
    return ok, body
