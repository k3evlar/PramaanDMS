from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_v2"
LABELS = DATASET / "labels.csv"
EXPECTED_CLASSES = {f"E{i}" for i in range(16)}
FIELD_CLASS_RULES = {
    "E1": {"accused_name"},
    "E2": {"incident_date"},
    "E3": {"incident_time"},
    "E4": {"monetary_amount"},
    "E5": {"act_name", "section_number"},
    "E6": {"offence_description"},
    "E7": {"complainant_name", "accused_name"},
    "E8": {"incident_location"},
    "E9": {"evidence_item_id"},
    "E10": {"evidence_description"},
    "E11": {"evidence_description"},
    "E12": {"offence_description"},
    "E13": {"custody_holder"},
    "E14": {"filing_date", "document_date"},
    "E15": {"signature_seal_region"},
}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def source_sample_id(sample_id: str) -> str:
    for suffix in ("-PRINT_SCAN", "-PHONE_PHOTO"):
        if sample_id.endswith(suffix):
            return sample_id[:-len(suffix)]
    return sample_id


def json_path_for_digital_row(row: dict) -> Path | None:
    sample_id = row["sample_id"]
    original_id = row["original_id"]
    cls = row["tamper_class"]
    if sample_id == original_id:
        path = DATASET / "base_docs" / f"{original_id}.json"
    elif cls == "E0" and sample_id.endswith("-E0"):
        path = DATASET / "tampered" / "E0" / f"{sample_id}.json"
    else:
        path = DATASET / "tampered" / cls / f"{sample_id}.json"
    return path if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dataset_v2 labels, paths, and structured tampering.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with error status if any validation issue is found.")
    args = parser.parse_args()

    if not LABELS.exists():
        raise SystemExit(f"Missing labels file: {LABELS}")

    with LABELS.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    issues: list[str] = []
    warnings: list[str] = []
    counts = Counter(row.get("tamper_class", "") for row in rows)
    capture_counts = Counter(row.get("capture_type", "") for row in rows)
    seen = set()
    originals = {row["original_id"] for row in rows}
    rows_by_id = {row["sample_id"]: row for row in rows}

    for row in rows:
        sid = row.get("sample_id", "")
        if not sid:
            issues.append("Found a row with an empty sample_id.")
            continue
        if sid in seen:
            issues.append(f"Duplicate sample_id: {sid}")
        seen.add(sid)

        file_path = ROOT / row.get("file_path", "")
        if not file_path.exists():
            issues.append(f"{sid}: missing file {row.get('file_path', '')}")

        if row.get("capture_type") not in {"digital", "print_scan", "phone_photo"}:
            issues.append(f"{sid}: unknown capture_type {row.get('capture_type')}")

        if row.get("capture_type") != "digital":
            source_id = source_sample_id(sid)
            source_row = rows_by_id.get(source_id)
            if source_row is None:
                issues.append(f"{sid}: cannot find digital source row {source_id}")
            else:
                for field in ("original_id", "tamper_class", "field_changed", "expected_verdict"):
                    if row.get(field) != source_row.get(field):
                        issues.append(f"{sid}: capture label mismatch in {field}")

    digital_rows = [r for r in rows if r.get("capture_type") == "digital"]
    classes_found = {r.get("tamper_class") for r in digital_rows}
    missing_classes = sorted(EXPECTED_CLASSES - classes_found)
    if missing_classes:
        issues.append("Missing digital tamper classes: " + ", ".join(missing_classes))

    # Check every digital record against its original structured JSON.
    for row in digital_rows:
        sid, cls, original_id = row["sample_id"], row["tamper_class"], row["original_id"]
        actual_json_path = json_path_for_digital_row(row)
        original_json_path = DATASET / "base_docs" / f"{original_id}.json"
        if actual_json_path is None:
            issues.append(f"{sid}: missing structured JSON sidecar")
            continue
        if not original_json_path.exists():
            issues.append(f"{sid}: missing original JSON {original_json_path}")
            continue
        try:
            actual = read_json(actual_json_path)
            original = read_json(original_json_path)
        except Exception as exc:
            issues.append(f"{sid}: JSON read error: {exc}")
            continue

        if cls == "E0":
            if actual != original:
                issues.append(f"{sid}: E0 structured record differs from original")
        elif cls == "E15":
            # E15 is intentionally visual-only; structured data should remain identical.
            if actual != original:
                issues.append(f"{sid}: E15 should not change structured fields")
        elif cls in FIELD_CLASS_RULES:
            changed = {key for key in original if original.get(key) != actual.get(key)}
            expected = FIELD_CLASS_RULES[cls]
            if changed != expected:
                issues.append(
                    f"{sid}: class {cls} changed fields {sorted(changed)}, expected {sorted(expected)}"
                )
            if row.get("field_changed") != ";".join(sorted(expected)) and len(expected) > 1:
                # Field order in labels is human-authored; only warn for order/representation mismatches.
                listed = {v.strip() for v in row.get("field_changed", "").split(";") if v.strip()}
                if listed != expected:
                    issues.append(f"{sid}: field_changed label {row.get('field_changed')!r} does not match {sorted(expected)}")
            elif len(expected) == 1 and row.get("field_changed") not in expected:
                issues.append(f"{sid}: field_changed label does not match class {cls}")

        if cls != "E0" and row.get("expected_verdict") != "Tampered":
            issues.append(f"{sid}: tampered class {cls} should have expected_verdict=Tampered")

    print("=== PramaanDMS dataset validation ===")
    print("Total rows:", len(rows))
    print("Unique original/base IDs:", len(originals))
    print("Capture types:", dict(capture_counts))
    print("Digital class counts:", dict(sorted(Counter(r["tamper_class"] for r in digital_rows).items())))
    print("Digital samples:", len(digital_rows))
    print("Validation issues:", len(issues))
    print("Warnings:", len(warnings))
    for issue in issues[:100]:
        print("ERROR:", issue)
    if len(issues) > 100:
        print(f"... plus {len(issues) - 100} additional issues")
    if not issues:
        print("PASS: file paths, capture labels, class coverage, and structured field-change rules passed.")
    else:
        print("NOT READY: fix validation issues before scaling or creating final splits.")
    if args.strict and issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
