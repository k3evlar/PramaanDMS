"""Quality checks for a built FIR-Tamper dataset.

Usage:
    .venv/Scripts/python -m ml.data.generator.check --data dataset

Writes dataset/qa/report.md and dataset/qa/recheck_10pct.csv. Exits non-zero if
any check fails.

Checks:
1. Text-layer check (independent of how labels were computed): read the text of
   every vector digital PDF and confirm that the values the label says are present
   are printed, and that changed or redacted old values are gone.
2. No real personal data: phone numbers, vehicle numbers, names, e-mails, URLs.
3. Coverage: every class in every split; share of untouched or format-only samples.
4. Split leakage: each base document is in exactly one split.
5. A random 10% of samples for a second person to re-check by hand.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium

from . import fakedata as fd
from .model import FIELD_SPECS, Style, fmt_sections, fmt_value
from .render import FOOTER
from .tamper import BY_CODE, CLASSES

PHONE_REAL = re.compile(r"(?<![\d+])[6-9]\d{9}(?!\d)")
VEHICLE = re.compile(r"\b([A-Z]{2})[ -]?\d{2}[ -]?[A-Z]{2}[ -]?\d{4}\b")
EMAIL_URL = re.compile(r"[\w.+-]+@[\w-]+\.\w+|https?://|www\.", re.I)
ALLOWED_NAME_TOKENS = ({t.casefold() for t in fd.MALE_FIRST + fd.FEMALE_FIRST + fd.SURNAMES}
                       | {"shri", "smt"})


def pdf_text(path: Path) -> str:
    doc = pdfium.PdfDocument(str(path))
    try:
        parts = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    finally:
        doc.close()
    text = " ".join(parts)
    text = re.sub(re.escape(FOOTER) + r"\s+Page \d+", " ", text)
    return " ".join(text.split())


def _style(d: dict[str, Any]) -> Style:
    d = dict(d)
    if d.get("section_order") is not None:
        d["section_order"] = tuple(d["section_order"])
    return Style(**d)


def _tuple_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {k: tuple(v) if isinstance(v, list) else v for k, v in fields.items()}


def displays(fields: dict[str, Any], style: Style, redacted: set[str]) -> dict[str, str]:
    """Box key -> printed text, for every field value in a variant."""
    out: dict[str, str] = {}
    for key, val in fields.items():
        spec = FIELD_SPECS[key]
        if spec.ftype == "section":
            out[key] = fmt_sections(val, style)
        elif spec.is_list:
            for i, x in enumerate(val):
                bk = f"{key}[{i}]"
                if bk not in redacted:
                    out[bk] = fmt_value(spec.ftype, key, x, style)
        else:
            out[key] = fmt_value(spec.ftype, key, val, style)
    return out


def text_layer_check(data: Path, versions: list[dict[str, Any]]) -> tuple[int, list[str]]:
    checked, failures = 0, []
    base_cache: dict[str, dict[str, Any]] = {}
    for v in versions:
        if v["group"] == "blur":
            continue  # blurred versions are image-only PDFs
        text = pdf_text(data / v["files"]["digital"])
        var = v["variant"]
        style = _style(var["style"])
        fields = _tuple_fields(var["fields"])
        disp = displays(fields, style, set(var["redacted"]))
        page_edit = v["group"] == "page"
        checked += 1
        if not page_edit:
            for bk, s in disp.items():
                if s not in text:
                    failures.append(f"{v['version_id']} {v['tamper_class']}: missing {bk}={s!r}")
            for sen in var["narrative"]:
                if sen not in text:
                    failures.append(f"{v['version_id']} {v['tamper_class']}: missing sentence {sen[:50]!r}")
        all_new = " | ".join(list(disp.values()) + var["narrative"])
        oid = v["original_id"]
        if oid not in base_cache:
            base_cache[oid] = json.loads((data / "base_docs" / f"{oid}.json").read_text(encoding="utf-8"))
        base = base_cache[oid]
        for c in v["changes"]:
            if c["kind"] in ("field_changed", "field_removed") and c["key"] in FIELD_SPECS and c["old"] is not None:
                spec = FIELD_SPECS[c["key"]]
                if spec.ftype == "section":
                    olds = [fmt_sections(tuple(c["old"]), style)]
                elif spec.is_list:
                    olds = [fmt_value(spec.ftype, c["key"], x, style)
                            for x in (c["old"] if isinstance(c["old"], list) else [c["old"]])]
                    newv = c["new"] if isinstance(c["new"], list) else []
                    olds = [o for o, raw in zip(olds, c["old"] if isinstance(c["old"], list) else [c["old"]])
                            if raw not in newv]
                else:
                    olds = [fmt_value(spec.ftype, c["key"], c["old"], style)]
                for o in olds:
                    if o in text and o not in all_new:
                        failures.append(f"{v['version_id']} {v['tamper_class']}: old value still printed {c['key']}={o!r}")
        if v["group"] == "narrative":
            # Original sentences that the label says changed or were removed must be gone.
            vstyle_base = base["narrative"] if base["style"] == var["style"] else None
            if vstyle_base is not None:
                for c in v["changes"]:
                    if c["kind"] in ("narrative_changed", "narrative_removed") and isinstance(c["old"], str) \
                            and c["old"].startswith("sentence "):
                        idx = int(c["old"].split()[1]) - 1
                        old_sen = vstyle_base[idx]
                        # An edit can keep the old sentence as part of the new one ("I know X" ->
                        # "I think I know X"); only a stand-alone old sentence is a failure.
                        inside_new = any(old_sen in ns for ns in var["narrative"])
                        if old_sen in text and old_sen not in var["narrative"] and not inside_new:
                            failures.append(f"{v['version_id']} {v['tamper_class']}: old sentence still printed {old_sen[:50]!r}")
    return checked, failures


def pii_check(data: Path, versions: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    seen_pdfs = set()
    for v in versions:
        if v["group"] == "blur":
            continue
        p = v["files"]["digital"]
        if p in seen_pdfs:
            continue
        seen_pdfs.add(p)
        text = pdf_text(data / p)
        for m in PHONE_REAL.findall(text):
            problems.append(f"{p}: number that looks like a real mobile number: {m}")
        for m in VEHICLE.finditer(text):
            if m.group(1) != "ZZ":
                problems.append(f"{p}: vehicle number with a real-looking state code: {m.group(0)}")
        if EMAIL_URL.search(text):
            problems.append(f"{p}: e-mail address or URL found")
        for key, val in v["variant"]["fields"].items():
            if FIELD_SPECS[key].ftype != "name":
                continue
            for name in (val if isinstance(val, list) else [val]):
                bad = [t for t in name.split() if t.casefold() not in ALLOWED_NAME_TOKENS]
                if bad:
                    problems.append(f"{p}: name token not from the invented lists: {bad}")
        for ph in v["variant"]["fields"].get("phone_numbers", []):
            if not ph.startswith("10"):
                problems.append(f"{p}: phone number not in the 10 prefix: {ph}")
    return problems


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("dataset"))
    ap.add_argument("--recheck-seed", type=int, default=7)
    a = ap.parse_args(argv)
    data = a.data
    lab = json.loads((data / "labels.json").read_text(encoding="utf-8"))
    versions = lab["versions"]
    with open(data / "labels.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    report: list[str] = ["# FIR-Tamper QA report", "",
                         f"Seed: {lab['seed']}. Versions: {len(versions)}. Samples: {len(rows)}.", ""]
    ok = True

    # 1. Declared vs computed labels (repeated here from the build, on the saved labels)
    bad_decl = []
    for v in versions:
        cls = BY_CODE[v["tamper_class"]]
        exp_v = cls.expected_verdict or "Equivalent"
        if v["verdict_capture"] != exp_v or (cls.expected_severity and v["severity"] != cls.expected_severity):
            bad_decl.append(v["version_id"])
    report += ["## 1. Labels agree with class declarations", "",
               f"Mismatches: {len(bad_decl)}", ""]
    ok &= not bad_decl

    # 2. Text layer
    checked, failures = text_layer_check(data, versions)
    report += ["## 2. Text-layer check of digital PDFs", "",
               f"Versions checked: {checked} (blurred versions are image-only and are skipped). Failures: {len(failures)}.", ""]
    report += [f"- {x}" for x in failures[:50]] + ([""] if failures else [])
    ok &= not failures

    # 3. Personal data
    pii = pii_check(data, versions)
    report += ["## 3. No real personal data", "",
               "Checked: no 10-digit numbers starting 6 to 9, every vehicle number uses the invented ZZ code, "
               "no e-mail addresses or URLs, every name token comes from the invented lists, every phone number starts with 10.", "",
               f"Problems: {len(pii)}", ""]
    report += [f"- {x}" for x in pii[:50]] + ([""] if pii else [])
    ok &= not pii

    # 4. Split leakage
    split_of: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        split_of[r["original_id"]].add(r["split"])
    leaks = [k for k, s in split_of.items() if len(s) != 1]
    report += ["## 4. Split leakage", "", f"Base documents in more than one split: {len(leaks)}", ""]
    ok &= not leaks

    # 5. Coverage
    split_names = [s for s in ("train", "val", "test", "test_unseen") if any(r["split"] == s for r in rows)]
    vers_split = {s: Counter() for s in split_names}
    for v in versions:
        vers_split[v["split"]][v["tamper_class"]] += 1
    report += ["## 5. Coverage per class and split", "",
               "Counts are versions (samples = versions x 3 capture types).", "",
               "| Class | Group | Worked example | Decision | Expected verdict | " + " | ".join(split_names) + " |",
               "|---|---|---|---|---|" + "---|" * len(split_names)]
    missing, unused = [], []
    for c in CLASSES:
        cnt = [vers_split[s][c.code] for s in split_names]
        if max(cnt) == 0:
            unused.append(c.code)  # not planned in this build (for example N_ENTITY in the E-class plan)
            continue
        if min(cnt) == 0:
            missing.append(c.code)
        exp = c.expected_verdict or "Identical (digital) / Equivalent (scan, photo)"
        sev = f", {c.expected_severity}" if c.expected_severity not in (None, "None") else ""
        report.append(f"| {c.code} | {c.group} | {c.worked_example} | {c.rule_ref or '-'} | {exp}{sev} | "
                      + " | ".join(str(x) for x in cnt) + " |")
    report += ["", f"Classes missing from a split: {missing or 'none'}",
               f"Classes not used in this build: {unused or 'none'}", ""]
    ok &= not missing
    neg = sum(1 for r in rows if BY_CODE[r["tamper_class"]].group in ("none", "format"))
    frac = neg / len(rows)
    report += [f"Untouched or format-only samples: {neg} of {len(rows)} ({frac:.1%}). Target: about one third.", ""]
    verdicts = Counter(r["expected_verdict"] for r in rows)
    report += ["Expected verdicts over all samples: " + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())), ""]

    # 6. Random 10% for a second person
    rng = random.Random(a.recheck_seed)
    pick = sorted(rng.sample(range(len(rows)), k=max(1, round(len(rows) * 0.10))))
    qa = data / "qa"
    qa.mkdir(exist_ok=True)
    with open(qa / "recheck_10pct.csv", "w", newline="", encoding="utf-8") as f:
        cols = list(rows[0].keys()) + ["reviewer", "reviewer_verdict", "agrees_with_label", "notes"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i in pick:
            w.writerow({**rows[i], "reviewer": "", "reviewer_verdict": "", "agrees_with_label": "", "notes": ""})
    report += ["## 6. Second-person re-check", "",
               f"{len(pick)} samples ({len(pick) / len(rows):.0%}) picked at random (seed {a.recheck_seed}) into "
               "`qa/recheck_10pct.csv`. Status: NOT DONE. A second person must open each file, compare it with "
               "the base document, and fill in the reviewer columns.", ""]

    report.insert(3, f"Overall automated result: {'PASS' if ok else 'FAIL'}\n")
    (qa / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report[:6]))
    print(f"failures: decl={len(bad_decl)} text={len(failures)} pii={len(pii)} leaks={len(leaks)} missing={missing}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
