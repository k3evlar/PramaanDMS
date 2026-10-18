"""JSON logs: UTC timestamps, request IDs, redaction, no log forging."""

from __future__ import annotations

import json
import logging

from app.logs import REDACTED, JsonFormatter, request_id_var, scrub


def _format(msg: str, **extra: object) -> dict:
    record = logging.LogRecord("pramaan.test", logging.INFO, __file__, 1, msg, None, None)
    for k, v in extra.items():
        setattr(record, k, v)
    return json.loads(JsonFormatter().format(record))


def test_log_line_is_json_with_utc_time() -> None:
    entry = _format("hello")
    assert entry["msg"] == "hello" and entry["level"] == "INFO"
    assert entry["ts"].endswith("Z")


def test_request_id_is_attached() -> None:
    token = request_id_var.set("abcdef0123456789")
    try:
        assert _format("x")["request_id"] == "abcdef0123456789"
    finally:
        request_id_var.reset(token)


def test_sensitive_fields_are_redacted() -> None:
    entry = _format("login", password="hunter2-secret", api_key="k", user="io_ravi",
                    headers={"Authorization": "Bearer abc", "Accept": "json"})
    assert entry["password"] == REDACTED and entry["api_key"] == REDACTED
    assert entry["headers"]["Authorization"] == REDACTED and entry["headers"]["Accept"] == "json"
    assert entry["user"] == "io_ravi"


def test_newlines_cannot_forge_extra_log_lines() -> None:
    line = JsonFormatter().format(logging.LogRecord("t", logging.INFO, __file__, 1,
                                                    "user\n{\"level\": \"ERROR\"}", None, None))
    assert "\n" not in line
    assert json.loads(line)["level"] == "INFO"


def test_scrub_handles_nested_and_odd_values() -> None:
    out = scrub({"a": [{"token": "x"}], "b": object()})
    assert out["a"][0]["token"] == REDACTED and isinstance(out["b"], str)


def test_exception_goes_to_log_field() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", None, sys.exc_info())
    entry = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in entry["exc"]
