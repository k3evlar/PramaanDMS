"""One error shape for the API: {"error": code, "message": text, "request_id": id}.

`code` is stable for clients and tests. `message` is plain English for people and never
contains document content, secrets or stack traces (ASVS V16.5.1).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logs import request_id_var


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _body(code: str, message: str) -> dict[str, str]:
    return {"error": code, "message": message, "request_id": request_id_var.get()}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Field names only; the submitted values are not echoed back.
        fields = sorted({".".join(str(p) for p in e.get("loc", ())[1:]) or "body" for e in exc.errors()})
        return JSONResponse(status_code=422, content=_body("invalid_request", "Check these fields: " + ", ".join(fields)))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        messages = {404: "Not found.", 405: "Method not allowed.", 413: "The request is too large."}
        code = {404: "not_found", 405: "method_not_allowed", 413: "too_large"}.get(exc.status_code, "http_error")
        return JSONResponse(status_code=exc.status_code, content=_body(code, messages.get(exc.status_code, "Request failed.")),
                            headers=getattr(exc, "headers", None))
