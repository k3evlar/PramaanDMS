"""Independent check of dataset_v3 captures: after simulated scan or photo, can OCR still read
(a) the changed values of field edits and (b) the field values of harmless (E0) copies?

Read only. Writes outputs/v3_ocr.json.
Usage (from analysis/dataset_audit):  .venv/Scripts/python ocr_v3.py [--per-capture 40]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

from audit_lib import ROOT, SEED, write_json

sys.path.insert(0, str(ROOT))
from ml.data.generator.check import _style, _tuple_fields, displays  # noqa: E402

DATA = ROOT / "dataset_v3"


def squash(s: str) -> str:
    return re.sub(r"[\s—–\-]+", "", s).lower()


# Header fields that every layout prints on page 1, used for the harmless (E0) check.
HEADER_KEYS = ("district", "police_station", "fir_number", "date_of_report", "date_of_incident",
               "date_of_statement", "charge_sheet_number")


def page_images(rel: str, data: Path, pages: set[int]) -> list[np.ndarray]:
    """Images of the given 1-based pages only (OCR is slow; a page takes about 15 s)."""
    out = []
    parts = rel.split(";")
    for n, part in enumerate(parts, 1):
        p = data / part
        if p.suffix == ".pdf":
            doc = pdfium.PdfDocument(str(p))
            out += [np.asarray(doc[i].render(scale=200 / 72).to_pil().convert("RGB"))
                    for i in range(len(doc)) if i + 1 in pages]
            doc.close()
        elif n in pages:
            out.append(np.asarray(Image.open(p).convert("RGB")))
    return out


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-capture", type=int, default=40)
    a = ap.parse_args()
    from rapidocr import RapidOCR
    engine = RapidOCR()

    with open(DATA / "labels_eclass.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    versions = {v["version_id"]: v for v in json.loads((DATA / "labels.json").read_text(encoding="utf-8"))["versions"]}
    base_disp: dict[str, dict[str, str]] = {}

    def new_strings(v: dict) -> list[str]:
        """Printed values present in the variant but not in its original (the visible edit)."""
        oid = v["original_id"]
        if oid not in base_disp:
            rec = json.loads((DATA / "base_docs" / f"{oid}.json").read_text(encoding="utf-8"))
            base_disp[oid] = displays(_tuple_fields(rec["fields"]), _style(rec["style"]), set())
        var = displays(_tuple_fields(v["variant"]["fields"]), _style(v["variant"]["style"]), set(v["variant"]["redacted"]))
        return [s for k, s in var.items() if base_disp[oid].get(k) != s]

    rng = random.Random(SEED)
    pools: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        v = versions[r["version_id"]]
        if v["group"] == "field" and r["e_class"] not in ("E16",) and new_strings(v):
            pools[(r["capture_type"], "edit")].append(r)
        elif r["e_class"] == "E0":
            pools[(r["capture_type"], "e0")].append(r)
    sample = []
    for cap in ("digital", "scan_sim", "photo_sim"):
        n = a.per_capture if cap != "digital" else a.per_capture // 2
        sample += [(cap, "edit", r) for r in rng.sample(pools[(cap, "edit")], n)]
        sample += [(cap, "e0", r) for r in rng.sample(pools[(cap, "e0")], n // 2)]

    results = []
    t0 = time.time()
    for k, (cap, kind, r) in enumerate(sample, 1):
        v = versions[r["version_id"]]
        if kind == "edit":
            targets = new_strings(v)
            pages = {p for c in v["changes"] for p in c["pages"]} or {1, 2, 3}
        else:
            rec = v["variant"]
            disp = displays(_tuple_fields(rec["fields"]), _style(rec["style"]), set())
            targets = [disp[k] for k in HEADER_KEYS if k in disp]
            pages = {1}
        txt = []
        for img in page_images(r["files"], DATA, pages):
            res = engine(img)
            txt += list(res.txts or [])
        o = squash(" ".join(txt))
        found = [squash(t) in o for t in targets]
        results.append({"sample_id": r["sample_id"], "capture": cap, "kind": kind, "e_class": r["e_class"],
                        "subtype": r["tamper_class"], "targets": len(targets), "found": sum(found),
                        "all_found": all(found), "missed": [t for t, ok in zip(targets, found) if not ok][:5]})
        print(f"{k}/{len(sample)} {cap} {kind} {r['e_class']} {sum(found)}/{len(targets)} ({time.time() - t0:.0f}s)", flush=True)

    summary = {}
    for cap in ("digital", "scan_sim", "photo_sim"):
        e = [x for x in results if x["capture"] == cap and x["kind"] == "edit"]
        z = [x for x in results if x["capture"] == cap and x["kind"] == "e0"]
        summary[cap] = {
            "edit_samples": len(e),
            "edit_value_readable_rate": round(sum(x["all_found"] for x in e) / len(e), 3) if e else None,
            "e0_samples": len(z),
            "e0_field_read_rate": round(sum(x["found"] for x in z) / max(1, sum(x["targets"] for x in z)), 3),
            "e0_all_fields_read_rate": round(sum(x["all_found"] for x in z) / len(z), 3) if z else None,
        }
    out = {"engine": "RapidOCR (PP-OCR ONNX), default settings", "seed": SEED,
           "seconds": round(time.time() - t0), "summary": summary, "per_sample": results}
    write_json("v3_ocr.json", out)
    print(json.dumps(summary, indent=1))
    return out


if __name__ == "__main__":
    main()
