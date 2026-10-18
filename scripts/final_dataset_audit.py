from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_v2"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    labels_path = DATASET / "labels.csv"
    splits_path = DATASET / "splits.csv"
    manifest_path = DATASET / "split_manifest.json"
    capture_log_path = DATASET / "annotations" / "capture_variants.csv"
    change_log_path = DATASET / "annotations" / "change_log.csv"

    errors = []
    warnings = []

    try:
        labels = read_csv(labels_path)
        split_rows = read_csv(splits_path)
        capture_log = read_csv(capture_log_path)
        change_log = read_csv(change_log_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read required dataset files: {exc}")

    required_label_cols = {
        "sample_id", "doc_type", "original_id", "tamper_class", "field_changed",
        "page_affected", "severity", "expected_verdict", "capture_type", "file_path", "split"
    }
    if labels and not required_label_cols.issubset(labels[0]):
        errors.append("labels.csv is missing columns: " + ", ".join(sorted(required_label_cols - set(labels[0]))))

    sample_ids = [r.get("sample_id", "") for r in labels]
    duplicate_ids = [sid for sid, count in Counter(sample_ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Duplicate sample IDs: {duplicate_ids[:10]}")

    for row in labels:
        sid = row.get("sample_id", "<unknown>")
        if not (ROOT / row.get("file_path", "")).is_file():
            errors.append(f"{sid}: missing file {row.get('file_path', '')}")
        if row.get("split") not in {"train", "validation", "test"}:
            errors.append(f"{sid}: invalid or missing split {row.get('split')!r}")

    captures = Counter(r.get("capture_type", "") for r in labels)
    classes_digital = Counter(r.get("tamper_class", "") for r in labels if r.get("capture_type") == "digital")
    splits_samples = Counter(r.get("split", "") for r in labels)

    # Verify one split per original_id.
    base_splits = defaultdict(set)
    base_types = defaultdict(set)
    for row in labels:
        base_splits[row.get("original_id", "")].add(row.get("split", ""))
        base_types[row.get("original_id", "")].add(row.get("doc_type", ""))
    leaking = [base for base, splits in base_splits.items() if len(splits) != 1]
    if leaking:
        errors.append(f"Split leakage: {leaking[:10]}")

    inconsistent_types = [base for base, types in base_types.items() if len(types) != 1]
    if inconsistent_types:
        errors.append(f"Inconsistent doc_type within base variants: {inconsistent_types[:10]}")

    split_mapping = {r.get("original_id"): r.get("split") for r in split_rows}
    for base, splits in base_splits.items():
        if len(splits) == 1 and split_mapping.get(base) not in splits:
            errors.append(f"splits.csv disagrees with labels.csv for {base}")

    expected_captures = {"digital": 850, "print_scan": 850, "phone_photo": 850}
    if len(labels) == 2550 and dict(captures) != expected_captures:
        warnings.append(f"Capture counts differ from expected {expected_captures}: {dict(captures)}")

    expected_classes = {f"E{i}" for i in range(16)}
    missing_classes = sorted(expected_classes - set(classes_digital))
    if missing_classes:
        errors.append("Missing digital classes: " + ", ".join(missing_classes))
    for cls in sorted(expected_classes):
        if classes_digital.get(cls, 0) != 50:
            warnings.append(f"Digital class {cls} has {classes_digital.get(cls, 0)} rows; expected 50 for 50 bases.")

    # Check capture log row coverage against non-digital label rows.
    non_digital_ids = {r.get("sample_id") for r in labels if r.get("capture_type") != "digital"}
    capture_log_ids = {r.get("sample_id") for r in capture_log}
    if non_digital_ids != capture_log_ids:
        errors.append(
            f"Capture log coverage mismatch: {len(non_digital_ids)} non-digital label rows vs "
            f"{len(capture_log_ids)} capture log rows."
        )

    # The change log is for semantic/digital samples; ensure each digital sample has an annotation.
    digital_ids = {r.get("sample_id") for r in labels if r.get("capture_type") == "digital"}
    change_ids = {r.get("sample_id") for r in change_log}
    if digital_ids != change_ids:
        errors.append(
            f"Change log coverage mismatch: {len(digital_ids)} digital label rows vs "
            f"{len(change_ids)} change log rows."
        )

    # Report split distribution by base document type; this is a warning if a split lacks a type.
    split_type_counts = defaultdict(Counter)
    for base, splits in base_splits.items():
        if len(splits) == 1:
            split = next(iter(splits))
            doc_type = next(iter(base_types[base])) if base_types[base] else "unknown"
            split_type_counts[split][doc_type] += 1
    all_types = {next(iter(v)) for v in base_types.values() if v}
    for split in ("train", "validation", "test"):
        absent = sorted(all_types - set(split_type_counts[split]))
        if absent:
            warnings.append(f"{split} split has no base document of type(s): {', '.join(absent)}")

    print("=== PramaanDMS final structural audit ===")
    print("Label rows:", len(labels))
    print("Unique base documents:", len(base_splits))
    print("Capture counts:", dict(captures))
    print("Digital class counts:", dict(sorted(classes_digital.items())))
    print("Sample rows by split:", dict(splits_samples))
    print("Base documents by split:", dict(Counter(next(iter(s)) for s in base_splits.values() if len(s) == 1)))
    print("Capture log rows:", len(capture_log))
    print("Change log rows:", len(change_log))
    print("Manifest base-document counts:", manifest.get("base_document_counts", {}))
    print("Errors:", len(errors))
    print("Warnings:", len(warnings))
    for msg in errors[:100]:
        print("ERROR:", msg)
    for msg in warnings[:100]:
        print("WARNING:", msg)
    if errors:
        print("RESULT: FAIL — fix errors before calling the dataset structurally complete.")
        raise SystemExit(1)
    print("RESULT: PASS — structural consistency checks passed.")
    print("Human review is still required for semantic correctness, capture legibility, and the required independent 10% review.")


if __name__ == "__main__":
    main()
