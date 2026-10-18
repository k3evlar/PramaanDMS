"""Audit of dataset_v3 against the targets in docs/DATASET_V3_PLAN.md section 8.

Read only. Writes outputs/v3_audit.json and prints a pass/fail table.
Usage (from analysis/dataset_audit):  .venv/Scripts/python audit_v3.py [--data ../../dataset_v3]
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image
from rapidfuzz import fuzz

from audit_lib import ROOT, pct, write_json
from compare_v0_narratives import mask_v0

SPLITS = ("train", "val", "test", "test_unseen")
SEEN = ("train", "val", "test")


def pdf_text_and_meta(path: Path) -> tuple[str, str]:
    doc = pdfium.PdfDocument(str(path))
    try:
        text = " ".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
        meta = " ".join(str(v) for v in doc.get_metadata_dict().values())
        return text, meta
    finally:
        doc.close()


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "dataset_v3")
    data = ap.parse_args().data.resolve()

    with open(data / "labels_eclass.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    versions = json.loads((data / "labels.json").read_text(encoding="utf-8"))["versions"]
    bases = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (data / "base_docs").glob("*.json")}
    codes = sorted({r["tamper_class"] for r in rows})

    # 1. Files exist and open
    missing, corrupt, n_files = [], [], 0
    for r in rows:
        for rel in r["files"].split(";"):
            p = data / rel
            n_files += 1
            if not p.is_file():
                missing.append(rel)
                continue
            try:
                if p.suffix == ".pdf":
                    d = pdfium.PdfDocument(str(p))
                    ok = len(d) > 0
                    d.close()
                    if not ok:
                        raise ValueError("no pages")
                else:
                    with Image.open(p) as im:
                        im.verify()
            except Exception as exc:  # noqa: BLE001
                corrupt.append(f"{rel}: {exc}")

    # 2. Label leakage in printed text or PDF metadata (digital vector PDFs)
    leak_pat = re.compile(r"\b(" + "|".join(map(re.escape, codes)) + r")\b|\bE\d{1,2}\b|FIR-Tamper v\d")
    text_leaks, meta_leaks, version_footer = [], [], 0
    for r in rows:
        if r["capture_type"] != "digital":
            continue
        p = data / r["files"].split(";")[0]
        text, meta = pdf_text_and_meta(p)
        hits = {m.group(0) for m in leak_pat.finditer(text)}
        if "FIR-Tamper v0" in text:
            version_footer += 1
            hits.discard("FIR-Tamper v0")
        if hits:
            text_leaks.append(f"{r['sample_id']}: {sorted(hits)}")
        if leak_pat.search(meta.replace("FIR-Tamper", "")):
            meta_leaks.append(r["sample_id"])
    path_leaks = sum(any(c in r["files"] for c in codes if c != "NONE") for r in rows)

    # 3. Splits
    split_of: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        split_of[r["original_id"]].add(r["split"])
    leaking = sorted(b for b, s in split_of.items() if len(s) > 1)
    base_split = {b: next(iter(s)) for b, s in split_of.items()}
    nb = len(base_split)
    split_bases = Counter(base_split.values())
    n_seen = sum(split_bases[s] for s in SEEN)
    splits_present = [s for s in SPLITS if split_bases[s]]
    ratios = {s: {"bases": split_bases[s], "pct": pct(split_bases[s], n_seen)} for s in SEEN}
    ratios["test_unseen"] = {"bases": split_bases["test_unseen"], "pct": None}

    # 4. Narrative diversity and template overlap
    narr = {b: " ".join(bases[b]["narrative"]) for b in base_split}
    cross = [fuzz.ratio(narr[a], narr[b]) / 100 for a, b in itertools.combinations(sorted(narr), 2)
             if base_split[a] != base_split[b]]
    sent_splits: dict[str, set[str]] = defaultdict(set)
    for b, rec in bases.items():
        for s in rec["narrative"]:
            sent_splits[mask_v0(s, rec)].add(base_split[b])
    train_tpl = {t for b, rec in bases.items() if base_split[b] == "train" for t in rec.get("template_ids", [])}

    def tpl_overlap(split: str) -> float | None:
        shares = [sum(t in train_tpl for t in rec["template_ids"]) / len(rec["template_ids"])
                  for b, rec in bases.items() if base_split[b] == split and rec.get("template_ids")]
        return round(sum(shares) / len(shares), 3) if shares else None
    overlap_test, overlap_unseen = tpl_overlap("test"), tpl_overlap("test_unseen")

    # 5. Coverage and balance
    harmless = sum(r["e_class"] == "E0" for r in rows)
    e_by_split = {s: dict(Counter(r["e_class"] for r in rows if r["split"] == s)) for s in splits_present}
    v3_by_split = {s: dict(Counter(r["verdict_3level"] for r in rows if r["split"] == s)) for s in splits_present}
    sev_by_split = {s: dict(Counter(r["severity"] for r in rows if r["split"] == s)) for s in splits_present}
    used_train = {r["tamper_class"] for r in rows if r["split"] == "train"}
    sub_by_split = {s: sorted(used_train - {r["tamper_class"] for r in rows if r["split"] == s})
                    for s in splits_present if s != "train"}
    all_e = [f"E{i}" for i in range(20)]
    missing_e = [e for e in all_e if not any(r["e_class"] == e for r in rows)]
    min_test = min((e_by_split.get("test", {}).get(e, 0), e) for e in all_e)

    needed_verdicts = {"Identical", "Equivalent", "Materially Altered", "Inconclusive", "Not supported"}
    checks = [
        ("Label rows with a missing file", len(missing), len(missing) == 0),
        ("Corrupt or unreadable files", len(corrupt), len(corrupt) == 0),
        ("Class code in printed text (digital PDFs)", len(text_leaks), len(text_leaks) == 0),
        ("Class code in PDF metadata", len(meta_leaks), len(meta_leaks) == 0),
        ("Base documents in more than one split", len(leaking), len(leaking) == 0),
        ("Class code in any file path", path_leaks, path_leaks == 0),
        ("Version tag in the page footer", version_footer, version_footer == 0),
        ("Validation share of seen bases (%)", ratios["val"]["pct"], 13 <= ratios["val"]["pct"] <= 17),
        ("Test share of seen bases (%)", ratios["test"]["pct"], 13 <= ratios["test"]["pct"] <= 17),
        ("Distinct narratives / bases", f"{len(set(narr.values()))} / {nb}", len(set(narr.values())) == nb),
        ("Cross-split narrative pairs above 0.9", sum(s > 0.9 for s in cross), sum(s > 0.9 for s in cross) == 0),
        ("Harmless (E0) share of rows (%)", pct(harmless, len(rows)), 30 <= pct(harmless, len(rows)) <= 40),
        ("Generator classes used in train but missing from another split", {k: v for k, v in sub_by_split.items() if v},
         all(not v for v in sub_by_split.values())),
        ("E-classes with no samples", missing_e, not missing_e),
        ("Smallest per-E-class test count (samples)", f"{min_test[0]} ({min_test[1]})", min_test[0] >= 60),
        ("test_unseen sentences whose template is in train (mean share)", overlap_unseen,
         overlap_unseen == 0 if overlap_unseen is not None else False),
        ("All 5 verdicts in every split", {s: sorted(needed_verdicts - set(v)) for s, v in v3_by_split.items()},
         all(needed_verdicts <= set(v) for v in v3_by_split.values())),
        ("Major and Minor in every split", {s: sorted({"Major", "Minor"} - set(v)) for s, v in sev_by_split.items()},
         all({"Major", "Minor"} <= set(v) for v in sev_by_split.values())),
    ]
    known_limits = [
        ("test (seen families) sentences whose template is in train (mean share)", overlap_test,
         "Expected: seen-family test shares templates by design; test_unseen measures generalisation"),
        ("Captures", "simulated scan_sim and photo_sim, one level", "Harder and real captures in Phase 10 (Stage 3)"),
    ]

    result = {
        "data": str(data.relative_to(ROOT)) if data.is_relative_to(ROOT) else str(data), "rows": len(rows), "versions": len(versions), "bases": nb,
        "files_checked": n_files,
        "checks": [{"check": c, "value": v, "pass": ok} for c, v, ok in checks],
        "known_limitations": [{"item": c, "value": v, "plan": p} for c, v, p in known_limits],
        "ratios": ratios, "template_overlap": {"test": overlap_test, "test_unseen": overlap_unseen},
        "rows_by_split": dict(Counter(r["split"] for r in rows)),
        "rows_by_capture": dict(Counter(r["capture_type"] for r in rows)),
        "rows_by_doc_type": dict(Counter(r["doc_type"] for r in rows)),
        "bases_by_doc_type": dict(Counter(bases[b]["doc_type"] for b in base_split)),
        "e_class_by_split": e_by_split, "verdict_3level_by_split": v3_by_split, "severity_by_split": sev_by_split,
        "narrative_cross_split_similarity": {"min": round(min(cross), 4), "mean": round(sum(cross) / len(cross), 4),
                                             "max": round(max(cross), 4), "pairs": len(cross)},
        "narrative_mean_words": round(sum(len(t.split()) for t in narr.values()) / nb, 1),
        "missing_files": missing[:50], "corrupt_files": corrupt[:50], "text_leaks": text_leaks[:50],
    }
    write_json("v3_audit.json", result)
    for c in result["checks"]:
        print(("PASS" if c["pass"] else "FAIL"), "|", c["check"], "|", c["value"])
    for k in result["known_limitations"]:
        print("NOTE |", k["item"], "|", k["value"], "|", k["plan"])
    return result


if __name__ == "__main__":
    main()
