"""Step 6 (part 2): quick OCR on a stratified sample of scan and photo images and a
clean digital render baseline. Reports character error rate (CER) against the PDF
text layer, token recall, critical field exact-match rate, whether the tampered value
survives capture, and whether the printed sample ID / class code is readable by OCR.

OCR engine: RapidOCR (Apache-2.0) with PP-OCR ONNX models (Apache-2.0).
Usage: python step6_ocr.py [--per-class 2]
"""
from __future__ import annotations

import argparse
import random
import re
import time
from collections import Counter, defaultdict

import numpy as np
from rapidfuzz.distance import Levenshtein

from audit_lib import (CAPTURE_ALIASES, CLASSES, FIELDS_27, SEED, abs_path, base_json, label_rows,
                       load_json, norm_text, pdf_text, sidecar_json, source_pdf, write_json)


def ocr_lines(engine, image) -> str:
    res = engine(image)
    if res.boxes is None or res.txts is None:
        return ""
    items = []
    for box, txt in zip(res.boxes, res.txts):
        b = np.asarray(box)
        items.append((b[:, 1].mean(), b[:, 0].min(), b[:, 1].max() - b[:, 1].min(), txt))
    items.sort()
    med_h = float(np.median([h for _, _, h, _ in items])) if items else 10
    lines: list[list[tuple]] = []
    for it in items:
        if lines and abs(it[0] - lines[-1][-1][0]) < 0.5 * med_h:
            lines[-1].append(it)
        else:
            lines.append([it])
    return "\n".join(" ".join(t for _, _, _, t in sorted(l, key=lambda x: x[1])) for l in lines)


def squash(s: str) -> str:
    return re.sub(r"\s+", "", norm_text(s)).lower()


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=2, help="images per class per capture type")
    args = ap.parse_args()

    from rapidocr import RapidOCR
    engine = RapidOCR()

    rows = label_rows()
    rng = random.Random(SEED)
    by_cap_cls: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        by_cap_cls[(CAPTURE_ALIASES[r["capture_type"]], r["tamper_class"])].append(r)
    sample: list[dict] = []
    for cap in ("scan", "photo"):
        for c in CLASSES:
            sample += rng.sample(by_cap_cls[(cap, c)], args.per_class)
    for c in CLASSES:  # digital baseline: render the PDF at the capture script's 160 dpi
        sample += rng.sample(by_cap_cls[("digital", c)], 1)

    per_sample = []
    t0 = time.time()
    for r in sample:
        cap = CAPTURE_ALIASES[r["capture_type"]]
        if cap == "digital":
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(abs_path(r["file_path"])))
            img = np.asarray(doc[0].render(scale=160 / 72).to_pil().convert("RGB"))
            doc.close()
        else:
            img = str(abs_path(r["file_path"]))
        ocr = ocr_lines(engine, img)
        gt = pdf_text(source_pdf(r))
        g, o = norm_text(gt), norm_text(ocr)
        cer = Levenshtein.distance(o, g) / max(1, len(g))
        gt_tok, oc_tok = Counter(g.split()), Counter(o.split())
        recall = sum((gt_tok & oc_tok).values()) / max(1, sum(gt_tok.values()))
        rec = load_json(sidecar_json(r))
        o_sq = squash(ocr)
        field_hits = {f: squash(str(rec[f])) in o_sq for f in FIELDS_27}
        changed_ok = None
        if r["tamper_class"] not in ("E0", "E15"):
            base = load_json(base_json(r["original_id"]))
            changed = [f for f in FIELDS_27 if base[f] != rec[f]]
            changed_ok = all(squash(str(rec[f])) in o_sq for f in changed) if changed else None
        if r["tamper_class"] == "E15":
            changed_ok = "e15test" in o_sq
        leak = bool(re.search(r"BASE-\d{4}-E\d+|variant:?\s*E\d+", ocr))
        per_sample.append({"sample_id": r["sample_id"], "capture": cap, "class": r["tamper_class"],
                           "cer": round(cer, 4), "token_recall": round(recall, 4),
                           "field_exact_match_rate": round(sum(field_hits.values()) / len(FIELDS_27), 4),
                           "fields_missed": [f for f, ok in field_hits.items() if not ok],
                           "tampered_value_read": changed_ok, "label_readable_in_image": leak})
        print(f"{len(per_sample)}/{len(sample)} {r['sample_id']} cer={cer:.3f} fields={sum(field_hits.values())}/27 "
              f"({time.time() - t0:.0f}s)", flush=True)

    summary = {}
    for cap in ("digital", "scan", "photo"):
        s = [p for p in per_sample if p["capture"] == cap]
        cers = np.array([p["cer"] for p in s])
        tv = [p["tampered_value_read"] for p in s if p["tampered_value_read"] is not None]
        summary[cap] = {
            "n": len(s),
            "cer_mean": round(float(cers.mean()), 4), "cer_median": round(float(np.median(cers)), 4),
            "cer_p90": round(float(np.percentile(cers, 90)), 4), "cer_max": round(float(cers.max()), 4),
            "token_recall_mean": round(float(np.mean([p["token_recall"] for p in s])), 4),
            "field_exact_match_mean": round(float(np.mean([p["field_exact_match_rate"] for p in s])), 4),
            "tampered_value_read_rate": round(sum(tv) / len(tv), 4) if tv else None,
            "tampered_value_n": len(tv),
            "label_readable_in_image_rate": round(np.mean([p["label_readable_in_image"] for p in s]), 4),
            "most_missed_fields": Counter(f for p in s for f in p["fields_missed"]).most_common(5),
        }
    result = {"engine": "RapidOCR (PP-OCR ONNX), default settings",
              "ground_truth": "PDF text layer of the source digital sample, whitespace collapsed, dashes folded",
              "sample_design": f"{args.per_class} random images per class per capture type (seed {SEED}), "
                               "plus 1 digital render per class at 160 dpi as a baseline",
              "seconds": round(time.time() - t0, 1), "summary": summary, "per_sample": per_sample}
    write_json("step6_ocr.json", result)
    print(summary)
    return result


if __name__ == "__main__":
    main()
