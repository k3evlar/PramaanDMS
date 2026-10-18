"""Step 4: split integrity. Leakage by base document, near-duplicate bases across
splits, actual ratios, class and capture coverage in validation and test."""
from __future__ import annotations

import itertools
from collections import Counter, defaultdict

from rapidfuzz import fuzz

from audit_lib import (CAPTURE_ALIASES, CLASSES, FIELDS_27, NARRATIVE_FIELDS, SPLIT_TARGET,
                       base_json, base_pdf, label_rows, load_json, norm_text, pct, pdf_text,
                       sidecar_json, strip_header, write_json)

NEAR_DUP = 0.90


def main() -> dict:
    rows = label_rows()
    splits_of: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        splits_of[r["original_id"]].add(r["split"])
    leaking = {b: sorted(s) for b, s in splits_of.items() if len(s) > 1}
    split_of = {b: next(iter(s)) for b, s in splits_of.items()}

    base_counts = Counter(split_of.values())
    sample_counts = Counter(r["split"] for r in rows)
    nb, ns = len(split_of), len(rows)
    ratios = {s: {"bases": base_counts[s], "bases_pct": pct(base_counts[s], nb),
                  "samples": sample_counts[s], "samples_pct": pct(sample_counts[s], ns),
                  "target_pct": SPLIT_TARGET[s] * 100}
              for s in ("train", "validation", "test")}

    # Coverage of every class and capture variant in validation and test.
    missing_cov = []
    for s in ("validation", "test"):
        have_cls = {r["tamper_class"] for r in rows if r["split"] == s}
        have_cap = {CAPTURE_ALIASES[r["capture_type"]] for r in rows if r["split"] == s}
        for c in CLASSES:
            if c not in have_cls:
                missing_cov.append(f"{c} missing from {s}")
        for c in ("digital", "scan", "photo"):
            if c not in have_cap:
                missing_cov.append(f"{c} missing from {s}")
        for c in CLASSES:
            for cap in ("digital", "scan", "photo"):
                if not any(r["split"] == s and r["tamper_class"] == c
                           and CAPTURE_ALIASES[r["capture_type"]] == cap for r in rows):
                    missing_cov.append(f"{c} x {cap} missing from {s}")

    # Near-duplicate base documents: full printed text (header with the sample ID removed),
    # narrative fields only, and structured values only.
    bases = sorted(split_of)
    full = {b: norm_text(strip_header(pdf_text(base_pdf(b)))) for b in bases}
    narr = {b: " ".join(load_json(base_json(b))[f] for f in sorted(NARRATIVE_FIELDS)) for b in bases}
    vals = {b: " | ".join(str(load_json(base_json(b))[f]) for f in FIELDS_27) for b in bases}
    sims_full, sims_narr, sims_vals, cross_pairs = [], [], [], []
    cross_narr_above = cross_vals_above = 0
    for a, b in itertools.combinations(bases, 2):
        sf = fuzz.ratio(full[a], full[b]) / 100
        sn = fuzz.ratio(narr[a], narr[b]) / 100
        sv = fuzz.ratio(vals[a], vals[b]) / 100
        sims_full.append(sf)
        sims_narr.append(sn)
        sims_vals.append(sv)
        if split_of[a] != split_of[b]:
            cross_narr_above += sn > NEAR_DUP
            cross_vals_above += sv > NEAR_DUP
        if split_of[a] != split_of[b] and sf > NEAR_DUP:
            cross_pairs.append({"a": a, "a_split": split_of[a], "b": b, "b_split": split_of[b],
                                "full_text_sim": round(sf, 4), "narrative_sim": round(sn, 4),
                                "values_sim": round(sv, 4)})
    n_cross_total = sum(1 for a, b in itertools.combinations(bases, 2) if split_of[a] != split_of[b])

    # Exact narrative strings shared across splits (after masking the exhibit ID).
    def mask(s: str) -> str:
        import re
        return re.sub(r"EXHIBIT-SYN-[A-Z0-9]+", "<ID>", s)
    narr_split: dict[str, set[str]] = defaultdict(set)
    for b in bases:
        narr_split[mask(narr[b])].add(split_of[b])
    shared_narr = sum(1 for v in narr_split.values() if len(v) > 1)

    # Do the tampered replacement values themselves repeat across splits? If every E1 sample
    # inserts the same name, a model can learn the string rather than the change.
    replacement_by_class: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["capture_type"] != "digital" or r["tamper_class"] in ("E0", "E15") \
                or r["sample_id"] == r["original_id"]:
            continue
        new = load_json(sidecar_json(r))
        old = load_json(base_json(r["original_id"]))
        for f in FIELDS_27:
            if new[f] != old[f]:
                val = new[f].replace(old[f], "<ORIG>") if f in NARRATIVE_FIELDS else new[f]
                replacement_by_class[r["tamper_class"]][mask(val)].add(r["split"])
    replacement_values = {c: {"distinct_new_values": len(v),
                              "values_in_all_three_splits": sum(1 for s in v.values() if len(s) == 3)}
                          for c, v in sorted(replacement_by_class.items(), key=lambda x: int(x[0][1:]))}

    result = {
        "base_documents": nb,
        "leaking_bases": leaking,
        "ratios": ratios,
        "coverage_gaps_val_test": missing_cov,
        "near_duplicate_threshold": NEAR_DUP,
        "cross_split_base_pairs_total": n_cross_total,
        "cross_split_pairs_above_threshold": len(cross_pairs),
        "full_text_similarity_all_pairs": {"min": round(min(sims_full), 4), "mean": round(sum(sims_full) / len(sims_full), 4),
                                           "max": round(max(sims_full), 4)},
        "cross_split_pairs_narrative_above_threshold": cross_narr_above,
        "cross_split_pairs_values_above_threshold": cross_vals_above,
        "values_only_similarity_all_pairs": {"min": round(min(sims_vals), 4), "mean": round(sum(sims_vals) / len(sims_vals), 4),
                                             "max": round(max(sims_vals), 4)},
        "narrative_similarity_all_pairs": {"min": round(min(sims_narr), 4), "mean": round(sum(sims_narr) / len(sims_narr), 4),
                                           "max": round(max(sims_narr), 4)},
        "distinct_narratives_after_masking_ids": len(narr_split),
        "narratives_shared_across_splits": shared_narr,
        "replacement_values_per_class": replacement_values,
        "cross_split_pairs": cross_pairs,
    }
    write_json("step4_splits.json", result)
    print(f"leaking={len(leaking)} ratios={ {s: (v['bases'], v['samples_pct']) for s, v in ratios.items()} }")
    print(f"near-dup cross pairs {len(cross_pairs)}/{n_cross_total}", result["full_text_similarity_all_pairs"],
          result["narrative_similarity_all_pairs"], result["values_only_similarity_all_pairs"],
          "narr cross >0.9", cross_narr_above, "vals cross >0.9", cross_vals_above, "distinct narratives", len(narr_split))
    print(replacement_values)
    print(missing_cov[:10])
    return result


if __name__ == "__main__":
    main()
