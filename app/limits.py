"""Request body size limit, applied before any parsing (NFR-06, ASVS V5.2.1).

A request that declares a larger Content-Length is refused at once. A request without
one (chunked) is counted while it streams and cut off once it passes the limit, so a
client cannot fill the server's disk with an endless upload.
"""

from __future__ import annotations

import json

from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

FORM_OVERHEAD = 64 * 1024  # multipart boundaries and the small text fields


class BodySizeLimit:
    def __init__(self, app: ASGIApp, max_body: int) -> None:
        self.app, self.max_body = app, max_body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope.get("headers") or []).get(b"content-length")
        if declared is not None:
            try:
                too_big = int(declared) > self.max_body
            except ValueError:
                too_big = True
            if too_big:
                await _send_413(send)
                return

        seen = 0

        async def counted() -> Message:
            nonlocal seen
            message = await receive()
            if message["type"] == "http.request":
                seen += len(message.get("body", b""))
                if seen > self.max_body:
                    # Raised inside body parsing; FastAPI passes HTTPException through as is.
                    raise HTTPException(413)
            return message

        await self.app(scope, counted, send)


async def _send_413(send: Send) -> None:
    body = json.dumps({"error": "too_large", "message": "The request is too large."}).encode()
    await send({"type": "http.response.start", "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()),
                            (b"connection", b"close")]})
    await send({"type": "http.response.body", "body": body})
