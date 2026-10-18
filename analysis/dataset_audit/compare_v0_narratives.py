"""Compare narrative diversity of dataset/ (v0, ml/data/generator) with dataset_v2/.
Read only. Writes outputs/compare_v0_v2_narratives.json.

Same measures as step4_splits.py: distinct narratives, and narrative similarity of
base-document pairs in different splits (RapidFuzz normalised Indel ratio). For v0 the
narrative entities (names, dates, amounts, vehicles) are also masked, which shows how much
of the similarity comes from shared sentence templates.
"""
from __future__ import annotations

import itertools
import json
import re
from collections import Counter

from rapidfuzz import fuzz

from audit_lib import ROOT, base_json, label_rows, load_json, write_json

V0 = ROOT / "dataset"


def v0_bases() -> tuple[dict[str, dict], dict[str, str]]:
    recs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((V0 / "base_docs").glob("*.json"))}
    split_of = {}
    for s in ("train", "val", "test"):
        for line in (V0 / "splits" / f"{s}.txt").read_text(encoding="utf-8").split():
            split_of[line.strip()] = s
    return recs, split_of


def mask_v0(text: str, rec: dict) -> str:
    f = rec["fields"]
    names = [f.get("complainant_name", "")] + f.get("accused_names", []) + f.get("victim_names", []) \
        + f.get("witness_names", []) + [f.get("officer_name", "")]
    for n in sorted({re.sub(r"^(Shri|Smt)\s+", "", x) for x in names if x}, key=len, reverse=True):
        text = text.replace(n, "<NAME>")
    text = re.sub(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}(st|nd|rd|th)? \w+ \d{4}\b", "<DATE>", text)
    text = re.sub(r"\b\d{1,2}[:.]\d{2}\s?(AM|PM|hrs)?\b", "<TIME>", text)
    text = re.sub(r"Rs\.?\s?[\d,]+(/-)?", "<AMOUNT>", text)
    text = re.sub(r"ZZ[\s-]?\d{2}[\s-]?[A-Z]{1,2}[\s-]?\d{4}", "<VEHICLE>", text)
    return text


def stats(narr: dict[str, str], split_of: dict[str, str]) -> dict:
    ids = sorted(narr)
    cross = [fuzz.ratio(narr[a], narr[b]) / 100 for a, b in itertools.combinations(ids, 2)
             if split_of[a] != split_of[b]]
    return {"bases": len(ids), "distinct_narratives": len(set(narr.values())),
            "cross_split_pairs": len(cross),
            "cross_split_pairs_above_0.9": sum(s > 0.9 for s in cross),
            "cross_split_sim_min": round(min(cross), 4), "cross_split_sim_mean": round(sum(cross) / len(cross), 4),
            "cross_split_sim_max": round(max(cross), 4),
            "mean_words": round(sum(len(t.split()) for t in narr.values()) / len(ids), 1)}


def main() -> dict:
    recs, split_of = v0_bases()
    raw = {k: " ".join(r["narrative"]) for k, r in recs.items()}
    masked = {k: mask_v0(raw[k], recs[k]) for k in recs}
    sentences = Counter(s for k in recs for s in (mask_v0(x, recs[k]) for x in recs[k]["narrative"]))

    rows = label_rows()
    v2_split = {r["original_id"]: r["split"] for r in rows}
    v2_narr = {b: " ".join(load_json(base_json(b))[f] for f in ("evidence_description", "offence_description"))
               for b in v2_split}
    v2_masked = {b: re.sub(r"EXHIBIT-SYN-\w+", "<ID>", t) for b, t in v2_narr.items()}

    result = {
        "v0_raw": stats(raw, split_of),
        "v0_entities_masked": stats(masked, split_of),
        "v0_scenarios": dict(Counter(r.get("scenario") for r in recs.values())),
        "v0_doc_types": dict(Counter(r["doc_type"] for r in recs.values())),
        "v0_distinct_masked_sentences": len(sentences),
        "v0_sentences_used_by_over_half_of_bases": sum(n > len(recs) / 2 for n in sentences.values()),
        "v2_raw": stats(v2_narr, v2_split),
        "v2_ids_masked": stats(v2_masked, v2_split),
    }
    write_json("compare_v0_v2_narratives.json", result)
    print(json.dumps(result, indent=1))
    return result


if __name__ == "__main__":
    main()
