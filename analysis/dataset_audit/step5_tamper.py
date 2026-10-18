"""Step 5: tamper correctness. Every original vs digital variant pair is checked
(not only a sample), and 5 random pairs per class are kept as report examples.

Checks per pair:
  * structured diff (JSON sidecar vs base JSON) stays inside the class definition
  * the new value is actually printed in the PDF text layer
  * printed text outside the changed fields is identical once the header is removed
  * a class-specific semantic check (a negation flip really flips a negation, ...)
  * the printed header (sample ID, class note) is reported separately as label leakage
"""
from __future__ import annotations

import difflib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date

from audit_lib import (CLASS_ALLOWED_FIELDS, CLASSES, DATASET, FIELDS_27, NARRATIVE_FIELDS, SEED,
                       base_json, base_pdf, label_rows, load_json, norm_text, pdf_meta, pdf_text,
                       read_csv, sidecar_json, source_pdf, strip_header, write_json)

NAME_FIELDS = CLASS_ALLOWED_FIELDS["E1"]
DATE_FIELDS = CLASS_ALLOWED_FIELDS["E2"]
NEGATIONS = {"not", "no", "never", "none", "nobody", "nothing", "neither", "nor", "n't", "without"}
MODALS_QUANTS = {"may", "might", "shall", "should", "must", "will", "would", "can", "could",
                 "some", "all", "any", "none", "few", "many", "every", "each", "most", "several",
                 "always", "never", "sometimes", "certainly", "possibly", "probably"}
AMOUNT_RE = re.compile(r"^Rs\.?\s?[\d,]+(\.\d+)?(/-)?$")
TIME_RE = re.compile(r"^(0?[1-9]|1[0-2]):[0-5]\d (AM|PM)$|^([01]\d|2[0-3]):[0-5]\d$")


def toks(s: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9'-]+|[.;,]", s)


def token_ops(old: str, new: str) -> list[tuple[str, list[str], list[str]]]:
    a, b = toks(old), toks(new)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]


def is_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def semantic_check(cls: str, old: dict, new: dict, changed: set[str], new_pdf_meta: dict,
                   base_meta: dict, change_row: dict, header_free_diff: list[str]) -> tuple[bool, str]:
    """Return (pass, reason). The reason explains a failure or notes a caveat on a pass."""
    if cls == "E0":
        if changed:
            return False, f"structured fields changed: {sorted(changed)}"
        if header_free_diff:
            return False, f"printed content differs: {header_free_diff[:2]}"
        return True, "content identical; only header differs"
    if cls == "E15":
        if changed:
            return False, f"structured fields changed: {sorted(changed)}"
        seal_lines = [l for l in header_free_diff if "SEAL" in l.upper()]
        if any("E15" in l for l in seal_lines):
            return False, ("seal change is a printed text swap that spells out the class "
                           f"('{norm_text(seal_lines[-1][1:])}'); no signature or seal image is altered")
        return (bool(seal_lines), "seal region changed" if seal_lines else "no visible seal change")
    if not changed:
        return False, "no structured change"
    if not changed <= CLASS_ALLOWED_FIELDS[cls]:
        return False, f"fields {sorted(changed)} outside class definition"

    if cls == "E1":
        f = next(iter(changed))
        if len(changed) != 1:
            return False, "more than one name changed"
        others = {new[x] for x in NAME_FIELDS if x != f}
        if new[f] in others:
            return False, "new name duplicates another party (role confusion, not substitution)"
        return True, f"{f}: {old[f]!r} -> {new[f]!r}"
    if cls == "E2":
        f = next(iter(changed))
        ok = len(changed) == 1 and is_date(old[f]) and is_date(new[f])
        return ok, f"{f}: {old[f]} -> {new[f]}"
    if cls == "E3":
        ok = TIME_RE.match(new["incident_time"]) is not None
        return ok, f"incident_time: {old['incident_time']} -> {new['incident_time']}"
    if cls == "E4":
        o, n = old["monetary_amount"], new["monetary_amount"]
        if not AMOUNT_RE.match(o):
            return False, f"original has no amount ({o!r}); edit inserts an amount instead of changing one"
        return bool(AMOUNT_RE.match(n)), f"{o} -> {n}"
    if cls == "E5":
        return True, f"{old['act_name']} {old['section_number']} -> {new['act_name']} {new['section_number']}"
    if cls == "E6":
        f = next(iter(changed & NARRATIVE_FIELDS))
        ops = token_ops(old[f], new[f])
        if len(ops) == 1 and ops[0][0] in ("insert", "delete") \
                and {t.lower() for t in ops[0][1] + ops[0][2]} <= NEGATIONS:
            return True, f"negation {ops[0][0]}: {ops[0][2] or ops[0][1]}"
        return False, f"diff is not a single negation token: {ops}"
    if cls == "E7":
        ok = (new["complainant_name"] == old["accused_name"]
              and new["accused_name"] == old["complainant_name"])
        return ok, "complainant and accused swapped" if ok else "not a clean swap"
    if cls in ("E8", "E9", "E13"):
        notes = []
        if cls == "E8" and new["incident_location"] != new["jurisdiction"] \
                and old["incident_location"] == old["jurisdiction"]:
            notes.append("narrative and jurisdiction still name the old place")
        if cls == "E9" and old["evidence_item_id"] in new["evidence_description"]:
            notes.append("evidence_description still cites the old exhibit ID")
        f = sorted(changed)[0]
        return True, f"{f}: {old[f]!r} -> {new[f]!r}" + (f" ({'; '.join(notes)})" if notes else "")
    if cls == "E10":
        f = next(iter(changed))
        ops = token_ops(old[f], new[f])
        ok = all(op == "insert" for op, _, _ in ops) and sum(len(b) for _, _, b in ops) >= 4
        return ok, f"inserted: {' '.join(sum((b for _, _, b in ops), []))!r}"
    if cls == "E11":
        f = next(iter(changed))
        ops = token_ops(old[f], new[f])
        if all(op == "delete" for op, _, _ in ops):
            return True, f"deleted: {' '.join(sum((a for _, a, _ in ops), []))!r}"
        added = sorted({t for _, _, b in ops for t in b})
        return False, f"rewrite, not a deletion: new words {added} were added ({new[f]!r})"
    if cls == "E12":
        f = next(iter(changed))
        ops = token_ops(old[f], new[f])
        if len(ops) == 1 and ops[0][0] == "replace" and len(ops[0][1]) == len(ops[0][2]) == 1 \
                and ops[0][1][0].lower() in MODALS_QUANTS and ops[0][2][0].lower() in MODALS_QUANTS:
            return True, f"{ops[0][1][0]} -> {ops[0][2][0]}"
        inserted = " ".join(sum((b for _, _, b in ops), []))
        return False, f"a whole sentence was appended (clause insertion, same as E10): {inserted!r}"
    if cls == "E14":
        moved_earlier = all(new[f] < old[f] for f in changed)
        meta_changed = {k: (base_meta.get(k), new_pdf_meta.get(k)) for k in ("CreationDate", "ModDate")
                        if (base_meta.get(k) or "")[2:10] != (new_pdf_meta.get(k) or "")[2:10]}
        log_has_meta = "meta" in (change_row.get("original_value", "") + change_row.get("modified_value", "")).lower()
        if not moved_earlier:
            return False, "dates not moved earlier"
        if not meta_changed and not log_has_meta:
            return False, ("printed dates moved earlier, but no file metadata was changed or logged; "
                           "this is a two-date E2 edit, not the metadata inconsistency E14 defines")
        return True, "dates backdated with metadata inconsistency"
    return True, ""


def main() -> dict:
    rows = [r for r in label_rows() if r["capture_type"] == "digital" and r["sample_id"] != r["original_id"]]
    _, change_log = read_csv(DATASET / "annotations" / "change_log.csv")
    log_by_id = {c["sample_id"]: c for c in change_log}

    per_class: dict[str, dict] = {c: {"checked": 0, "pass": 0, "fail": 0, "failures": [], "notes": Counter()}
                                  for c in CLASSES}
    header_leak = 0
    critical_change_in_harmless: list[str] = []
    printed_mismatch: list[str] = []
    log_mismatch: list[str] = []
    all_pairs: dict[str, list[dict]] = defaultdict(list)
    base_meta_cache: dict[str, dict] = {}

    for r in rows:
        cls, sid, oid = r["tamper_class"], r["sample_id"], r["original_id"]
        old, new = load_json(base_json(oid)), load_json(sidecar_json(r))
        changed = {f for f in FIELDS_27 if old[f] != new[f]}
        t_old = pdf_text(base_pdf(oid)).splitlines()
        t_new = pdf_text(source_pdf(r)).splitlines()
        diff = [l for l in difflib.unified_diff(t_old, t_new, lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        header_lines = [l for l in diff if strip_header(l[1:]).strip() != l[1:].strip()]
        if header_lines:
            header_leak += 1
        h_old = [strip_header(l) for l in t_old]
        h_new = [strip_header(l) for l in t_new]
        hf_diff = [l for l in difflib.unified_diff(h_old, h_new, lineterm="", n=0)
                   if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        # Lines that changed but belong to no changed field (and are not the seal line).
        changed_vals = [str(new[f]) for f in changed] + [str(old[f]) for f in changed]
        stray = [l for l in hf_diff if l[1:].strip()
                 and not any(w in norm_text(" ".join(changed_vals)) for w in [norm_text(l[1:])])
                 and not any(norm_text(l[1:]).split(" ", 1)[-1] in norm_text(v) or norm_text(v) in norm_text(l[1:])
                             for v in changed_vals)
                 and "SEAL" not in l.upper()]

        page = norm_text(pdf_text(source_pdf(r)))
        for f in changed:
            if norm_text(str(new[f])) not in page:
                printed_mismatch.append(f"{sid}:{f}")

        c = log_by_id.get(sid, {})
        try:
            logged_new = json.loads(c.get("modified_value") or "{}")
        except json.JSONDecodeError:
            logged_new = {}
        for f in changed:
            if logged_new.get(f) != new[f]:
                log_mismatch.append(f"{sid}:{f}")

        if base_meta_cache.get(oid) is None:
            base_meta_cache[oid] = pdf_meta(base_pdf(oid))
        ok, reason = semantic_check(cls, old, new, changed, pdf_meta(source_pdf(r)),
                                    base_meta_cache[oid], c, hf_diff)
        if cls == "E0" and changed:
            critical_change_in_harmless.append(sid)
        pc = per_class[cls]
        pc["checked"] += 1
        pc["pass" if ok else "fail"] += 1
        if not ok:
            pc["failures"].append({"sample_id": sid, "reason": reason})
        if stray:
            pc["notes"]["changed printed lines outside the changed fields"] += 1
        all_pairs[cls].append({"sample_id": sid, "original_id": oid, "split": r["split"],
                               "fields_changed": sorted(changed),
                               "old": {f: old[f] for f in sorted(changed)},
                               "new": {f: new[f] for f in sorted(changed)},
                               "text_diff": diff, "pass": ok, "reason": reason})

    rng = random.Random(SEED)
    examples = {c: rng.sample(v, min(5, len(v))) for c, v in all_pairs.items()}
    summary = {}
    for c in CLASSES:
        pc = per_class[c]
        verdict = "PASS" if pc["fail"] == 0 else ("FAIL" if pc["pass"] == 0 else "PARTIAL")
        summary[c] = {"checked": pc["checked"], "pass": pc["pass"], "fail": pc["fail"], "verdict": verdict,
                      "first_failure": pc["failures"][0] if pc["failures"] else None,
                      "failure_ids": [f["sample_id"] for f in pc["failures"]],
                      "notes": dict(pc["notes"])}
    result = {
        "pairs_checked": len(rows),
        "per_class": summary,
        "pairs_with_header_label_leak": header_leak,
        "harmless_with_structured_change": critical_change_in_harmless,
        "new_value_not_printed": printed_mismatch,
        "change_log_vs_json_mismatch": log_mismatch,
        "examples": examples,
    }
    write_json("step5_tamper.json", result)
    for c in CLASSES:
        s = summary[c]
        print(c, s["verdict"], f"{s['pass']}/{s['checked']}",
              (s["first_failure"] or {}).get("reason", "")[:140])
    print("header leak pairs", header_leak, "printed mismatch", len(printed_mismatch),
          "log mismatch", len(log_mismatch))
    return result


if __name__ == "__main__":
    main()
