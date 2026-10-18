"""Upload type and limit checks: each rule has an accepted case and a refused case."""

from __future__ import annotations

import io

import pytest

from app.evidence.filetypes import JPEG, PDF, PNG, TIFF, Limits, RejectedFile, inspect, sniff
from app.validation import InvalidText, clean_filename, clean_text

from . import samples

LIMITS = Limits(max_bytes=2 * 1024 * 1024, max_pages=3, max_pixels=1_000_000)


def check(data: bytes, name: str, limits: Limits = LIMITS):  # type: ignore[no-untyped-def]
    return inspect(io.BytesIO(data), len(data), name, limits)


def refused(data: bytes, name: str, limits: Limits = LIMITS) -> RejectedFile:
    with pytest.raises(RejectedFile) as e:
        check(data, name, limits)
    return e.value


@pytest.mark.parametrize("data, name, media, pages", [
    (samples.pdf(2), "fir.pdf", PDF, 2),
    (samples.png(), "scan.png", PNG, 1),
    (samples.jpeg(), "photo.JPG", JPEG, 1),
    (samples.jpeg(), "photo.jpeg", JPEG, 1),
    (samples.tiff(frames=3), "scan.tif", TIFF, 3),
    (samples.tiff(), "scan.tiff", TIFF, 1),
], ids=["pdf", "png", "jpg", "jpeg", "tif-3", "tiff"])
def test_valid_files_are_accepted_with_page_count(data: bytes, name: str, media: str, pages: int) -> None:
    info = check(data, name)
    assert (info.media_type, info.page_count) == (media, pages)


@pytest.mark.parametrize("data", [
    b"PK\x03\x04" + b"\x00" * 64,                    # zip archive (section 4.4: archives refused)
    b"<html><script>alert(1)</script></html>",       # HTML named as a PDF
    b"plain text that claims to be a pdf",
    b"GIF89a" + b"\x00" * 32,                         # real image type, but not on the list
    b"II+\x00" + b"\x00" * 32,                        # BigTIFF
], ids=["zip", "html", "text", "gif", "bigtiff"])
def test_wrong_type_is_refused_by_content_not_name(data: bytes) -> None:
    e = refused(data, "evidence.pdf")
    assert (e.code, e.status) == ("unsupported_type", 415)


def test_client_name_cannot_make_a_wrong_type_pass() -> None:
    # A PNG called .pdf is refused, and a PDF called .png too: the extension must match the bytes.
    assert refused(samples.png(), "fir.pdf").code == "extension_mismatch"
    assert refused(samples.pdf(), "fir.png").code == "extension_mismatch"
    assert refused(samples.pdf(), "fir").code == "extension_mismatch"


def test_size_limit() -> None:
    assert check(samples.pdf(), "ok.pdf").page_count == 1
    big = samples.pdf() + b"\x00" * (LIMITS.max_bytes + 1)
    e = refused(big, "big.pdf")
    assert (e.code, e.status) == ("too_large", 413)
    assert refused(b"", "empty.pdf").code == "empty"


def test_page_limit_for_pdf_and_tiff() -> None:
    assert check(samples.pdf(3), "three.pdf").page_count == 3
    assert refused(samples.pdf(4), "four.pdf").code == "too_many_pages"
    assert refused(samples.tiff(frames=4), "four.tif").code == "too_many_pages"


def test_pixel_limit_is_checked_before_decoding() -> None:
    assert check(samples.png(size=(1000, 1000)), "ok.png").page_count == 1
    # A plain image compresses to a few KB, so only the pixel check can catch it.
    data = samples.png(size=(1001, 1000))
    assert len(data) < 20_000
    assert refused(data, "wide.png").code == "image_too_large"
    assert refused(samples.tiff(size=(2000, 600), compression="tiff_lzw"), "wide.tif").code == "image_too_large"


@pytest.mark.parametrize("data, name", [
    (b"%PDF-1.7\n" + b"this is not a pdf body" * 10, "broken.pdf"),
    (samples.png()[:40], "cut.png"),
    (samples.jpeg()[:200], "cut.jpg"),
    (samples.tiff()[:30], "cut.tif"),
    (b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "fake.png"),
], ids=["pdf-body", "png-cut", "jpg-cut", "tif-cut", "png-header-only"])
@pytest.mark.filterwarnings("ignore:Corrupt EXIF data")
def test_malformed_files_are_refused_cleanly(data: bytes, name: str) -> None:
    assert refused(data, name).code == "malformed"


def test_animated_png_is_refused() -> None:
    assert refused(samples.animated_png(), "anim.png").code == "unsupported_type"


def test_sniff_needs_the_magic_at_offset_zero() -> None:
    assert sniff(b"%PDF-1.4") == PDF
    assert sniff(b" %PDF-1.4") is None
    assert sniff(b"MM\x00*rest") == TIFF


def test_clean_text_rules() -> None:
    assert clean_text("  Theft\u202e at\tstation\x00  ", field="title") == "Theft at station"
    with pytest.raises(InvalidText, match="must not be empty"):
        clean_text("\x00\u200b ", field="title")
    with pytest.raises(InvalidText, match="at most 5"):
        clean_text("abcdef", field="reason", max_len=5)


@pytest.mark.parametrize("raw, cleaned", [
    ("../../etc/passwd.pdf", "passwd.pdf"),
    ("C:\\Users\\io\\FIR 12.pdf", "FIR 12.pdf"),
    ("..", "upload"),
    (None, "upload"),
    ("bad\x00name\u202e.pdf", "badname.pdf"),
    ("a" * 300 + ".pdf", "a" * 251 + ".pdf"),
])
def test_clean_filename(raw: str | None, cleaned: str) -> None:
    assert clean_filename(raw) == cleaned
