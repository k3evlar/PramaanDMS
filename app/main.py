"""FastAPI application factory.

Phase 3 provides the skeleton: settings, JSON logging, request IDs, safe error handling and
health endpoints. Phase 5 adds cases and evidence intake. Later phases add their routers
here (see ARCHITECTURE.md modules).

Tests pass their own session factory and object store (SQLite and an in-memory store);
the running stack builds them from settings (PostgreSQL and SeaweedFS).
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker

from . import errors
from .cases.api import router as cases_router
from .config import Settings, get_settings
from .db import get_engine, make_session_factory
from .evidence.api import router as evidence_router
from .evidence.storage import ObjectStore, S3ObjectStore
from .health import DEFAULT_CHECKS, Check, run_checks
from .limits import FORM_OVERHEAD, BodySizeLimit
from .logs import configure_logging, request_id_var
from .version import APP_VERSION

log = logging.getLogger("pramaan.api")

# An incoming request ID (for example set by nginx) is accepted only if it looks safe;
# otherwise a new one is generated. This keeps log lines and headers clean.
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def create_app(settings: Settings | None = None, checks: dict[str, Check] | None = None,
               session_factory: sessionmaker[Session] | None = None,
               object_store: ObjectStore | None = None) -> FastAPI:
    s = settings or get_settings()
    configure_logging(s.log_level)
    app = FastAPI(
        title="Pramaan DMS API",
        version=APP_VERSION,
        docs_url="/docs" if s.expose_api_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if s.expose_api_docs else None,
    )
    app.state.settings = s
    app.state.checks = checks if checks is not None else DEFAULT_CHECKS
    # Neither connects yet: the engine and the S3 client connect on first use.
    app.state.session_factory = session_factory or make_session_factory(get_engine(s))
    app.state.object_store = object_store or S3ObjectStore.from_settings(s)
    errors.install(app)
    # Added first, so it runs inside the request-ID middleware below.
    app.add_middleware(BodySizeLimit, max_body=s.max_upload_bytes + FORM_OVERHEAD)

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(rid)
        start = time.perf_counter()
        status = 500
        try:
            try:
                response = await call_next(request)
            except Exception as exc:  # noqa: BLE001 - turn any crash into a safe response
                # Handled here, while the request ID is still set, so the caller can quote it.
                # Full detail goes to the server log only (ASVS V16.5.1).
                log.error("unhandled error", exc_info=exc, extra={"path": request.url.path})
                response = JSONResponse(status_code=500, content={"error": "internal_error", "request_id": rid})
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            # Path only, never the query string (ASVS V14.2.1: no sensitive data from URLs in logs).
            log.info("request", extra={"method": request.method, "path": request.url.path, "status": status,
                                       "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                                       "client": request.client.host if request.client else None})
            request_id_var.reset(token)

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok", "version": APP_VERSION}

    @app.get("/health", tags=["health"])
    async def health(request: Request) -> JSONResponse:
        ok, body = await run_checks(request.app.state.settings, request.app.state.checks)
        return JSONResponse(status_code=200 if ok else 503, content=body)

    app.include_router(cases_router)
    app.include_router(evidence_router)

    log.info("api started", extra={"version": APP_VERSION, "commit": s.build_commit, "env": s.env})
    return app


def __getattr__(name: str) -> FastAPI:
    # `uvicorn app.main:app` builds the app on first access, so importing this module in
    # tests does not require a configured environment.
    if name == "app":
        globals()["app"] = create_app()
        return globals()["app"]
    raise AttributeError(name)
