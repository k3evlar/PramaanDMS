"""Build the FIR-Tamper v0 (English) dataset.

Usage (from the repo root):
    .venv/Scripts/python -m ml.data.generator.build --out dataset
    .venv/Scripts/python -m ml.data.generator.build --out dataset --no-captures

The same seed gives byte-identical files (checked by tests/ml/test_dataset_generator.py).

FIR-Tamper v3 (D96) adds --eclass-plan (one version per applicable E-class for every base
document), held-out bases from template family B (--n-*-unseen, split test_unseen), and
opaque version IDs so that no file name or ID tells the class.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from .capture import blur_boxes, make_captures, rasterize, save_pdf
from ..e_class import SUBTYPE_TO_E
from .generate import HELD_OUT_SCENARIOS, SCENARIOS, make_base_doc
from .labels import TASK_VERDICT, diff, field_changed_text, pages_text
from .model import Doc, fields_for
from .narrative import render_sentence
from .render import Assembled, box_dict, render
from .tamper import BY_CODE, CONTENT_CODES, FORMAT_CODES

DEFAULT_SEED = 20261015
CSV_COLUMNS = ["sample_id", "doc_type", "original_id", "tamper_class", "field_changed",
               "page_affected", "severity", "expected_verdict", "capture_type",
               "task_verdict", "content_changed", "could_not_verify", "flagged", "rule_ref",
               "version_id", "split", "files"]
CAPTURES = ("digital", "scan_sim", "photo_sim")
SPLITS = ("train", "val", "test", "test_unseen")

# Versions per E-class per base document in the E-class plan. Classes that fit fewer
# document types get more versions on the documents they fit, to even out the counts.
E_MULTIPLICITY: dict[str, int] = {"E5": 2, "E7": 2, "E9": 2, "E14": 2, "E13": 3}
E_CONTENT = [f"E{i}" for i in range(1, 20)]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(v: Any) -> Any:
    if isinstance(v, (tuple, list)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (frozenset, set)):
        return sorted(v)
    return v


def make_bases(rng: random.Random, counts: dict[str, int], scenarios: tuple[str, ...] = SCENARIOS,
               start: dict[str, int] | None = None) -> list[Doc]:
    docs: list[Doc] = []
    for doc_type, n in counts.items():
        scen = [scenarios[i % len(scenarios)] for i in range(n)]
        rng.shuffle(scen)
        longs = [i % 2 == 0 for i in range(n)]
        rng.shuffle(longs)
        first = (start or {}).get(doc_type, 0)
        for i in range(n):
            docs.append(make_base_doc(doc_type, first + i + 1, scen[i], longs[i], rng))
    return docs


def version_id(seed: int, doc_id: str, n: int, code: str) -> str:
    """Opaque version ID: the base document ID and 10 hex characters that do not show the class."""
    return f"{doc_id}-{hashlib.sha256(f'{seed}|{doc_id}|{n}|{code}'.encode()).hexdigest()[:10]}"


def assign_eclass(docs: list[Doc], n_pages: dict[str, int], rng: random.Random) -> dict[str, list[str]]:
    """For every document and E-class, pick applicable generator classes (balanced within the group)."""
    by_e: dict[str, list[str]] = {}
    for code, e in SUBTYPE_TO_E.items():
        if e in E_CONTENT and code in BY_CODE:
            by_e.setdefault(e, []).append(code)
    counts: Counter[str] = Counter()
    chosen: dict[str, list[str]] = {d.doc_id: [] for d in docs}
    for e in E_CONTENT:
        order = list(docs)
        rng.shuffle(order)
        for d in order:
            cands = sorted(c for c in by_e.get(e, []) if BY_CODE[c].applies(d, n_pages[d.doc_id]))
            for k in range(E_MULTIPLICITY.get(e, 1) if cands else 0):
                fresh = [c for c in cands if c not in chosen[d.doc_id]] or cands
                m = min(counts[c] for c in fresh)
                pick = rng.choice([c for c in fresh if counts[c] == m])
                chosen[d.doc_id].append(pick)
                counts[pick] += 1
    return chosen


def split_docs(docs: list[Doc], rng: random.Random) -> dict[str, str]:
    """Split by base document, stratified by type: about 70 / 15 / 15."""
    out: dict[str, str] = {}
    for t in sorted({d.doc_type for d in docs}):
        ids = [d.doc_id for d in docs if d.doc_type == t]
        rng.shuffle(ids)
        n = len(ids)
        n_val = max(1, round(n * 0.15))
        n_test = max(1, round(n * 0.15))
        n_train = n - n_val - n_test
        for i, did in enumerate(ids):
            out[did] = "train" if i < n_train else ("val" if i < n_train + n_val else "test")
    return out


def assign(docs: list[Doc], codes: list[str], per_doc: int, n_pages: dict[str, int],
           rng: random.Random) -> dict[str, list[str]]:
    """Give each doc `per_doc` distinct classes, keeping class counts balanced within the group."""
    counts: Counter[str] = Counter()
    chosen: dict[str, list[str]] = {d.doc_id: [] for d in docs}
    for _ in range(per_doc):
        order = list(docs)
        rng.shuffle(order)
        for d in order:
            cands = [c for c in codes if c not in chosen[d.doc_id] and BY_CODE[c].applies(d, n_pages[d.doc_id])]
            if not cands:
                continue
            m = min(counts[c] for c in cands)
            pick = rng.choice(sorted(c for c in cands if counts[c] == m))
            chosen[d.doc_id].append(pick)
            counts[pick] += 1
    return chosen


def doc_record(doc: Doc, asm: Assembled) -> dict[str, Any]:
    return {
        "doc_id": doc.doc_id, "doc_type": doc.doc_type, "scenario": doc.scenario,
        "family": doc.meta.get("family", "A"), "template_ids": [s.template_id for s in doc.narrative],
        "fields": _jsonable(doc.fields), "relations": _jsonable(doc.relations),
        "narrative": [render_sentence(s, doc.style) for s in doc.narrative],
        "style": _jsonable(doc.style.__dict__), "n_pages": len(asm.pages),
        "page_order": asm.order, "boxes": box_dict(asm.layout.boxes), "meta": doc.meta,
    }


def build(out: Path, seed: int, counts: dict[str, int], content_per_doc: int, format_per_doc: int,
          captures: bool, workers: int, eclass_plan: bool = False,
          unseen_counts: dict[str, int] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    if out.exists():
        for sub in ("base_docs", "tampered", "captures", "splits", "qa"):
            shutil.rmtree(out / sub, ignore_errors=True)
        for f in ("labels.csv", "labels.json", "manifest.json"):
            (out / f).unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    bases = make_bases(rng, counts)
    splits = split_docs(bases, rng)
    if unseen_counts:
        held = make_bases(rng, unseen_counts, HELD_OUT_SCENARIOS, start=counts)
        bases += held
        splits.update({d.doc_id: "test_unseen" for d in held})
    base_asm: dict[str, Assembled] = {}
    base_records = {}
    for d in bases:
        asm = render(d, out / "base_docs" / f"{d.doc_id}.pdf")
        base_asm[d.doc_id] = asm
        base_records[d.doc_id] = doc_record(d, asm)
        (out / "base_docs" / f"{d.doc_id}.json").write_text(json.dumps(base_records[d.doc_id], indent=1), encoding="utf-8")
    n_pages = {d.doc_id: len(base_asm[d.doc_id].pages) for d in bases}

    plan: dict[str, list[str]] = {d.doc_id: ["NONE"] for d in bases}
    for split in SPLITS:
        group = [d for d in bases if splits[d.doc_id] == split]
        if not group:
            continue
        fmt = assign(group, FORMAT_CODES, format_per_doc, n_pages, rng)
        cnt = assign_eclass(group, n_pages, rng) if eclass_plan else assign(group, CONTENT_CODES, content_per_doc, n_pages, rng)
        for d in group:
            plan[d.doc_id] += fmt[d.doc_id] + cnt[d.doc_id]

    versions: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for d in bases:
        base_pdf = out / "base_docs" / f"{d.doc_id}.pdf"
        for n, code in enumerate(plan[d.doc_id]):
            cls = BY_CODE[code]
            vid = version_id(seed, d.doc_id, n, code)
            vrng = random.Random(f"{seed}|{vid}|{code}")
            var, params = cls.apply(d, vrng, n_pages[d.doc_id])
            vdir = out / "tampered" / d.doc_id
            vpdf = vdir / f"{vid}.pdf"
            if code == "NONE":
                vdir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(base_pdf, vpdf)
                vasm = base_asm[d.doc_id]
            else:
                vasm = render(var, vpdf)
            res = diff(d, var, base_asm[d.doc_id], vasm, is_byte_copy=(code == "NONE"))
            blur_bx: list[list[float]] = []
            for k in sorted(var.blurred):
                blur_bx += [[b.page + 1] + b.as_list() for b in vasm.layout.boxes[k]]
            if blur_bx:
                save_pdf(blur_boxes(rasterize(vpdf), blur_bx), vpdf, quality=95)

            # Independent check: the class declaration must agree with the computed label.
            exp_v = cls.expected_verdict or "Equivalent"
            if res.verdict_capture != exp_v or (cls.expected_severity and res.severity != cls.expected_severity):
                mismatches.append(f"{vid} {code}: computed {res.verdict_capture}/{res.severity}, "
                                  f"declared {exp_v}/{cls.expected_severity}")
            if cls.group == "format":
                if res.changes:
                    mismatches.append(f"{vid} {code}: format class produced changes")
                if sha256_file(vpdf) == sha256_file(base_pdf):
                    mismatches.append(f"{vid} {code}: format class produced identical bytes")
            if cls.group not in ("none", "format", "blur") and not res.changes:
                mismatches.append(f"{vid} {code}: content class produced no change")
            if code == "NONE" and sha256_file(vpdf) != sha256_file(base_pdf):
                mismatches.append(f"{vid}: NONE copy is not byte-identical")

            rec = {
                "version_id": vid, "original_id": d.doc_id, "doc_type": d.doc_type,
                "split": splits[d.doc_id], "tamper_class": code, "group": cls.group,
                "worked_example": cls.worked_example, "rule_ref": cls.rule_ref,
                "description": cls.description, "params": _jsonable(params),
                "changes": [c.as_dict() for c in res.changes], "could_not_verify": res.could_not_verify,
                "flagged": res.flagged,
                "blur_boxes": blur_bx, "verdict_digital": res.verdict_digital,
                "verdict_capture": res.verdict_capture, "severity": res.severity,
                "content_changed": res.content_changed,
                "field_changed": field_changed_text(res),
                "page_affected": pages_text(res, sorted({int(b[0]) for b in blur_bx})),
                "variant": {"fields": _jsonable(var.fields), "style": _jsonable(var.style.__dict__),
                            "narrative": [render_sentence(s, var.style) for s in var.narrative],
                            "extra_page": [render_sentence(s, var.style) for s in var.extra_page],
                            "redacted": sorted(var.redacted), "page_order": vasm.order},
                "files": {"digital": vpdf.relative_to(out).as_posix()},
            }
            versions.append(rec)
            if captures:
                jobs.append({"version_id": vid, "pdf": str(vpdf), "blur_boxes": [], "seed": str(seed),
                             "digital_out": "", "scan_out": str(out / "captures" / "scan_sim" / d.doc_id / f"{vid}.pdf"),
                             "photo_dir": str(out / "captures" / "photo_sim" / d.doc_id)})
    if mismatches:
        raise SystemExit("Label check failed:\n" + "\n".join(mismatches))

    if captures:
        by_vid = {v["version_id"]: v for v in versions}
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for r in ex.map(make_captures, jobs, chunksize=4):
                v = by_vid[r["version_id"]]
                v["files"]["scan_sim"] = (Path("captures") / "scan_sim" / v["original_id"] / f"{r['version_id']}.pdf").as_posix()
                v["files"]["photo_sim"] = [(Path("captures") / "photo_sim" / v["original_id"] / f).as_posix() for f in r["photo_files"]]
                v["photo_matrices"] = r["photo_matrices"]

    # Samples: one per version per capture type.
    rows: list[dict[str, str]] = []
    for v in versions:
        for cap in CAPTURES:
            if cap not in v["files"]:
                continue
            files = v["files"][cap]
            verdict = v["verdict_digital"] if cap == "digital" else v["verdict_capture"]
            rows.append({
                "sample_id": f"{v['version_id']}-{cap}", "doc_type": v["doc_type"],
                "original_id": v["original_id"], "tamper_class": v["tamper_class"],
                "field_changed": v["field_changed"], "page_affected": v["page_affected"],
                "severity": v["severity"], "expected_verdict": verdict, "capture_type": cap,
                "task_verdict": TASK_VERDICT[verdict], "content_changed": "yes" if v["content_changed"] else "no",
                "could_not_verify": ";".join(v["could_not_verify"]), "flagged": "yes" if v["flagged"] else "no",
                "rule_ref": v["rule_ref"], "version_id": v["version_id"], "split": v["split"],
                "files": ";".join(files) if isinstance(files, list) else files,
            })
    with open(out / "labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    (out / "labels.json").write_text(json.dumps({"seed": seed, "versions": versions}, indent=1), encoding="utf-8")

    (out / "splits").mkdir(exist_ok=True)
    for split in SPLITS:
        if split not in set(splits.values()):
            continue
        ids = sorted(k for k, s in splits.items() if s == split)
        (out / "splits" / f"{split}.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
        sids = sorted(r["sample_id"] for r in rows if r["split"] == split)
        (out / "splits" / f"{split}_samples.txt").write_text("\n".join(sids) + "\n", encoding="utf-8")

    manifest = write_manifest(out, splits, rows)
    return {"bases": len(bases), "versions": len(versions), "samples": len(rows),
            "split_hashes": manifest["split_hashes"], "dataset_hash": manifest["dataset_hash"]}


def write_manifest(out: Path, splits: dict[str, str], rows: list[dict[str, str]]) -> dict[str, Any]:
    files = sorted(p for p in out.rglob("*") if p.is_file()
                   and p.name not in ("manifest.json", "README.md") and "qa" not in p.relative_to(out).parts
                   and "templates" not in p.relative_to(out).parts)
    hashes = {p.relative_to(out).as_posix(): sha256_file(p) for p in files}
    split_files: dict[str, set[str]] = {s: set() for s in sorted(set(splits.values()), key=SPLITS.index)}
    for did, s in splits.items():
        split_files[s].update({f"base_docs/{did}.pdf", f"base_docs/{did}.json"})
    for r in rows:
        split_files[r["split"]].update(r["files"].split(";"))
    split_hashes = {}
    for s, fs in split_files.items():
        h = hashlib.sha256()
        for path in sorted(fs):
            h.update(f"{path}:{hashes[path]}\n".encode())
        split_hashes[s] = h.hexdigest()
    total = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in hashes.items()).encode()).hexdigest()
    manifest = {"files": hashes, "split_hashes": split_hashes, "dataset_hash": total}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("dataset"))
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n-fir", type=int, default=24)
    ap.add_argument("--n-chargesheet", type=int, default=21)
    ap.add_argument("--n-statement", type=int, default=15)
    ap.add_argument("--content-per-doc", type=int, default=10)
    ap.add_argument("--format-per-doc", type=int, default=4)
    ap.add_argument("--eclass-plan", action="store_true",
                    help="one version per applicable E-class per base (v3); ignores --content-per-doc")
    ap.add_argument("--n-fir-unseen", type=int, default=0)
    ap.add_argument("--n-chargesheet-unseen", type=int, default=0)
    ap.add_argument("--n-statement-unseen", type=int, default=0)
    ap.add_argument("--no-captures", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args(argv)
    counts = {"FIR": a.n_fir, "CHARGESHEET": a.n_chargesheet, "STATEMENT": a.n_statement}
    unseen = {"FIR": a.n_fir_unseen, "CHARGESHEET": a.n_chargesheet_unseen, "STATEMENT": a.n_statement_unseen}
    unseen = {k: v for k, v in unseen.items() if v}
    stats = build(a.out, a.seed, counts, a.content_per_doc, a.format_per_doc, not a.no_captures, a.workers,
                  eclass_plan=a.eclass_plan, unseen_counts=unseen or None)
    json.dump(stats, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
