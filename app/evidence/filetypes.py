"""File type and limit checks for uploads (REQUIREMENTS.md 4.1, 4.4 and NFR-06).

The type comes from the file's first bytes (magic bytes), never from the client's
Content-Type or the file name. The extension must then agree with the detected type.
Each file is also opened with a real parser (pdfium for PDF, Pillow for images), so a
file that only starts with the right bytes but is broken inside is rejected too.

Not checked here yet: the 200 MB decompressed-stream limit for PDFs and the virus scan
(ClamAV). Both are in Phase 22 (PROGRESS.md, Phase 5 known issues).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import BinaryIO

import pypdfium2 as pdfium
from PIL import Image, UnidentifiedImageError

PDF, PNG, JPEG, TIFF = "application/pdf", "image/png", "image/jpeg", "image/tiff"

# (media type, magic prefix). BigTIFF and other variants are not accepted.
MAGIC: tuple[tuple[str, bytes], ...] = (
    (PDF, b"%PDF-"),
    (PNG, b"\x89PNG\r\n\x1a\n"),
    (JPEG, b"\xff\xd8\xff"),
    (TIFF, b"II*\x00"),
    (TIFF, b"MM\x00*"),
)
EXTENSIONS: dict[str, tuple[str, ...]] = {
    PDF: (".pdf",), PNG: (".png",), JPEG: (".jpg", ".jpeg"), TIFF: (".tif", ".tiff"),
}
PIL_FORMAT = {PNG: "PNG", JPEG: "JPEG", TIFF: "TIFF"}

# pdfium is not thread-safe; FastAPI runs sync endpoints in a thread pool.
_PDFIUM_LOCK = threading.Lock()


@dataclass(frozen=True)
class Limits:
    max_bytes: int
    max_pages: int
    max_pixels: int


@dataclass(frozen=True)
class FileInfo:
    media_type: str
    page_count: int


class RejectedFile(Exception):
    """An upload broke a rule. `code` is stable for clients and logs; `message` is for people."""

    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def sniff(head: bytes) -> str | None:
    for media_type, magic in MAGIC:
        if head.startswith(magic):
            return media_type
    return None


def check_extension(media_type: str, filename: str) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in EXTENSIONS[media_type]:
        allowed = ", ".join(EXTENSIONS[media_type])
        raise RejectedFile("extension_mismatch",
                           f"The file content is {media_type} but the name does not end in {allowed}.")


def _pdf_pages(fp: BinaryIO) -> int:
    fp.seek(0)
    with _PDFIUM_LOCK:
        try:
            pdf = pdfium.PdfDocument(fp, autoclose=False)
        except pdfium.PdfiumError as e:
            if "password" in str(e).lower():
                raise RejectedFile("encrypted", "Password-protected PDFs are not accepted.") from None
            raise RejectedFile("malformed", "The PDF could not be read.") from None
        try:
            return len(pdf)
        finally:
            pdf.close()


def _image_pages(fp: BinaryIO, media_type: str, limits: Limits) -> int:
    fp.seek(0)
    try:
        with Image.open(fp) as img:
            if img.format != PIL_FORMAT[media_type]:
                raise RejectedFile("malformed", "The image could not be read.")
            frames = int(getattr(img, "n_frames", 1))
            if media_type == PNG and frames > 1:
                raise RejectedFile("unsupported_type", "Animated PNG files are not accepted.", 415)
            if frames > limits.max_pages:
                raise RejectedFile("too_many_pages", f"The file has more than {limits.max_pages} pages.")
            for i in range(frames):
                img.seek(i)
                w, h = img.size
                # Checked before decoding, so a small file cannot expand into a huge image.
                if w * h > limits.max_pixels:
                    raise RejectedFile("image_too_large",
                                       f"A page image is larger than {limits.max_pixels // 1_000_000} megapixels.")
                img.load()  # full decode: truncated or corrupt data fails here
            return frames
    except RejectedFile:
        raise
    except Image.DecompressionBombError:
        raise RejectedFile("image_too_large",
                           f"A page image is larger than {limits.max_pixels // 1_000_000} megapixels.") from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, EOFError):
        raise RejectedFile("malformed", "The image could not be read.") from None


def inspect(fp: BinaryIO, size: int, filename: str, limits: Limits) -> FileInfo:
    """Check a fully received upload. `fp` must be seekable and hold exactly `size` bytes."""
    if size == 0:
        raise RejectedFile("empty", "The file is empty.")
    if size > limits.max_bytes:
        raise RejectedFile("too_large", f"The file is larger than {limits.max_bytes // (1024 * 1024)} MB.", 413)
    fp.seek(0)
    media_type = sniff(fp.read(16))
    if media_type is None:
        raise RejectedFile("unsupported_type", "Only PDF, PNG, JPEG and TIFF files are accepted.", 415)
    check_extension(media_type, filename)
    pages = _pdf_pages(fp) if media_type == PDF else _image_pages(fp, media_type, limits)
    if pages < 1:
        raise RejectedFile("malformed", "The file has no pages.")
    if pages > limits.max_pages:
        raise RejectedFile("too_many_pages", f"The file has more than {limits.max_pages} pages.")
    fp.seek(0)
    return FileInfo(media_type=media_type, page_count=pages)
