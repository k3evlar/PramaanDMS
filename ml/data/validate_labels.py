"""Validate a FIR-Tamper labels.csv against the locked tampering rules.

Usage (from the repo root):
    .venv/Scripts/python -m ml.data.validate_labels --data dataset
    .venv/Scripts/python -m ml.data.validate_labels --data dataset --report out/validation.md \
        --sample-out out/recheck_10pct.csv
    .venv/Scripts/python -m ml.data.validate_labels --data dataset --no-hashes   # skip SHA-256 work

It only reads the dataset. Reports and the human re-check sample are written only to the
paths you give. Exit code 0 when there are no errors, 1 when there are errors, 2 when the
input cannot be read.

Checks (each finding has a code, so a report can be traced back to a rule):
  SCHEMA   required columns present; sample IDs unique
  VALUE    allowed values for doc type, capture, verdict, severity, split, pages; old
           terms ("Altered", "Critical") rejected; no Devanagari text (D39)
  SEV      Tampered has Major or Minor; every other verdict has severity None
  D41      a clear edit (content_changed=yes) must be Tampered, never Inconclusive or
           Equivalent; Inconclusive needs a "could not verify" list and no clear edit
  D43      page changes are Major
  VIS      stamp, seal and signature changes are Major
  D46      a flagged annotation belongs to a Tampered verdict
  D47      a redacted sample is "Not supported"
  IDENT    Identical only for a digital capture with nothing changed
  TASK     task_verdict agrees with expected_verdict
  CLASS    rows whose tamper_class is in the generator's class table match that class
  VERSION  the captures of one version agree (class, severity, changes, verdict)
  SPLIT    each base document is in exactly one split; ratios near 70/15/15; split files agree
  FILE     every listed file exists
  HASH     split hashes in manifest.json match the files on disk
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .generator.tamper import BY_CODE

REQUIRED = ["sample_id", "doc_type", "original_id", "tamper_class", "field_changed", "page_affected",
            "severity", "expected_verdict", "capture_type", "split", "files"]
DOC_TYPES = {"FIR", "STATEMENT", "CHARGESHEET"}
CAPTURES = {"digital", "scan_sim", "photo_sim", "scan_real", "photo_real"}
VERDICTS = {"Identical", "Equivalent", "Tampered", "Inconclusive", "Not supported"}
SEVERITIES = {"Major", "Minor", "None"}
SPLITS = ("train", "val", "test", "test_unseen")
# Ratios are checked over the seen splits only; test_unseen holds extra held-out bases (D96).
SEEN_SPLITS = ("train", "val", "test")
TARGET_RATIO = {"train": 0.70, "val": 0.15, "test": 0.15}
TASK_VERDICT = {"Identical": "Valid", "Equivalent": "Valid", "Tampered": "Tampered",
                "Inconclusive": "Inconclusive", "Not supported": "Not supported"}
OLD_TERMS = {"Altered": "Tampered", "Critical": "Major"}
DEVANAGARI = re.compile("[ऀ-ॿ]")


@dataclass
class Finding:
    level: str  # "error" or "warning"
    code: str
    where: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    stats: dict[str, object] = field(default_factory=dict)

    def error(self, code: str, where: str, message: str) -> None:
        self.findings.append(Finding("error", code, where, message))

    def warn(self, code: str, where: str, message: str) -> None:
        self.findings.append(Finding("warning", code, where, message))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    def to_markdown(self, limit: int = 200) -> str:
        counts = Counter((f.level, f.code) for f in self.findings)
        lines = ["# Label validation report", "",
                 f"Result: **{'PASS' if not self.errors else 'FAIL'}** "
                 f"({len(self.errors)} errors, {len(self.findings) - len(self.errors)} warnings)", ""]
        for k, v in self.stats.items():
            lines.append(f"- {k}: {v}")
        if counts:
            lines += ["", "| Level | Code | Count |", "|---|---|---|"]
            for (level, code), n in sorted(counts.items()):
                lines.append(f"| {level} | {code} | {n} |")
        if self.findings:
            lines += ["", "## Findings", ""]
            for f in self.findings[:limit]:
                lines.append(f"- {f.level} {f.code} [{f.where}]: {f.message}")
            if len(self.findings) > limit:
                lines.append(f"- ... {len(self.findings) - limit} more")
        return "\n".join(lines) + "\n"


def _yes(v: str | None) -> bool | None:
    if v is None or v == "":
        return None
    return v.strip().lower() == "yes"


def _check_row(r: dict[str, str], rep: Report) -> None:
    sid = r["sample_id"]
    verdict, sev, cap = r["expected_verdict"], r["severity"], r["capture_type"]
    for col, value in r.items():
        if value and DEVANAGARI.search(value):
            rep.error("VALUE", sid, f"Devanagari text in column {col} (English only, D39)")
    if verdict in OLD_TERMS or sev in OLD_TERMS:
        old = verdict if verdict in OLD_TERMS else sev
        rep.error("VALUE", sid, f"old term '{old}': relabel as '{OLD_TERMS[old]}' (D49)")
        return
    if r["doc_type"] not in DOC_TYPES:
        rep.error("VALUE", sid, f"unknown doc_type {r['doc_type']!r}")
    if cap not in CAPTURES:
        rep.error("VALUE", sid, f"unknown capture_type {cap!r}")
    if verdict not in VERDICTS:
        rep.error("VALUE", sid, f"unknown expected_verdict {verdict!r}")
        return
    if sev not in SEVERITIES:
        rep.error("VALUE", sid, f"unknown severity {sev!r}")
        return
    if r["split"] not in SPLITS:
        rep.error("VALUE", sid, f"unknown split {r['split']!r}")
    pages = r["page_affected"]
    if pages and not re.fullmatch(r"[1-9]\d*(;[1-9]\d*)*", pages):
        rep.error("VALUE", sid, f"page_affected must be page numbers separated by ';', got {pages!r}")

    changed = _yes(r.get("content_changed"))
    cnv = [x for x in (r.get("could_not_verify") or "").split(";") if x]
    flagged = _yes(r.get("flagged"))
    fields = [x for x in r["field_changed"].split(";") if x]

    if verdict == "Tampered" and sev not in ("Major", "Minor"):
        rep.error("SEV", sid, "Tampered needs severity Major or Minor")
    if verdict != "Tampered" and sev != "None":
        rep.error("SEV", sid, f"{verdict} must have severity None, got {sev}")
    if changed and verdict in ("Equivalent", "Inconclusive", "Identical"):
        rep.error("D41", sid, f"a clear edit exists (content_changed=yes) but the verdict is {verdict}; "
                              "a clear edit is always Tampered")
    if verdict == "Inconclusive":
        if "could_not_verify" in r and not cnv:
            rep.error("D41", sid, "Inconclusive needs at least one field in could_not_verify")
    if verdict == "Equivalent" and (changed or cnv):
        rep.error("D41", sid, "Equivalent cannot have a content change or unreadable fields")
    if verdict == "Tampered":
        if not fields:
            rep.error("SEV", sid, "Tampered needs field_changed")
        if changed is False:
            rep.error("SEV", sid, "Tampered but content_changed=no")
    if verdict == "Identical" and (cap != "digital" or changed or cnv):
        rep.error("IDENT", sid, "Identical is only for a digital, byte-identical copy with nothing changed")
    if any(f.startswith("page_") for f in fields) and verdict == "Tampered" and sev != "Major":
        rep.error("D43", sid, "a page added, removed or reordered is Major")
    if any(f.startswith(("stamp:", "sig:")) for f in fields) and verdict == "Tampered" and sev != "Major":
        rep.error("VIS", sid, "a stamp, seal or signature change is Major")
    if flagged and verdict != "Tampered":
        rep.error("D46", sid, "a flagged annotation must come with a Tampered verdict")
    if r["tamper_class"].upper().startswith("R_") and verdict != "Not supported":
        rep.error("D47", sid, "a redacted copy must be 'Not supported' (no verdict) in v1")
    tv = r.get("task_verdict")
    if tv and TASK_VERDICT.get(verdict) != tv:
        rep.error("TASK", sid, f"task_verdict {tv!r} does not match {verdict} (expected {TASK_VERDICT.get(verdict)!r})")

    cls = BY_CODE.get(r["tamper_class"])
    if cls is not None:
        if cls.code == "NONE":
            exp = "Identical" if cap == "digital" else "Equivalent"
        else:
            exp = cls.expected_verdict
        if verdict != exp:
            rep.error("CLASS", sid, f"{cls.code} should be {exp}, got {verdict}")
        if cls.expected_severity and sev != cls.expected_severity:
            rep.error("CLASS", sid, f"{cls.code} should have severity {cls.expected_severity}, got {sev}")
        if "rule_ref" in r and r["rule_ref"] != cls.rule_ref:
            rep.error("CLASS", sid, f"{cls.code} rule_ref should be {cls.rule_ref!r}, got {r['rule_ref']!r}")


def _check_versions(rows: list[dict[str, str]], rep: Report) -> None:
    by_version: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_version[r.get("version_id") or r["sample_id"].rsplit("-", 1)[0]].append(r)
    for vid, group in by_version.items():
        for col in ("tamper_class", "severity", "field_changed", "original_id", "split"):
            values = {g[col] for g in group}
            if len(values) > 1:
                rep.error("VERSION", vid, f"captures disagree on {col}: {sorted(values)}")
        verdicts = {g["expected_verdict"] for g in group}
        if len(verdicts) > 1 and verdicts != {"Identical", "Equivalent"}:
            rep.error("VERSION", vid, f"captures disagree on the verdict: {sorted(verdicts)}")


def _check_splits(data: Path, rows: list[dict[str, str]], rep: Report, tolerance: float) -> None:
    split_of: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        split_of[r["original_id"]].add(r["split"])
    for oid, splits in split_of.items():
        if len(splits) > 1:
            rep.error("SPLIT", oid, f"base document is in more than one split: {sorted(splits)} (leakage)")
    clean = {oid: next(iter(s)) for oid, s in split_of.items() if len(s) == 1}
    counts = Counter(clean.values())
    total = sum(counts.get(s, 0) for s in SEEN_SPLITS)
    rep.stats["base documents per split"] = ", ".join(f"{s} {counts.get(s, 0)}" for s in SPLITS if counts.get(s))
    if total:
        for s in SEEN_SPLITS:
            share = counts.get(s, 0) / total
            if abs(share - TARGET_RATIO[s]) > tolerance:
                rep.warn("SPLIT", s, f"{share:.0%} of base documents, target {TARGET_RATIO[s]:.0%} (+/- {tolerance:.0%})")
    for s in SPLITS:
        path = data / "splits" / f"{s}.txt"
        if path.is_file():
            listed = {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
            expected = {oid for oid, sp in clean.items() if sp == s}
            if listed != expected:
                rep.error("SPLIT", f"splits/{s}.txt", f"lists {len(listed)} documents but labels.csv has "
                                                      f"{len(expected)} in this split ({len(listed ^ expected)} differ)")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_files_and_hashes(data: Path, rows: list[dict[str, str]], rep: Report, hashes: bool) -> None:
    missing = 0
    for r in rows:
        for rel in [x for x in r["files"].split(";") if x]:
            if not (data / rel).is_file():
                missing += 1
                if missing <= 20:
                    rep.error("FILE", r["sample_id"], f"missing file {rel}")
    if missing > 20:
        rep.error("FILE", "labels.csv", f"{missing - 20} more missing files")
    manifest_path = data / "manifest.json"
    if not hashes or not manifest_path.is_file():
        rep.stats["split hashes"] = "not checked" if not hashes else "no manifest.json"
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded = manifest.get("files", {})
    split_files: dict[str, set[str]] = {s: set() for s in SPLITS}
    for r in rows:
        if r["split"] in split_files:
            split_files[r["split"]].update(x for x in r["files"].split(";") if x)
    for oid in {r["original_id"] for r in rows}:
        s = next(r["split"] for r in rows if r["original_id"] == oid)
        for extra in (f"base_docs/{oid}.pdf", f"base_docs/{oid}.json"):
            if (data / extra).is_file():
                split_files[s].add(extra)
    ok = 0
    for s, files in split_files.items():
        h = hashlib.sha256()
        for rel in sorted(files):
            if not (data / rel).is_file():
                continue
            actual = _sha256(data / rel)
            if rel in recorded and recorded[rel] != actual:
                rep.error("HASH", rel, "file content differs from manifest.json")
            h.update(f"{rel}:{actual}\n".encode())
        expected = manifest.get("split_hashes", {}).get(s)
        if expected and expected != h.hexdigest():
            rep.error("HASH", s, "split hash differs from manifest.json")
        elif expected:
            ok += 1
    rep.stats["split hashes matching manifest"] = f"{ok} of {sum(1 for f in split_files.values() if f)}"


def validate(data: Path, hashes: bool = True, tolerance: float = 0.05) -> tuple[Report, list[dict[str, str]]]:
    rep = Report()
    path = data / "labels.csv"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)
    missing_cols = [c for c in REQUIRED if c not in columns]
    if missing_cols:
        rep.error("SCHEMA", "labels.csv", f"missing columns: {missing_cols}")
        return rep, rows
    dupes = [k for k, n in Counter(r["sample_id"] for r in rows).items() if n > 1]
    for d in dupes[:20]:
        rep.error("SCHEMA", d, "duplicate sample_id")
    for r in rows:
        _check_row(r, rep)
    _check_versions(rows, rep)
    _check_splits(data, rows, rep, tolerance)
    _check_files_and_hashes(data, rows, rep, hashes)

    verdicts = Counter(r["expected_verdict"] for r in rows)
    negatives = sum(1 for r in rows if r["tamper_class"] == "NONE" or r["tamper_class"].startswith("F_"))
    rep.stats["samples"] = len(rows)
    rep.stats["verdicts"] = ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items()))
    if rows:
        share = negatives / len(rows)
        rep.stats["untouched or format-only"] = f"{negatives} ({share:.1%})"
        if not 0.25 <= share <= 0.45:
            rep.warn("BALANCE", "labels.csv", f"untouched or format-only share is {share:.0%}; target about one third")
    by_split: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        by_split[r["split"]].add(r["tamper_class"])
    for s in [x for x in SPLITS[1:] if x in by_split]:
        gap = sorted(by_split["train"] - by_split[s])
        if gap:
            rep.warn("COVERAGE", s, f"classes in train but not in {s}: {gap}")
    return rep, rows


def write_sample(rows: list[dict[str, str]], out: Path, fraction: float, seed: int) -> int:
    """A random sample of rows for a second person to re-check by hand."""
    rng = random.Random(seed)
    k = max(1, round(len(rows) * fraction)) if rows else 0
    picked = sorted(rng.sample(range(len(rows)), k)) if k else []
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        cols = list(rows[0].keys()) + ["reviewer", "reviewer_verdict", "agrees_with_label", "notes"] if rows else ["sample_id"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i in picked:
            w.writerow({**rows[i], "reviewer": "", "reviewer_verdict": "", "agrees_with_label": "", "notes": ""})
    return k


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a FIR-Tamper labels.csv against the locked tampering rules.")
    ap.add_argument("--data", type=Path, required=True, help="dataset folder holding labels.csv")
    ap.add_argument("--report", type=Path, help="write the markdown report here")
    ap.add_argument("--sample-out", type=Path, help="write a random re-check sample (CSV) here")
    ap.add_argument("--sample-fraction", type=float, default=0.10)
    ap.add_argument("--sample-seed", type=int, default=7)
    ap.add_argument("--no-hashes", action="store_true", help="skip SHA-256 checks against manifest.json")
    ap.add_argument("--split-tolerance", type=float, default=0.05)
    args = ap.parse_args(argv)
    try:
        rep, rows = validate(args.data, hashes=not args.no_hashes, tolerance=args.split_tolerance)
    except (FileNotFoundError, csv.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = rep.to_markdown()
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    if args.sample_out:
        n = write_sample(rows, args.sample_out, args.sample_fraction, args.sample_seed)
        print(f"wrote {n} rows for human re-check to {args.sample_out}")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
