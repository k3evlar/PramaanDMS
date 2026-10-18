"""Step 2: validate every label row against the label schema and the verdict rules."""
from __future__ import annotations

from collections import Counter, defaultdict

from audit_lib import (ALLOWED, CAPTURE_ALIASES, CLASS_ALLOWED_FIELDS, DATASET, FIELDS_27,
                       HARMLESS_CLASSES, REQUIRED_COLUMNS, base_json, base_pdf, label_rows,
                       labels, load_json, read_csv, sha256, sidecar_json, source_sample_id,
                       target_verdict, write_json)


def main() -> dict:
    header, rows = labels()
    violations: list[dict] = []

    def bad(row_id: str, rule: str, detail: str) -> None:
        violations.append({"row_id": row_id, "rule": rule, "detail": detail})

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in header]
    for c in missing_cols:
        bad("<header>", "missing_column", c)
    # The brief also asks for an explicit path to the base/original document.
    has_original_path_col = any(c in header for c in ("original_path", "base_path", "original_file_path"))

    seen: Counter = Counter(r["sample_id"] for r in rows)
    for sid, n in seen.items():
        if n > 1:
            bad(sid, "duplicate_sample_id", f"appears {n} times")

    base_types: dict[str, set[str]] = defaultdict(set)
    sha_cache: dict[str, str] = {}
    for i, r in enumerate(rows, start=2):  # csv line number
        sid = r.get("sample_id") or f"line{i}"
        for c in REQUIRED_COLUMNS:
            if c in header and not (r.get(c) or "").strip():
                bad(sid, "empty_required_value", c)
        for col, allowed in ALLOWED.items():
            v = r.get(col, "")
            if v and v not in allowed:
                bad(sid, f"value_not_allowed:{col}", f"{v!r} not in {sorted(allowed)}")
        if not (r.get("page_affected") or "").strip().isdigit():
            bad(sid, "page_affected_not_integer", repr(r.get("page_affected")))
        if not base_pdf(r["original_id"]).is_file():
            bad(sid, "original_not_found", f"no base_docs/{r['original_id']}.pdf")
        base_types[r["original_id"]].add(r["doc_type"])

        cls, sev, ver = r["tamper_class"], r["severity"], r["expected_verdict"]
        # Verdict rule: harmless classes must never be Tampered, material ones never Valid.
        if cls in HARMLESS_CLASSES and ver != "Valid":
            bad(sid, "verdict_vs_class", f"{cls} labelled {ver}")
        if cls not in HARMLESS_CLASSES and ver == "Valid":
            bad(sid, "verdict_vs_class", f"{cls} labelled Valid")
        # Severity rule (SCOPE.md section 8): E0 -> None/Format, E1-E15 -> Major/Minor.
        if cls in HARMLESS_CLASSES and sev not in {"None", "Format"}:
            bad(sid, "severity_vs_class", f"{cls} severity {sev}")
        if cls not in HARMLESS_CLASSES and sev not in {"Major", "Minor"}:
            bad(sid, "severity_vs_class", f"{cls} severity {sev}")

        # field_changed must be inside the class definition and agree with the JSON diff.
        if r["capture_type"] == "digital" and cls != "E0":
            listed = {x.strip() for x in r["field_changed"].split(";") if x.strip()}
            allowed = CLASS_ALLOWED_FIELDS[cls]
            if cls == "E15":
                if not any(x in r["field_changed"] for x in ("signature", "seal")):
                    bad(sid, "field_changed_vs_class", r["field_changed"])
            elif not listed or not listed <= allowed:
                bad(sid, "field_changed_vs_class", f"{sorted(listed)} not within {sorted(allowed)}")
            actual = load_json(sidecar_json(r))
            original = load_json(base_json(r["original_id"]))
            changed = {k for k in FIELDS_27 if actual.get(k) != original.get(k)}
            if cls != "E15" and changed != listed:
                bad(sid, "field_changed_vs_json_diff", f"label {sorted(listed)} json {sorted(changed)}")
            if cls == "E15" and changed:
                bad(sid, "field_changed_vs_json_diff", f"E15 changed fields {sorted(changed)}")

    for base, types in base_types.items():
        if len(types) > 1:
            bad(base, "doc_type_inconsistent_within_base", str(sorted(types)))

    # Capture rows must inherit their source row's labels.
    by_id = {r["sample_id"]: r for r in rows}
    for r in rows:
        if r["capture_type"] == "digital":
            continue
        src = by_id.get(source_sample_id(r["sample_id"]))
        if src is None:
            bad(r["sample_id"], "capture_source_missing", source_sample_id(r["sample_id"]))
            continue
        for c in ("original_id", "doc_type", "tamper_class", "field_changed", "severity",
                  "expected_verdict", "split"):
            if r[c] != src[c]:
                bad(r["sample_id"], "capture_label_mismatch", f"{c}: {r[c]!r} vs {src[c]!r}")

    # change_log.csv must agree with labels.csv.
    _, change_log = read_csv(DATASET / "annotations" / "change_log.csv")
    for c in change_log:
        r = by_id.get(c["sample_id"])
        if r is None:
            continue
        for col in ("tamper_class", "field_changed", "severity", "expected_verdict", "original_id"):
            if c[col] != r[col]:
                bad(c["sample_id"], "change_log_mismatch", f"{col}: {c[col]!r} vs {r[col]!r}")
    review_status = Counter(c["review_status"] for c in change_log)

    # splits.csv must agree with labels.csv.
    _, split_rows = read_csv(DATASET / "splits.csv")
    split_map = {s["original_id"]: s for s in split_rows}
    for r in rows:
        s = split_map.get(r["original_id"])
        if s is None:
            bad(r["sample_id"], "split_map_missing", r["original_id"])
        elif s["split"] != r["split"] or s["doc_type"] != r["doc_type"]:
            bad(r["sample_id"], "split_map_mismatch", f"{s} vs {r['split']}/{r['doc_type']}")

    # Mapping to the 3-level target verdict. Identical needs byte equality with the original.
    target = Counter()
    identical_pairs = 0
    for r in rows:
        if r["capture_type"] != "digital":
            ident = False
        else:
            a, b = str(base_pdf(r["original_id"])), str(DATASET.parent / r["file_path"])
            sha_cache.setdefault(a, sha256(base_pdf(r["original_id"])))
            sha_cache.setdefault(b, sha256(DATASET.parent / r["file_path"]))
            ident = sha_cache[a] == sha_cache[b]
        is_self = r["sample_id"] == r["original_id"]
        if ident and not is_self:
            identical_pairs += 1
        tv = "Original (anchor)" if is_self else target_verdict(r, ident)
        target[tv] += 1

    rule_counts = Counter(v["rule"] for v in violations)
    result = {
        "rows_checked": len(rows),
        "missing_columns": missing_cols,
        "has_explicit_original_path_column": has_original_path_col,
        "violation_count": len(violations),
        "violations_by_rule": dict(rule_counts.most_common()),
        "value_counts": {c: dict(Counter(r[c] for r in rows)) for c in
                         ("severity", "expected_verdict", "capture_type", "split")},
        "page_affected_values": dict(Counter(r["page_affected"] for r in rows)),
        "change_log_review_status": dict(review_status),
        "target_verdict_counts": dict(target),
        "byte_identical_non_self_pairs": identical_pairs,
        "violations": violations,
    }
    write_json("step2_schema.json", result)
    print(f"violations={len(violations)}", dict(rule_counts.most_common()))
    print("target verdicts", dict(target))
    return result


if __name__ == "__main__":
    main()
