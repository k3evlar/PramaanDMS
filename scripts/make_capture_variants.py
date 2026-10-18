from __future__ import annotations

import argparse
import csv
import random
import shutil
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset_v2"
LABELS_PATH = DATASET_DIR / "labels.csv"
CAPTURE_DIR = DATASET_DIR / "captures"
SEED = 20261017


def render_first_page(pdf_path: Path, dpi: int = 160) -> Image.Image:
    """Render page 1 of a PDF. This pilot generator is designed for one-page PDFs."""
    with fitz.open(pdf_path) as doc:
        if len(doc) == 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")
        if len(doc) > 1:
            raise ValueError(
                f"Multi-page PDF found ({len(doc)} pages): {pdf_path}. "
                "This script intentionally stops rather than silently dropping pages."
            )
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def add_scan_effect(image: Image.Image, rng: random.Random) -> Image.Image:
    """Approximate a scanned print: grayscale, tiny rotation, and mild sensor/paper noise."""
    image = image.convert("L").convert("RGB")
    angle = rng.uniform(-1.0, 1.0)
    image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    arr = np.asarray(image).astype(np.int16)
    noise_rng = np.random.default_rng(rng.randint(0, 2**32 - 1))
    noise = noise_rng.normal(0, 2.0, arr.shape[:2]).astype(np.int16)
    arr = np.clip(arr + noise[:, :, None], 0, 255).astype(np.uint8)
    image = Image.fromarray(arr)
    image = ImageEnhance.Contrast(image).enhance(rng.uniform(0.92, 1.04))
    return image.filter(ImageFilter.GaussianBlur(radius=0.15))


def add_phone_photo_effect(image: Image.Image, rng: random.Random) -> Image.Image:
    """Approximate a phone photo with perspective, uneven light, and mild shadow."""
    rgb = np.asarray(image.convert("RGB"))
    h, w = rgb.shape[:2]

    # Keep the document fully in-frame while adding a modest perspective skew.
    margin_x = int(w * rng.uniform(0.015, 0.035))
    margin_y = int(h * rng.uniform(0.015, 0.035))
    src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    dst = np.float32([
        [margin_x, margin_y],
        [w - 1 - margin_x // 2, margin_y * 2],
        [w - 1 - margin_x, h - 1 - margin_y],
        [margin_x // 2, h - 1 - margin_y * 2],
    ])
    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(
        rgb, matrix, (w, h), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(232, 232, 232)
    )

    # Simulate gentle lighting variation and a soft edge shadow.
    y = np.linspace(0.96, 1.04, h, dtype=np.float32)[:, None]
    x = np.linspace(0.98, 1.02, w, dtype=np.float32)[None, :]
    illumination = y * x
    warped = np.clip(warped.astype(np.float32) * illumination[:, :, None], 0, 255)

    yy, xx = np.mgrid[0:h, 0:w]
    edge_distance = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]).astype(np.float32)
    shadow = np.clip(edge_distance / max(1, min(h, w) * 0.06), 0.82, 1.0)
    warped *= shadow[:, :, None]

    noise_rng = np.random.default_rng(rng.randint(0, 2**32 - 1))
    noise = noise_rng.normal(0, 1.4, warped.shape).astype(np.float32)
    warped = np.clip(warped + noise, 0, 255).astype(np.uint8)
    result = Image.fromarray(warped)
    result = ImageEnhance.Color(result).enhance(0.92)
    return result.filter(ImageFilter.GaussianBlur(radius=0.18))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create synthetic print-scan and phone-photo image variants for dataset_v2."
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--force", action="store_true",
        help="Replace existing captures and regenerate capture labels."
    )
    args = parser.parse_args()

    if not LABELS_PATH.exists():
        raise SystemExit(f"Cannot find {LABELS_PATH}. Run the V2 generator first.")

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    if any(CAPTURE_DIR.iterdir()) and not args.force:
        raise SystemExit(
            f"{CAPTURE_DIR} already contains files. Nothing was overwritten. "
            "Use --force only if you intend to regenerate captures."
        )

    with LABELS_PATH.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames:
        raise SystemExit("labels.csv has no header.")
    digital_rows = [row for row in rows if row.get("capture_type") == "digital"]
    if not digital_rows:
        raise SystemExit("No digital samples found in labels.csv.")

    # Remove prior capture rows when --force is explicitly used.
    kept_rows = [row for row in rows if row.get("capture_type") == "digital"]
    capture_rows = []
    rng = random.Random(args.seed)
    errors = []

    for row in digital_rows:
        pdf_path = ROOT / row["file_path"]
        if not pdf_path.exists():
            errors.append(f"Missing PDF: {pdf_path}")
            continue
        try:
            base_image = render_first_page(pdf_path)
            sample_id = row["sample_id"]
            for capture_type, effect_fn, folder in [
                ("print_scan", add_scan_effect, "print_scan"),
                ("phone_photo", add_phone_photo_effect, "phone_photo"),
            ]:
                output_path = CAPTURE_DIR / folder / f"{sample_id}.jpg"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                captured = effect_fn(base_image.copy(), rng)
                captured.save(output_path, "JPEG", quality=92, optimize=True)

                new_row = dict(row)
                new_row["sample_id"] = f"{sample_id}-{folder.upper()}"
                new_row["capture_type"] = capture_type
                new_row["file_path"] = output_path.relative_to(ROOT).as_posix()
                new_row["page_affected"] = row.get("page_affected", "1")
                capture_rows.append(new_row)
        except Exception as exc:
            errors.append(f"{row['sample_id']}: {exc}")

    if errors:
        print("Errors occurred; no labels.csv update was written.")
        for error in errors:
            print(" -", error)
        raise SystemExit(1)

    all_rows = kept_rows + capture_rows
    with LABELS_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    # Add a compact capture log; this does not replace the semantic change log.
    capture_log = DATASET_DIR / "annotations" / "capture_variants.csv"
    capture_log.parent.mkdir(parents=True, exist_ok=True)
    with capture_log.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=[
                "sample_id", "original_id", "source_sample_id", "capture_type",
                "file_path", "method", "review_status"
            ]
        )
        writer.writeheader()
        for new_row in capture_rows:
            source_id = new_row["sample_id"].removesuffix("-PRINT_SCAN").removesuffix("-PHONE_PHOTO")
            writer.writerow({
                "sample_id": new_row["sample_id"],
                "original_id": new_row["original_id"],
                "source_sample_id": source_id,
                "capture_type": new_row["capture_type"],
                "file_path": new_row["file_path"],
                "method": (
                    "Synthetic grayscale/rotation/noise simulation"
                    if new_row["capture_type"] == "print_scan"
                    else "Synthetic perspective/lighting/shadow simulation"
                ),
                "review_status": "needs_visual_review"
            })

    print(f"Digital samples retained: {len(kept_rows)}")
    print(f"Capture variants generated: {len(capture_rows)}")
    print(f"Total rows in labels.csv: {len(all_rows)}")
    print(f"Capture images: {CAPTURE_DIR}")
    print(f"Capture log: {capture_log}")
    print("Review the images for legibility and confirm no text or semantic content was lost.")
    print("These are simulated captures, not real scanner or phone-camera acquisitions.")


if __name__ == "__main__":
    main()
