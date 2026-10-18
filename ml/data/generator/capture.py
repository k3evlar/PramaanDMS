"""Simulated capture variants: blur, scan and phone photo.

These are image-processing simulations, labelled scan_sim and photo_sim. They are
not real prints or photos. Real captures are planned for Phase 10 (BUILD_PLAN.md)
and are for testing only.

Every operation is seeded, so the same seed gives the same images.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

cv2.setNumThreads(1)

DPI = 200
PT_TO_PX = DPI / 72.0


def seed_for(*parts: str) -> int:
    return int.from_bytes(hashlib.sha256("|".join(parts).encode()).digest()[:8], "big")


def rasterize(pdf_path: Path, dpi: int = DPI) -> list[np.ndarray]:
    """Render each PDF page to an RGB array."""
    doc = pdfium.PdfDocument(str(pdf_path))
    out = []
    try:
        for i in range(len(doc)):
            img = doc[i].render(scale=dpi / 72.0).to_pil().convert("RGB")
            out.append(np.asarray(img).copy())
    finally:
        doc.close()
    return out


def blur_boxes(pages: list[np.ndarray], boxes: list[list[float]]) -> list[np.ndarray]:
    """Blur each box ([page, x0, y0, x1, y1] in points, page 1-based) until it cannot be read."""
    out = [p.copy() for p in pages]
    for page, x0, y0, x1, y1 in boxes:
        img = out[int(page) - 1]
        pad = 3 * PT_TO_PX
        a, b = int(max(0, x0 * PT_TO_PX - pad)), int(min(img.shape[1], x1 * PT_TO_PX + pad))
        c, d = int(max(0, y0 * PT_TO_PX - pad)), int(min(img.shape[0], y1 * PT_TO_PX + pad))
        region = img[c:d, a:b]
        sigma = max(6.0, (d - c) * 0.45)
        img[c:d, a:b] = cv2.GaussianBlur(region, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return out


def scan_sim(page: np.ndarray, seed: int) -> np.ndarray:
    """Flatbed scan: grey, slightly rotated, a little blur, noise and contrast change."""
    rng = np.random.default_rng(seed)
    g = cv2.cvtColor(page, cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = g.shape
    ang = rng.uniform(-1.2, 1.2)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    m[:, 2] += rng.uniform(-8, 8, size=2)
    g = cv2.warpAffine(g, m, (w, h), flags=cv2.INTER_LINEAR, borderValue=255)
    g = cv2.GaussianBlur(g, (0, 0), sigmaX=rng.uniform(0.4, 0.9))
    contrast, bright = rng.uniform(0.9, 1.12), rng.uniform(-12, 6)
    g = (g - 128) * contrast + 128 + bright
    g += rng.normal(0, rng.uniform(2, 6), size=g.shape)
    for _ in range(int(rng.integers(5, 40))):  # dust specks
        cv2.circle(g, (int(rng.integers(0, w)), int(rng.integers(0, h))), int(rng.integers(1, 3)),
                   float(rng.uniform(40, 120)), -1)
    return np.clip(g, 0, 255).astype(np.uint8)


def photo_sim(page: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Phone photo: page on a desk, perspective, uneven light, blur, noise, colour cast.

    Returns the photo and the 3x3 matrix that maps page pixels (at DPI) to photo pixels.
    """
    rng = np.random.default_rng(seed)
    h, w = page.shape[:2]
    cw, ch = int(w * 1.16), int(h * 1.10)
    desk = np.array([rng.uniform(90, 170), rng.uniform(80, 150), rng.uniform(60, 130)], dtype=np.float32)
    bg = np.ones((ch, cw, 3), np.float32) * desk
    noise = cv2.resize(rng.normal(0, 14, size=(ch // 40 + 1, cw // 40 + 1)).astype(np.float32), (cw, ch))
    bg += noise[..., None]
    ox, oy = (cw - w) / 2, (ch - h) / 2
    j = 0.035
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[ox + rng.uniform(-j, j) * w, oy + rng.uniform(-j, j) * h],
                      [ox + w + rng.uniform(-j, j) * w, oy + rng.uniform(-j, j) * h],
                      [ox + w + rng.uniform(-j, j) * w, oy + h + rng.uniform(-j, j) * h],
                      [ox + rng.uniform(-j, j) * w, oy + h + rng.uniform(-j, j) * h]])
    # Small overall rotation about the centre.
    ang = np.deg2rad(rng.uniform(-4, 4))
    cx, cy = cw / 2, ch / 2
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], np.float32)
    dst = ((dst - [cx, cy]) @ rot.T + [cx, cy]).astype(np.float32)
    hm = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(page.astype(np.float32), hm, (cw, ch), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.ones((h, w), np.float32), hm, (cw, ch), flags=cv2.INTER_LINEAR)[..., None]
    img = warped * mask + bg * (1 - mask)
    # Uneven light: a linear gradient plus a soft vignette.
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    gx, gy = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)
    light = 1.0 + gx * (xx / cw - 0.5) + gy * (yy / ch - 0.5)
    r2 = ((xx - cx) / cw) ** 2 + ((yy - cy) / ch) ** 2
    light *= 1.0 - rng.uniform(0.15, 0.35) * r2 * 2
    light *= rng.uniform(0.78, 1.0)
    img *= light[..., None]
    img *= np.array([rng.uniform(0.95, 1.05), rng.uniform(0.95, 1.03), rng.uniform(0.88, 1.0)], np.float32)
    if rng.random() < 0.5:
        k = int(rng.integers(3, 7))
        kernel = np.zeros((k, k), np.float32)
        kernel[k // 2, :] = 1.0 / k
        rm = cv2.getRotationMatrix2D((k / 2 - 0.5, k / 2 - 0.5), float(rng.uniform(0, 180)), 1.0)
        kernel = cv2.warpAffine(kernel, rm, (k, k))
        kernel /= max(kernel.sum(), 1e-6)
        img = cv2.filter2D(img, -1, kernel)
    else:
        img = cv2.GaussianBlur(img, (0, 0), sigmaX=rng.uniform(0.6, 1.3))
    img += rng.normal(0, rng.uniform(2, 6), size=img.shape)
    return np.clip(img, 0, 255).astype(np.uint8), hm


def save_pdf(pages: list[np.ndarray], path: Path, quality: int) -> None:
    """Save page images as an image-only A4 PDF (JPEG inside).

    Written with ReportLab in invariant mode, because Pillow's PDF writer stamps the
    current time into the file and breaks byte-identical rebuilds.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    for p in pages:
        buf = io.BytesIO()
        Image.fromarray(p).save(buf, "JPEG", quality=quality, optimize=False)
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=A4[0], height=A4[1])
        c.showPage()
    c.save()


def save_jpeg(img: np.ndarray, path: Path, quality: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(str(path), "JPEG", quality=quality, optimize=False)


def make_captures(job: dict) -> dict:
    """Make the digital-blur, scan_sim and photo_sim files for one version.

    Runs in a worker process. `job` holds paths, blur boxes and the version id.
    """
    vid = job["version_id"]
    pages = rasterize(Path(job["pdf"]))
    if job["blur_boxes"]:
        pages = blur_boxes(pages, job["blur_boxes"])
        save_pdf(pages, Path(job["digital_out"]), quality=95)
    result: dict = {"version_id": vid, "photo_files": [], "photo_matrices": []}
    rng = np.random.default_rng(seed_for(job["seed"], vid, "scan"))
    scans = [scan_sim(p, seed_for(job["seed"], vid, "scan", str(i))) for i, p in enumerate(pages)]
    save_pdf(scans, Path(job["scan_out"]), quality=int(rng.integers(72, 88)))
    for i, p in enumerate(pages):
        s = seed_for(job["seed"], vid, "photo", str(i))
        img, hm = photo_sim(p, s)
        out = Path(job["photo_dir"]) / f"{vid}_p{i + 1}.jpg"
        save_jpeg(img, out, quality=int(np.random.default_rng(s).integers(74, 90)))
        result["photo_files"].append(out.name)
        result["photo_matrices"].append([[round(float(x), 6) for x in row] for row in hm])
    return result
