"""ml/data/validate_labels.py: catches every kind of label error, and passes clean data.

Uses the hand-written fixture in tests/fixtures/labels_fixture/ (a test fixture, not the
dataset) and a tiny dataset generated into a temporary folder.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from ml.data import validate_labels as vl
from ml.data.generator.build import build

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "labels_fixture"


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path / "labels.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write(path: Path, rows: list[dict[str, str]], columns: list[str] | None = None) -> None:
    cols = columns or list(rows[0].keys())
    with open(path / "labels.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def fx(tmp_path: Path) -> Path:
    dst = tmp_path / "fx"
    shutil.copytree(FIXTURE, dst)
    return dst


def codes(path: Path) -> set[str]:
    rep, _ = vl.validate(path, hashes=False)
    return {f.code for f in rep.errors}


def test_fixture_is_clean() -> None:
    rep, rows = vl.validate(FIXTURE, hashes=False)
    assert rep.errors == [], [f"{f.code} {f.where} {f.message}" for f in rep.errors]
    assert len(rows) == 15


def mutate(fx: Path, sample_id: str, **changes: str) -> set[str]:
    rows = _rows(fx)
    for r in rows:
        if r["sample_id"] == sample_id:
            r.update(changes)
    _write(fx, rows)
    return codes(fx)


@pytest.mark.parametrize("sample_id, changes, expected", [
    ("FIR-9001-V01-digital", {"expected_verdict": "Altered", "severity": "Critical"}, "VALUE"),
    ("FIR-9001-V01-digital", {"severity": "None"}, "SEV"),
    ("FIR-9001-V02-digital", {"severity": "Minor"}, "SEV"),
    ("FIR-9001-V03-digital", {"expected_verdict": "Inconclusive", "severity": "None", "task_verdict": "Inconclusive"}, "D41"),
    ("FIR-9001-V02-digital", {"could_not_verify": ""}, "D41"),
    ("FIR-9001-V06-digital", {"severity": "Minor"}, "D43"),
    ("FIR-9001-V07-digital", {"severity": "Minor"}, "VIS"),
    ("CS-9001-V02-digital", {"flagged": "yes"}, "D46"),
    ("FIR-9001-V05-digital", {"expected_verdict": "Tampered", "severity": "Major", "task_verdict": "Tampered"}, "D47"),
    ("FIR-9001-V00-scan_sim", {"expected_verdict": "Identical"}, "IDENT"),
    ("FIR-9001-V01-digital", {"task_verdict": "Valid"}, "TASK"),
    ("CS-9001-V01-digital", {"severity": "Minor"}, "CLASS"),  # negation must be Major (D42)
    ("STM-9001-V01-digital", {"severity": "Major"}, "CLASS"),  # name order must be Minor (D44)
    ("FIR-9001-V01-digital", {"doc_type": "MEMO"}, "VALUE"),
    ("FIR-9001-V01-digital", {"page_affected": "1,2"}, "VALUE"),
    ("FIR-9001-V01-digital", {"field_changed": "दिनांक"}, "VALUE"),
    ("FIR-9001-V01-digital", {"split": "test"}, "SPLIT"),  # leakage: one base document in two splits
    ("FIR-9001-V01-digital", {"files": "files/missing.pdf"}, "FILE"),
])
def test_each_error_kind_is_caught(fx: Path, sample_id: str, changes: dict[str, str], expected: str) -> None:
    assert expected in mutate(fx, sample_id, **changes)


def test_captures_of_one_version_must_agree(fx: Path) -> None:
    assert "VERSION" in mutate(fx, "FIR-9001-V00-scan_sim", tamper_class="F_FONT")


def test_duplicate_sample_and_missing_column_are_schema_errors(fx: Path) -> None:
    rows = _rows(fx)
    _write(fx, rows + [rows[0]])
    assert "SCHEMA" in codes(fx)
    _write(fx, rows, [c for c in rows[0] if c != "severity"])
    assert codes(fx) == {"SCHEMA"}


def test_split_file_must_agree_with_labels(fx: Path) -> None:
    (fx / "splits" / "val.txt").write_text("CS-9001\nCS-9999\n", encoding="utf-8")
    assert "SPLIT" in codes(fx)


def test_missing_labels_file_is_exit_code_2(tmp_path: Path) -> None:
    assert vl.main(["--data", str(tmp_path)]) == 2


def test_cli_exit_codes_and_outputs_go_only_where_asked(fx: Path, tmp_path: Path) -> None:
    before = sorted(p.name for p in fx.rglob("*"))
    out = tmp_path / "out"
    assert vl.main(["--data", str(FIXTURE), "--no-hashes", "--report", str(out / "r.md"),
                    "--sample-out", str(out / "s.csv")]) == 0
    assert (out / "r.md").read_text(encoding="utf-8").startswith("# Label validation report")
    sample = list(csv.DictReader(open(out / "s.csv", encoding="utf-8")))
    assert len(sample) == 2 and "agrees_with_label" in sample[0]  # 10% of 15, rounded
    assert sorted(p.name for p in fx.rglob("*")) == before  # nothing written into the data folder
    mutate(fx, "FIR-9001-V01-digital", severity="None")
    assert vl.main(["--data", str(fx), "--no-hashes"]) == 1


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("gen")
    build(out, 321, {"FIR": 3, "CHARGESHEET": 3, "STATEMENT": 2}, content_per_doc=10, format_per_doc=4,
          captures=False, workers=1)
    return out


def test_generated_dataset_validates_with_hashes(generated: Path) -> None:
    rep, rows = vl.validate(generated, hashes=True)
    assert rep.errors == [], [f"{f.code} {f.where} {f.message}" for f in rep.errors[:10]]
    assert rep.stats["split hashes matching manifest"] == "3 of 3"
    assert {r["expected_verdict"] for r in rows} >= {"Tampered", "Equivalent", "Identical"}


def test_changed_file_breaks_the_split_hash(generated: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy"
    shutil.copytree(generated, copy)
    target = next((copy / "tampered").rglob("*.pdf"))
    target.write_bytes(target.read_bytes() + b"\n%tampered")
    rep, _ = vl.validate(copy, hashes=True)
    assert "HASH" in {f.code for f in rep.errors}
