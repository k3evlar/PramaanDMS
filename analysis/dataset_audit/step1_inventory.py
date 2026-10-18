"""Step 1: inventory, orphan files, missing files, corrupt or unreadable files."""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from PIL import Image

from audit_lib import (DATASET, ROOT, abs_path, label_rows, labels, load_json, pdf_text,
                       read_csv, sha256, write_json)


def tree(max_depth: int = 3) -> list[str]:
    lines = []
    for path in sorted(DATASET.rglob("*")):
        if not path.is_dir():
            continue
        rel = path.relative_to(DATASET)
        if len(rel.parts) > max_depth:
            continue
        files = [p for p in path.iterdir() if p.is_file()]
        lines.append(f"{'  ' * (len(rel.parts) - 1)}{rel.name}/  ({len(files)} files)")
    return lines


def main() -> dict:
    files = [p for p in DATASET.rglob("*") if p.is_file()]
    by_ext = Counter(p.suffix.lower() or "<none>" for p in files)
    size_by_ext: dict[str, int] = defaultdict(int)
    for p in files:
        size_by_ext[p.suffix.lower()] += p.stat().st_size
    total = sum(size_by_ext.values())

    header, rows = labels()
    label_paths = {r["file_path"] for r in rows}
    on_disk_data = {p.relative_to(ROOT).as_posix() for p in files
                    if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}}
    orphans = sorted(on_disk_data - label_paths)
    missing = sorted(r["sample_id"] for r in rows if not abs_path(r["file_path"]).is_file())

    # JSON sidecars: every digital PDF needs one, every JSON needs a PDF.
    pdfs = {p.with_suffix("") for p in files if p.suffix.lower() == ".pdf"}
    jsons = {p.with_suffix("") for p in files if p.suffix.lower() == ".json"
             and p.parent != DATASET}
    pdf_without_json = sorted(str(p.relative_to(ROOT)) for p in pdfs - jsons)
    json_without_pdf = sorted(str(p.relative_to(ROOT)) for p in jsons - pdfs)

    corrupt: list[dict] = []
    page_counts: Counter = Counter()
    empty_text: list[str] = []
    for p in sorted(files):
        rel = p.relative_to(ROOT).as_posix()
        ext = p.suffix.lower()
        try:
            if p.stat().st_size == 0:
                raise ValueError("zero-byte file")
            if ext == ".pdf":
                import pypdfium2 as pdfium
                doc = pdfium.PdfDocument(str(p))
                n = len(doc)
                doc.close()
                page_counts[n] += 1
                if n == 0:
                    raise ValueError("PDF has no pages")
                if len(pdf_text(p).strip()) < 50:
                    empty_text.append(rel)
            elif ext in {".jpg", ".jpeg", ".png"}:
                with Image.open(p) as im:
                    im.verify()
                with Image.open(p) as im:
                    im.load()
            elif ext == ".json":
                obj = load_json(p)
                if not obj:
                    raise ValueError("empty JSON")
            elif ext == ".csv":
                read_csv(p)
        except Exception as exc:  # noqa: BLE001 - any failure is a finding
            corrupt.append({"file": rel, "error": f"{type(exc).__name__}: {exc}"})

    # Annotation files and manifests, cross-checked for row coverage.
    _, change_log = read_csv(DATASET / "annotations" / "change_log.csv")
    _, capture_log = read_csv(DATASET / "annotations" / "capture_variants.csv")
    _, splits = read_csv(DATASET / "splits.csv")
    review_files = sorted(p.name for p in (DATASET / "annotations").iterdir())
    manifest = json.loads((DATASET / "dataset_manifest.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((DATASET / "split_manifest.json").read_text(encoding="utf-8"))

    digital_ids = {r["sample_id"] for r in rows if r["capture_type"] == "digital"}
    capture_ids = {r["sample_id"] for r in rows if r["capture_type"] != "digital"}
    result = {
        "dataset_dir": str(DATASET.relative_to(ROOT)),
        "tree": tree(),
        "file_count": len(files),
        "files_by_extension": dict(sorted(by_ext.items())),
        "bytes_by_extension": dict(sorted(size_by_ext.items())),
        "total_bytes": total,
        "total_mb": round(total / 1e6, 1),
        "labels_csv": {
            "path": "dataset_v2/labels.csv", "format": "CSV, UTF-8 with BOM",
            "columns": header, "row_count": len(rows),
            "sha256": sha256(DATASET / "labels.csv"),
        },
        "other_label_files": {
            "annotations/change_log.csv": len(change_log),
            "annotations/capture_variants.csv": len(capture_log),
            "splits.csv": len(splits),
        },
        "annotation_dir_files": review_files,
        "independent_review_done": (DATASET / "annotations" / "independent_review.csv").exists(),
        "dataset_manifest": manifest,
        "split_manifest_base_counts": split_manifest.get("base_document_counts"),
        "files_without_label_row": orphans,
        "label_rows_without_file": missing,
        "pdf_without_json_sidecar": pdf_without_json,
        "json_without_pdf": json_without_pdf,
        "corrupt_or_unreadable": corrupt,
        "pdf_page_counts": {str(k): v for k, v in page_counts.items()},
        "pdfs_with_empty_text_layer": empty_text,
        "change_log_vs_digital_rows": {
            "missing_in_change_log": sorted(digital_ids - {r["sample_id"] for r in change_log}),
            "extra_in_change_log": sorted({r["sample_id"] for r in change_log} - digital_ids),
        },
        "capture_log_vs_capture_rows": {
            "missing_in_capture_log": sorted(capture_ids - {r["sample_id"] for r in capture_log}),
            "extra_in_capture_log": sorted({r["sample_id"] for r in capture_log} - capture_ids),
        },
        "stale_dataset_manifest": (
            manifest.get("capture_types") == ["digital"]
            and any(r["capture_type"] != "digital" for r in rows)
        ),
    }
    write_json("step1_inventory.json", result)
    print(f"files={len(files)} total={result['total_mb']} MB rows={len(rows)} "
          f"orphans={len(orphans)} missing={len(missing)} corrupt={len(corrupt)}")
    return result


if __name__ == "__main__":
    main()
