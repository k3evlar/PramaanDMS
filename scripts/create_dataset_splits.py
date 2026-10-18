from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_v2"
LABELS = DATASET / "labels.csv"
SPLITS_CSV = DATASET / "splits.csv"
MANIFEST = DATASET / "split_manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create leakage-safe train/validation/test splits grouped by original base document."
    )
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--force", action="store_true",
                        help="Replace an existing split assignment.")
    args = parser.parse_args()

    if not LABELS.exists():
        raise SystemExit(f"Missing labels file: {LABELS}")

    if SPLITS_CSV.exists() and not args.force:
        raise SystemExit(
            f"{SPLITS_CSV} already exists. Nothing was changed. "
            "Use --force only if you intentionally want a new split assignment."
        )

    with LABELS.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        raise SystemExit("labels.csv contains no data rows.")
    required = {"sample_id", "original_id", "doc_type", "file_path"}
    if not required.issubset(fieldnames):
        raise SystemExit("labels.csv is missing required columns: " + ", ".join(sorted(required - set(fieldnames))))

    # Build one record per original/base ID. Every digital/capture variant inherits its base's split.
    base_doc_type = {}
    for row in rows:
        base_id = row["original_id"]
        if base_id in base_doc_type and base_doc_type[base_id] != row["doc_type"]:
            raise SystemExit(f"Inconsistent doc_type for original_id {base_id}")
        base_doc_type[base_id] = row["doc_type"]

    base_ids = sorted(base_doc_type)
    if len(base_ids) < 3:
        raise SystemExit("At least 3 base documents are required to create splits.")

    rng = random.Random(args.seed)
    rng.shuffle(base_ids)

    n = len(base_ids)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    n_test = n - n_train - n_val
    if n_train < 1 or n_val < 1 or n_test < 1:
        raise SystemExit("Not enough base documents for non-empty train/validation/test splits.")

    assignment = {}
    for base_id in base_ids[:n_train]:
        assignment[base_id] = "train"
    for base_id in base_ids[n_train:n_train + n_val]:
        assignment[base_id] = "validation"
    for base_id in base_ids[n_train + n_val:]:
        assignment[base_id] = "test"

    # Update every row so all variants of a base document remain in one split.
    if "split" not in fieldnames:
        fieldnames.append("split")
    for row in rows:
        row["split"] = assignment[row["original_id"]]

    with LABELS.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    split_rows = [
        {"original_id": base_id, "doc_type": base_doc_type[base_id], "split": assignment[base_id]}
        for base_id in sorted(assignment)
    ]
    with SPLITS_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["original_id", "doc_type", "split"])
        writer.writeheader()
        writer.writerows(split_rows)

    base_counts = Counter(assignment.values())
    sample_counts = Counter(row["split"] for row in rows)
    manifest = {
        "dataset_name": "PramaanDMS synthetic English dataset V2",
        "seed": args.seed,
        "split_unit": "original_id (base document)",
        "proportions_requested": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "base_document_counts": {
            "train": base_counts["train"],
            "validation": base_counts["validation"],
            "test": base_counts["test"],
        },
        "sample_row_counts_including_capture_variants": {
            "train": sample_counts["train"],
            "validation": sample_counts["validation"],
            "test": sample_counts["test"],
        },
        "note": (
            "All variants of each original_id are assigned to the same split. "
            "Base-document proportions are approximate because documents are indivisible. "
            "This is a seeded random split, not stratified by document type."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Internal consistency check: one split per original_id and all rows mapped.
    splits_by_base = {}
    for row in rows:
        splits_by_base.setdefault(row["original_id"], set()).add(row["split"])
    leaked = [base_id for base_id, values in splits_by_base.items() if len(values) != 1]
    if leaked:
        raise SystemExit("Split leakage detected for: " + ", ".join(leaked))

    print("=== Dataset split complete ===")
    print("Base documents:", n)
    print("Base-document split counts:", dict(base_counts))
    print("Sample-row counts (includes digital and capture variants):", dict(sample_counts))
    print("labels.csv updated with a split column.")
    print("Split mapping:", SPLITS_CSV)
    print("Split manifest:", MANIFEST)
    print("PASS: all variants of each original_id are assigned to exactly one split.")
    print("Note: split proportions apply to base documents, not to individual sample rows.")


if __name__ == "__main__":
    main()
