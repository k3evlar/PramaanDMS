"""Step 6 (part 1): realism, personal data, language, templating, image quality.
OCR character error rate is in step6_ocr.py because it is slow."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import cv2
import numpy as np

from audit_lib import (CAPTURE_ALIASES, DATASET, FIELDS_27, abs_path, base_json, base_pdf,
                       label_rows, load_json, pdf_text, pct, write_json)

# Structural markers of real Indian FIRs, statements and charge sheets. These are
# generic form labels, not legal claims (see dataset/templates/SOURCES.md for the v0 source).
REALISM_MARKERS = {
    "BNS / BNSS / BSA reference": r"\bBNSS?\b|\bBSA\b|Bharatiya",
    "IPC / CrPC reference": r"\bIPC\b|\bCr\.?P\.?C\b",
    "u/s or 'Section N of <Act>' citation": r"\bu/s\b|Section\s+\d+\S*\s+of\s+",
    "Police Station label": r"Police Station|\bP\.S\.",
    "District label": r"\bDistrict\b",
    "Complainant / informant particulars": r"Father'?s|S/o|D/o|W/o|Address|Informant",
    "Information received at PS (date/time)": r"Information received|General Diary|GD No",
    "Brief facts / statement body heading": r"Brief facts|Contents of|Statement of",
    "Officer rank and belt / ID": r"\b(SI|ASI|Inspector|Sub-Inspector|Belt No)\b",
    "Signature of officer / complainant": r"Signature|Thumb impression",
}
PII_PATTERNS = {
    "indian_mobile": r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
    "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "aadhaar_like": r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)",
    "pan_like": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "pin_code_like": r"(?<![\d-])\d{6}(?![\d-])",
    "street_address": r"\b(House|Flat|Plot)\s+No\b|\b(Road|Street|Nagar|Colony|Layout)\b",
}
# Thresholds for "too bad to OCR". Chosen to be lenient; they flag clear outliers only.
MIN_DPI = 150
MIN_SHARPNESS_RATIO = 0.25   # Laplacian variance vs the clean render of the same page
MAX_SKEW_DEG = 5.0
BRIGHT_RANGE = (60, 250)
MIN_CONTRAST = 25


def page_skew(gray: np.ndarray) -> float:
    small = cv2.resize(gray, (600, int(gray.shape[0] * 600 / gray.shape[1])))
    edges = cv2.Canny(small, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 720, threshold=100, minLineLength=250, maxLineGap=4)
    if lines is None:
        return float("nan")
    angles = [np.degrees(np.arctan2(y2 - y1, x2 - x1)) for x1, y1, x2, y2 in lines.reshape(-1, 4)]
    angles = [a for a in angles if abs(a) < 20]
    return float(np.median(angles)) if angles else float("nan")


def image_metrics(path) -> dict:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    return {"w": w, "h": h, "dpi_a4": round(w / 8.27, 1),
            "sharpness": float(cv2.Laplacian(img, cv2.CV_64F).var()),
            "brightness": float(img.mean()), "contrast": float(img.std()),
            "skew_deg": page_skew(img)}


def clean_render_metrics() -> dict:
    """Same metrics on a clean 160 dpi render (the capture script renders at 160 dpi)."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(base_pdf("BASE-0001")))
    pil = doc[0].render(scale=160 / 72).to_pil().convert("L")
    doc.close()
    img = np.asarray(pil)
    return {"sharpness": float(cv2.Laplacian(img, cv2.CV_64F).var()),
            "brightness": float(img.mean()), "contrast": float(img.std()), "w": img.shape[1]}


def summarize(vals: list[float]) -> dict:
    a = np.array([v for v in vals if v == v])
    return {"min": round(float(a.min()), 2), "p05": round(float(np.percentile(a, 5)), 2),
            "median": round(float(np.median(a)), 2), "max": round(float(a.max()), 2)} if len(a) else {}


def main() -> dict:
    rows = label_rows()
    bases = sorted({r["original_id"] for r in rows})
    base_type = {r["original_id"]: r["doc_type"] for r in rows}
    texts = {b: pdf_text(base_pdf(b)) for b in bases}

    # Realism
    realism = {m: {t: 0 for t in ("FIR", "charge_sheet", "statement", "court_order")} for m in REALISM_MARKERS}
    for b, t in texts.items():
        for m, pat in REALISM_MARKERS.items():
            if re.search(pat, t):
                realism[m][base_type[b]] += 1
    acts = Counter(load_json(base_json(b))["act_name"] for b in bases)
    sections = Counter(load_json(base_json(b))["section_number"] for b in bases)
    layouts = defaultdict(set)
    for b in bases:
        labels_printed = tuple(l.split(" ", 1)[0] for l in texts[b].splitlines() if l.split(" ", 1)[0] in FIELDS_27)
        layouts[base_type[b]].add(labels_printed)
    same_layout_all_types = len({lay for s in layouts.values() for lay in s}) == 1
    timeline = []
    for b in bases:
        j = load_json(base_json(b))
        if j["document_date"] < j["incident_date"]:
            timeline.append(f"{b}: document_date before incident_date")
        if j["filing_date"] < j["incident_date"]:
            timeline.append(f"{b}: filing_date before incident_date")

    # Personal data and language (every printed text layer and every JSON value)
    pii_hits: dict[str, list[str]] = defaultdict(list)
    non_ascii: Counter = Counter()
    devanagari = 0
    for r in rows:
        if r["capture_type"] != "digital":
            continue
        t = pdf_text(abs_path(r["file_path"]))
        for k, pat in PII_PATTERNS.items():
            for m in re.findall(pat, t):
                pii_hits[k].append(f"{r['sample_id']}: {m if isinstance(m, str) else ''.join(m)}")
        for ch in t:
            if ord(ch) > 127:
                non_ascii[f"U+{ord(ch):04X}"] += 1
        if re.search(r"[ऀ-ॿ]", t):
            devanagari += 1
    json_non_ascii = Counter()
    for p in DATASET.rglob("*.json"):
        for ch in p.read_text(encoding="utf-8"):
            if ord(ch) > 127:
                json_non_ascii[f"U+{ord(ch):04X}"] += 1
    name_pool = Counter()
    for b in bases:
        j = load_json(base_json(b))
        for f in ("complainant_name", "accused_name", "victim_name", "witness_name",
                  "investigating_officer", "advocate_name"):
            name_pool[j[f]] += 1

    # Templating
    distinct_per_field = {f: len({str(load_json(base_json(b))[f]) for b in bases}) for f in FIELDS_27}
    sentence_counter: Counter = Counter()
    for b in bases:
        j = load_json(base_json(b))
        for f in ("offence_description", "evidence_description"):
            for s in re.split(r"(?<=[.;])\s+", re.sub(r"EXHIBIT-SYN-\w+", "<ID>", j[f])):
                sentence_counter[s.strip()] += 1
    repeated_sentences = {s: n for s, n in sentence_counter.items() if n > 1}

    # Image quality on every capture image
    ref = clean_render_metrics()
    img_stats: dict[str, list[dict]] = defaultdict(list)
    flagged: list[dict] = []
    for r in rows:
        if r["capture_type"] == "digital":
            continue
        cap = CAPTURE_ALIASES[r["capture_type"]]
        m = image_metrics(abs_path(r["file_path"]))
        m["sample_id"] = r["sample_id"]
        img_stats[cap].append(m)
        reasons = []
        if m["dpi_a4"] < MIN_DPI:
            reasons.append(f"dpi {m['dpi_a4']}")
        if m["sharpness"] < MIN_SHARPNESS_RATIO * ref["sharpness"]:
            reasons.append(f"blur (sharpness {m['sharpness']:.0f} vs clean {ref['sharpness']:.0f})")
        if m["skew_deg"] == m["skew_deg"] and abs(m["skew_deg"]) > MAX_SKEW_DEG:
            reasons.append(f"skew {m['skew_deg']:.1f} deg")
        if not BRIGHT_RANGE[0] <= m["brightness"] <= BRIGHT_RANGE[1]:
            reasons.append(f"brightness {m['brightness']:.0f}")
        if m["contrast"] < MIN_CONTRAST:
            reasons.append(f"contrast {m['contrast']:.0f}")
        if reasons:
            flagged.append({"sample_id": r["sample_id"], "reasons": reasons})
    image_summary = {cap: {k: summarize([m[k] for m in ms]) for k in
                           ("dpi_a4", "sharpness", "brightness", "contrast", "skew_deg")}
                     | {"count": len(ms), "abs_skew": summarize([abs(m["skew_deg"]) for m in ms])}
                     for cap, ms in img_stats.items()}

    result = {
        "realism_marker_hits_by_doc_type": realism,
        "act_names_used": dict(acts),
        "sections_used": dict(sections),
        "all_doc_types_share_one_layout": same_layout_all_types,
        "layout_variants_per_type": {t: len(v) for t, v in layouts.items()},
        "timeline_inconsistencies_in_bases": timeline,
        "pii_hits": {k: {"count": len(v), "examples": v[:5]} for k, v in pii_hits.items()},
        "non_ascii_chars_in_pdf_text": dict(non_ascii),
        "non_ascii_chars_in_json": dict(json_non_ascii),
        "pdfs_with_devanagari": devanagari,
        "name_pool": dict(name_pool.most_common()),
        "distinct_values_per_field_across_50_bases": distinct_per_field,
        "repeated_narrative_sentences": repeated_sentences,
        "clean_render_reference": ref,
        "image_quality": image_summary,
        "image_thresholds": {"min_dpi": MIN_DPI, "min_sharpness_ratio": MIN_SHARPNESS_RATIO,
                             "max_skew_deg": MAX_SKEW_DEG, "brightness": BRIGHT_RANGE,
                             "min_contrast": MIN_CONTRAST},
        "images_flagged": flagged,
        "images_flagged_pct": pct(len(flagged), sum(len(v) for v in img_stats.values())),
    }
    write_json("step6_quality.json", result)
    print("realism", {m: sum(v.values()) for m, v in realism.items()})
    print("pii", {k: len(v) for k, v in pii_hits.items()}, "non-ascii", dict(non_ascii), "json", dict(json_non_ascii))
    print("distinct per field", distinct_per_field)
    print("names", len(name_pool), "repeated sentences", repeated_sentences)
    print("images", image_summary, "flagged", len(flagged), flagged[:3])
    print("ref", ref, "timeline", timeline[:3])
    return result


if __name__ == "__main__":
    main()
