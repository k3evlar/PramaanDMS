from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_v2"
LABELS = DATASET / "labels.csv"
SPLITS_CSV = DATASET / "splits.csv"
MANIFEST = DATASET / "split_manifest.json"


def allocate_type(ids: list[str], rng: random.Random) -> dict[str, str]:
    """Assign one doc type's base IDs to approximate 70/15/15 splits."""
    ids = ids[:]
    rng.shuffle(ids)
    n = len(ids)
    if n < 3:
        raise ValueError(
            f"Need at least 3 base documents per document type to put that type "
            f"in train, validation, and test; found {n}."
        )

    # Start with a non-empty assignment to each split.
    n_train = max(1, int(n * 0.70))
    n_val = max(1, int(n * 0.15))
    n_test = n - n_train - n_val

    # Correct rounding while preserving at least one item in each split.
    while n_test < 1:
        if n_train > 1 and (n_train / n) > 0.70:
            n_train -= 1
        elif n_val > 1:
            n_val -= 1
        else:
            n_train -= 1
        n_test = n - n_train - n_val

    # For common cases (e.g. 12 docs), floor-based counts are close enough.
    assigned = {}
    for base_id in ids[:n_train]:
        assigned[base_id] = "train"
    for base_id in ids[n_train:n_train + n_val]:
        assigned[base_id] = "validation"
    for base_id in ids[n_train + n_val:]:
        assigned[base_id] = "test"
    return assigned


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create train/validation/test splits stratified by document type and grouped by base ID."
    )
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--force", action="store_true",
                        help="Replace existing split assignments.")
    args = parser.parse_args()

    if not LABELS.exists():
        raise SystemExit(f"Missing labels file: {LABELS}")
    if SPLITS_CSV.exists() and not args.force:
        raise SystemExit(
            f"{SPLITS_CSV} already exists. Use --force to intentionally replace it."
        )

    with LABELS.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if not rows:
        raise SystemExit("labels.csv contains no data rows.")

    base_types: dict[str, str] = {}
    for row in rows:
        base_id = row.get("original_id", "")
        doc_type = row.get("doc_type", "")
        if not base_id or not doc_type:
            raise SystemExit("A row is missing original_id or doc_type.")
        if base_id in base_types and base_types[base_id] != doc_type:
            raise SystemExit(f"Inconsistent doc_type for {base_id}.")
        base_types[base_id] = doc_type

    ids_by_type: dict[str, list[str]] = defaultdict(list)
    for base_id, doc_type in base_types.items():
        ids_by_type[doc_type].append(base_id)

    rng = random.Random(args.seed)
    assignment: dict[str, str] = {}
    for doc_type in sorted(ids_by_type):
        ids = ids_by_type[doc_type]
        try:
            assignment.update(allocate_type(ids, rng))
        except ValueError as exc:
            raise SystemExit(f"Cannot create stratified split for {doc_type}: {exc}")

    if "split" not in fieldnames:
        fieldnames.append("split")
    for row in rows:
        row["split"] = assignment[row["original_id"]]

    with LABELS.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with SPLITS_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["original_id", "doc_type", "split"])
        writer.writeheader()
        for base_id in sorted(assignment):
            writer.writerow({
                "original_id": base_id,
                "doc_type": base_types[base_id],
                "split": assignment[base_id],
            })

    base_counts = Counter(assignment.values())
    sample_counts = Counter(row["split"] for row in rows)
    by_type = {
        doc_type: dict(Counter(assignment[base_id] for base_id in ids))
        for doc_type, ids in sorted(ids_by_type.items())
    }
    manifest = {
        "dataset_name": "PramaanDMS synthetic English dataset V2",
        "seed": args.seed,
        "split_unit": "original_id (base document)",
        "strategy": "stratified by doc_type; all variants grouped by original_id",
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
        "base_document_counts_by_doc_type": by_type,
        "note": (
            "Approximate 70/15/15 proportions are applied within each document type. "
            "Small per-type counts cause rounding deviations. All variants of each original_id "
            "are assigned to the same split. This is not stratified by tamper class because each "
            "base document has variants across the tamper classes."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    split_sets = defaultdict(set)
    for row in rows:
        split_sets[row["original_id"]].add(row["split"])
    leakage = [base for base, values in split_sets.items() if len(values) != 1]
    if leakage:
        raise SystemExit("Split leakage detected: " + ", ".join(leakage[:10]))

    print("=== Stratified dataset split complete ===")
    print("Base documents:", len(base_types))
    print("Base-document split counts:", dict(base_counts))
    print("Sample-row counts:", dict(sample_counts))
    print("Base documents by type and split:")
    for doc_type, counts in by_type.items():
        print(f"  {doc_type}: {counts}")
    print("Updated:", LABELS)
    print("Split mapping:", SPLITS_CSV)
    print("Split manifest:", MANIFEST)
    print("PASS: every document type appears in train, validation, and test; all variants remain grouped.")
    print("Run scripts/final_dataset_audit.py afterward.")
    print("Note: E0 counts include both each original base PDF and its separate E0 control copy.")


if __name__ == "__main__":
    main()
