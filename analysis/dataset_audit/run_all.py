"""Run the full dataset_v2 audit and write stats.json and issues.csv.

Usage (from analysis/dataset_audit):
    .venv/Scripts/python run_all.py            # all steps, OCR sample of 2 per class per capture
    .venv/Scripts/python run_all.py --skip-ocr # reuse outputs/step6_ocr.json (OCR takes ~10 min)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone

from audit_lib import AUDIT_DIR, read_out, sha256, DATASET, write_json

STEPS = ["step1_inventory.py", "step2_schema.py", "step3_coverage.py", "step4_splits.py",
         "step5_tamper.py", "step6_quality.py"]


def run(script: str, *args: str) -> None:
    print(f"== {script}", flush=True)
    subprocess.run([sys.executable, str(AUDIT_DIR / script), *args], check=True, cwd=AUDIT_DIR)


def build_stats() -> dict:
    s1, s2, s3 = read_out("step1_inventory.json"), read_out("step2_schema.json"), read_out("step3_coverage.json")
    s4, s5, s6, ocr = (read_out("step4_splits.json"), read_out("step5_tamper.json"),
                       read_out("step6_quality.json"), read_out("step6_ocr.json"))
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": "dataset_v2",
        "labels_csv_sha256": sha256(DATASET / "labels.csv"),
        "inventory": {k: s1[k] for k in ("file_count", "files_by_extension", "total_mb", "pdf_page_counts")}
        | {"label_rows": s1["labels_csv"]["row_count"],
           "files_without_label_row": len(s1["files_without_label_row"]),
           "label_rows_without_file": len(s1["label_rows_without_file"]),
           "corrupt_files": len(s1["corrupt_or_unreadable"])},
        "schema": {k: s2[k] for k in ("violation_count", "violations_by_rule", "value_counts",
                                      "target_verdict_counts", "byte_identical_non_self_pairs")},
        "coverage": {k: s3[k] for k in ("base_documents", "base_by_type", "class_all_rows", "expected_verdict",
                                        "severity", "capture", "class_x_capture", "class_by_doc_type",
                                        "class_by_split", "harmless_share_pct")},
        "splits": {k: s4[k] for k in ("leaking_bases", "ratios", "coverage_gaps_val_test",
                                      "cross_split_base_pairs_total", "cross_split_pairs_above_threshold",
                                      "cross_split_pairs_narrative_above_threshold",
                                      "full_text_similarity_all_pairs", "narrative_similarity_all_pairs",
                                      "values_only_similarity_all_pairs",
                                      "distinct_narratives_after_masking_ids", "replacement_values_per_class")},
        "tamper_correctness": {c: {k: v[k] for k in ("checked", "pass", "fail", "verdict")}
                               for c, v in s5["per_class"].items()}
        | {"pairs_with_header_label_leak": s5["pairs_with_header_label_leak"]},
        "content_quality": {k: s6[k] for k in ("realism_marker_hits_by_doc_type", "act_names_used",
                                               "all_doc_types_share_one_layout", "pii_hits",
                                               "non_ascii_chars_in_pdf_text", "pdfs_with_devanagari",
                                               "distinct_values_per_field_across_50_bases", "image_quality",
                                               "images_flagged_pct")},
        "ocr": ocr["summary"] if ocr else None,
    }
    write_json("../stats.json", stats)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-ocr", action="store_true")
    ap.add_argument("--per-class", default="2")
    a = ap.parse_args()
    for s in STEPS:
        run(s)
    if not a.skip_ocr:
        run("step6_ocr.py", "--per-class", a.per_class)
    build_stats()
    run("build_issues.py")
    print("Wrote stats.json and issues.csv. REPORT.md is written by hand from these numbers.")


if __name__ == "__main__":
    main()
