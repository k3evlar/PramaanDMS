"""Small sample files built at test time (test fixtures, not dataset data).

They carry no personal data: blank pages and plain colour images only.
"""

from __future__ import annotations

import io

import pypdfium2 as pdfium
from PIL import Image


def pdf(pages: int = 1) -> bytes:
    doc = pdfium.PdfDocument.new()
    for _ in range(pages):
        doc.new_page(595, 842)  # A4 in points
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def image(fmt: str, size: tuple[int, int] = (64, 48), frames: int = 1, colour: str = "white",
          compression: str | None = None) -> bytes:
    buf = io.BytesIO()
    imgs = [Image.new("RGB", size, colour) for _ in range(frames)]
    extra = {"compression": compression} if compression else {}
    if frames > 1:
        imgs[0].save(buf, format=fmt, save_all=True, append_images=imgs[1:], **extra)
    else:
        imgs[0].save(buf, format=fmt, **extra)
    return buf.getvalue()


def png(**kw) -> bytes:  # type: ignore[no-untyped-def]
    return image("PNG", **kw)


def jpeg(**kw) -> bytes:  # type: ignore[no-untyped-def]
    return image("JPEG", **kw)


def tiff(**kw) -> bytes:  # type: ignore[no-untyped-def]
    return image("TIFF", **kw)


def animated_png() -> bytes:
    buf = io.BytesIO()
    a, b = Image.new("RGB", (8, 8), "white"), Image.new("RGB", (8, 8), "black")
    a.save(buf, format="PNG", save_all=True, append_images=[b])
    return buf.getvalue()
