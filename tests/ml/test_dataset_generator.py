"""Tests for the FIR-Tamper v0 dataset generator (ml/data/generator)."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from ml.data.generator import check
from ml.data.generator.build import build
from ml.data.generator.generate import make_base_doc
from ml.data.generator.labels import diff
from ml.data.generator.model import Style, canonical, fmt_amount, fmt_date, fmt_sections, fmt_time
from ml.data.generator.render import assemble
from ml.data.generator.tamper import CLASSES, _one_digit

SMALL = {"FIR": 2, "CHARGESHEET": 2, "STATEMENT": 2}


@pytest.fixture(scope="module")
def small_build(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    out = tmp_path_factory.mktemp("ds")
    stats = build(out, 123, SMALL, content_per_doc=10, format_per_doc=4, captures=False, workers=1)
    return out, stats


def test_same_seed_gives_identical_files(small_build: tuple[Path, dict], tmp_path: Path) -> None:
    _, stats = small_build
    again = build(tmp_path / "again", 123, SMALL, content_per_doc=10, format_per_doc=4, captures=False, workers=1)
    assert again["dataset_hash"] == stats["dataset_hash"]
    assert again["split_hashes"] == stats["split_hashes"]


def test_different_seed_gives_different_files(small_build: tuple[Path, dict], tmp_path: Path) -> None:
    _, stats = small_build
    other = build(tmp_path / "other", 124, SMALL, content_per_doc=10, format_per_doc=4, captures=False, workers=1)
    assert other["dataset_hash"] != stats["dataset_hash"]


def test_text_layer_agrees_with_labels(small_build: tuple[Path, dict]) -> None:
    out, _ = small_build
    versions = json.loads((out / "labels.json").read_text(encoding="utf-8"))["versions"]
    checked, failures = check.text_layer_check(out, versions)
    assert checked > 50
    assert failures == []


def test_no_real_personal_data(small_build: tuple[Path, dict]) -> None:
    out, _ = small_build
    versions = json.loads((out / "labels.json").read_text(encoding="utf-8"))["versions"]
    assert check.pii_check(out, versions) == []


def test_split_is_by_base_document(small_build: tuple[Path, dict]) -> None:
    out, _ = small_build
    seen: dict[str, str] = {}
    for v in json.loads((out / "labels.json").read_text(encoding="utf-8"))["versions"]:
        assert seen.setdefault(v["original_id"], v["split"]) == v["split"]


@pytest.mark.parametrize("doc_type", ["FIR", "STATEMENT", "CHARGESHEET"])
def test_every_class_gives_its_declared_verdict(doc_type: str) -> None:
    rng = random.Random(5)
    for k in range(3):
        base = make_base_doc(doc_type, k + 1, ["house_theft", "assault", "cheating"][k], k % 2 == 0, rng)
        base_asm = assemble(base)
        n_pages = len(base_asm.pages)
        for cls in CLASSES:
            if not cls.applies(base, n_pages):
                continue
            var, _ = cls.apply(base, random.Random(f"{k}{cls.code}"), n_pages)
            res = diff(base, var, base_asm, assemble(var), is_byte_copy=(cls.code == "NONE"))
            exp = cls.expected_verdict or "Equivalent"
            assert res.verdict_capture == exp, cls.code
            if cls.expected_severity:
                assert res.severity == cls.expected_severity, cls.code
            if cls.group == "format":
                assert res.changes == [], cls.code
            if cls.code == "NONE":
                assert res.verdict_digital == "Identical"


def test_any_page_removed_is_major_whatever_it_held() -> None:
    # D43: added, removed and reordered pages are Major, even a page of narrative only.
    rng = random.Random(9)
    base = make_base_doc("FIR", 1, "assault", True, rng)
    asm = assemble(base)
    by_code = {c.code: c for c in CLASSES}
    for p in range(len(asm.pages)):
        var, _ = by_code["P_PAGE_REMOVED"].apply(base, random.Random(0), len(asm.pages))
        var.removed_page = p
        res = diff(base, var, asm, assemble(var), is_byte_copy=False)
        assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


def test_display_formats_normalize_to_one_value() -> None:
    s = Style()
    assert fmt_amount(500000, Style(amount_fmt="indian_rs")) == "Rs 5,00,000/-"
    assert fmt_amount(500000, Style(amount_fmt="plain_rs")) == "Rs. 500000"
    assert fmt_amount(500000, Style(amount_fmt="lakh_words")) == "Rs 5 lakh"
    assert fmt_amount(512345, Style(amount_fmt="lakh_words")) == "Rs 5,12,345/-"
    assert fmt_date("2026-03-12", Style(date_fmt="d_month_y")) == "12 March 2026"
    assert fmt_date("2026-03-12", Style(date_fmt="dth_mon_y")) == "12th Mar 2026"
    assert fmt_time("14:30", Style(time_fmt="12h")) == "2:30 PM"
    secs = ("BNS:303(2)", "BNS:305")
    assert fmt_sections(secs, Style(section_fmt="section_of")) == "Sections 303(2) and 305 of BNS"
    assert canonical("law_sections", secs) == canonical("law_sections", tuple(reversed(secs)))
    assert canonical("complainant_name", "RAMESH  KUMAR") == canonical("complainant_name", "Ramesh Kumar")
    assert canonical("accused_names", ("A B", "C D")) != canonical("accused_names", ("C D", "A B"))
    assert s.date_fmt == "dmy_slash"


def test_one_digit_change_changes_exactly_one_digit() -> None:
    rng = random.Random(1)
    for n in [7, 45000, 500000, 19, 830]:
        for _ in range(50):
            m = _one_digit(n, rng)
            a, b = str(n), str(m)
            assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
