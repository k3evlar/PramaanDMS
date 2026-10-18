"""Cleaning rules for free text and file names (REQUIREMENTS.md section 4.1).

Free text is stored as data only. It is never used to build queries, paths or commands.
"""

from __future__ import annotations

import unicodedata

# Unicode categories removed from free text: control (Cc), format (Cf, for example
# bidirectional overrides), surrogates (Cs), private use (Co) and unassigned (Cn).
_DROP = {"Cc", "Cf", "Cs", "Co", "Cn"}


class InvalidText(ValueError):
    """A free-text value broke a rule. The message names the rule, never the value."""


def clean_text(value: str, *, field: str, max_len: int = 500, required: bool = True) -> str:
    """NFC-normalise, drop control and format characters, trim. Reject, never truncate."""
    text = unicodedata.normalize("NFC", value)
    text = "".join(" " if ch in "\t\r\n" else ch for ch in text if ch in "\t\r\n" or unicodedata.category(ch) not in _DROP)
    text = " ".join(text.split())
    if required and not text:
        raise InvalidText(f"{field} must not be empty")
    if len(text) > max_len:
        raise InvalidText(f"{field} must be at most {max_len} characters")
    return text


def clean_filename(name: str | None) -> str:
    """Display name for an uploaded file. Never used as a storage path (section 4.4)."""
    base = (name or "").replace("\\", "/").rsplit("/", 1)[-1]
    try:
        cleaned = clean_text(base, field="file name", max_len=10_000, required=False)
    except InvalidText:
        cleaned = ""
    cleaned = cleaned.strip(". ")
    if len(cleaned) > 255:
        stem, dot, ext = cleaned.rpartition(".")
        cleaned = (stem[: 255 - len(ext) - 1] + "." + ext) if dot and len(ext) <= 10 else cleaned[:255]
    return cleaned or "upload"
