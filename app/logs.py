"""Structured JSON logging for forensic traceability.

Every log line is one JSON object with a UTC timestamp, level, logger, message, and the
request ID of the request being served (if any). JSON encoding escapes newlines and quotes,
so user text cannot forge extra log lines (ASVS V16.4.1).

Fields whose names look sensitive (password, token, secret, key, cookie, authorization)
are replaced by "[redacted]" before writing (ASVS V16.2.5). Document content is never
logged; callers log IDs and hashes only (REQUIREMENTS.md 4.8).

Note: these are operational logs. The tamper-evident action log (Merkle transparency log)
is a separate component built in Phase 20.
"""

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

SENSITIVE_KEY = re.compile(r"pass(word)?|secret|token|api[_-]?key|access[_-]?key|private|cookie|authori[sz]ation|credential", re.I)
REDACTED = "[redacted]"

# Attributes every LogRecord has; anything else was passed via `extra=` and is logged as a field.
_STANDARD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


def scrub(value: Any, key: str = "") -> Any:
    """Return a copy of `value` with sensitive-looking fields redacted (recursively)."""
    if key and SENSITIVE_KEY.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {k: scrub(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_var.get()
        if rid:
            entry["request_id"] = rid
        for k, v in vars(record).items():
            if k not in _STANDARD_ATTRS and not k.startswith("_"):
                entry[k] = scrub(v, k)
        if record.exc_info:
            # Stack traces go to the server log only, never to API responses (ASVS V16.5.1).
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, sort_keys=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install one JSON handler on the root logger. Safe to call more than once.

    Replaces earlier Pramaan handlers and plain stream handlers (default console output),
    but keeps other handlers, such as test log capture.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._pramaan = True  # type: ignore[attr-defined]
    root = logging.getLogger()
    root.handlers[:] = [h for h in root.handlers
                        if not getattr(h, "_pramaan", False) and type(h) is not logging.StreamHandler] + [handler]
    root.setLevel(level)
    # Uvicorn's own access log is replaced by our request log middleware (no query strings).
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers[:] = []
        logging.getLogger(name).propagate = True
