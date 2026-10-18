"""Phase 2 exit checks as automated tests (D65).

Phase 2 produces documents, so these tests check the documents themselves:
- THREAT_MODEL.md: every threat has a valid STRIDE category, group, mitigation, phase and
  test idea; at most 60 rows; the three special groups are covered; the coverage matrix
  has a valid entry in every component x STRIDE cell.
- REQUIREMENTS.md: every requirement has an acceptance test and a valid phase; IDs are
  unique; legal claims carry a source and a verified mark; referenced threats exist.
- LICENCES.md: no chosen or shipped component has a restricted or non-commercial licence;
  every planned stack component is listed with a source.
- ASVS_CHECKLIST.md: generated from the official CSV, complete, valid and up to date; the
  generator refuses bad input.
- TAMPERING_DEFINITION.md: the worked examples follow the locked rules.
- Text hygiene: no em or en dashes, banned words, Devanagari text or HOD review gates.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from tools import asvs_checklist

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
VALID_PHASES = {str(n) for n in range(1, 29)} | {"S"}
STRIDE = set("STRIDE")
BANNED = ["tamper-proof", "unhackable", "100% secure", "court admissible", "legally valid",
          "certified", "compliant with"]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def tables(text: str) -> list[list[dict[str, str]]]:
    """Parse every markdown table in `text` into a list of row dicts keyed by header."""
    out: list[list[dict[str, str]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("|") and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[i + 1]):
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", lines[j].strip().strip("|"))]
                rows.append(dict(zip(header, cells)))
                j += 1
            out.append(rows)
            i = j
        else:
            i += 1
    return out


def table_with(text: str, *columns: str) -> list[dict[str, str]]:
    for t in tables(text):
        if t and all(c in t[0] for c in columns):
            return t
    raise AssertionError(f"no table with columns {columns}")


def all_tables_with(text: str, *columns: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for t in tables(text):
        if t and all(c in t[0] for c in columns):
            rows += t
    return rows


def phases_valid(cell: str) -> bool:
    tokens = [t.strip() for t in cell.split(",") if t.strip()]
    return bool(tokens) and all(t in VALID_PHASES or t == "all" for t in tokens)


# ---------------------------------------------------------------------------
# Threat model
# ---------------------------------------------------------------------------

THREATS = table_with(read("docs/THREAT_MODEL.md"), "ID", "STRIDE", "Mitigation", "Phase", "Test idea")
THREAT_IDS = {r["ID"] for r in THREATS}


def test_threat_table_has_at_most_60_unique_rows() -> None:
    assert 0 < len(THREATS) <= 60
    assert len(THREAT_IDS) == len(THREATS)
    assert all(re.fullmatch(r"T\d{2}", r["ID"]) for r in THREATS)


@pytest.mark.parametrize("row", THREATS, ids=lambda r: r["ID"])
def test_every_threat_is_complete_and_mapped_to_a_phase(row: dict[str, str]) -> None:
    letters = {x.strip() for x in row["STRIDE"].split(",")}
    assert letters and letters <= STRIDE, row["STRIDE"]
    assert row["Group"] in {"core", "insider", "AI", "verification"}
    assert len(row["Threat"]) > 20 and len(row["Mitigation"]) > 20 and len(row["Test idea"]) > 15
    assert phases_valid(row["Phase"]), row["Phase"]


def test_special_groups_are_covered() -> None:
    groups = [r["Group"] for r in THREATS]
    for g in ("insider", "AI", "verification"):
        assert groups.count(g) >= 3, g


def test_coverage_matrix_has_every_component_and_stride_cell() -> None:
    matrix = table_with(read("docs/THREAT_MODEL.md"), "Component", "S", "T", "R", "I", "D", "E")
    components = {r["Component"] for r in matrix}
    assert components == {"API", "Storage", "Database", "Transparency log", "Worker", "Verify page", "Model"}
    by_id = {r["ID"]: r for r in THREATS}
    for row in matrix:
        for letter in "STRIDE":
            cell = row[letter]
            if cell.startswith("n/a:"):
                assert len(cell) > 30, f"{row['Component']}/{letter}: reason too short"
                continue
            ids = re.findall(r"T\d{2}", cell)
            assert ids, f"{row['Component']}/{letter} is empty"
            for tid in ids:
                assert tid in by_id, tid
                letters = {x.strip() for x in by_id[tid]["STRIDE"].split(",")}
                assert letter in letters, f"{tid} listed under {letter} but is {letters}"


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------

REQ_TEXT = read("docs/REQUIREMENTS.md")
REQS = all_tables_with(REQ_TEXT, "ID", "Requirement", "Acceptance test", "Phase")


def test_requirements_exist_for_every_kind() -> None:
    ids = [r["ID"] for r in REQS]
    assert len(ids) == len(set(ids)), "duplicate requirement IDs"
    for prefix in ("FR-", "FR-PUB-", "NFR-", "SR-"):
        assert any(i.startswith(prefix) for i in ids), prefix


@pytest.mark.parametrize("row", REQS, ids=lambda r: r["ID"])
def test_every_requirement_is_testable_and_phased(row: dict[str, str]) -> None:
    assert len(row["Requirement"]) > 20
    assert len(row["Acceptance test"]) > 15, f"{row['ID']} has no acceptance test"
    assert phases_valid(row["Phase"]), f"{row['ID']}: {row['Phase']}"


def test_public_page_messages_reveal_no_field_detail() -> None:
    pub = next(r for r in REQS if r["ID"] == "FR-PUB-2")
    messages = re.findall(r'"([^"]+\.)"', pub["Requirement"])
    assert "A critical field was changed." in messages
    assert len(messages) == 6
    field_words = ["date", "name", "amount", "section", "vehicle", "FIR", "page", "accused"]
    for m in messages:
        assert not any(w.lower() in m.lower() for w in field_words), m


def test_legal_claims_have_sources_and_verified_marks() -> None:
    legal = table_with(REQ_TEXT, "Topic", "Source", "Verified")
    assert len(legal) >= 10
    for row in legal:
        assert row["Source"].startswith("http"), row["Topic"]
        assert row["Verified"].startswith("yes"), row["Topic"]


def test_referenced_threats_exist() -> None:
    referenced = set(re.findall(r"\bT\d{2}\b", REQ_TEXT))
    assert referenced, "requirements reference no threats"
    assert referenced <= THREAT_IDS, referenced - THREAT_IDS


def test_asvs_documentation_sections_exist() -> None:
    for n in range(1, 11):
        assert re.search(rf"^### 4\.{n} ", REQ_TEXT, re.M), f"section 4.{n} missing"


# ---------------------------------------------------------------------------
# Licences
# ---------------------------------------------------------------------------

LIC = all_tables_with(read("docs/LICENCES.md"), "Component", "Licence (SPDX)", "Commercial use", "Status", "Source")
SHIPPED = ("Chosen", "Dev/test only", "Evaluation only")


def test_licence_table_is_populated() -> None:
    assert len(LIC) >= 50


@pytest.mark.parametrize("row", LIC, ids=lambda r: r["Component"])
def test_no_licence_blockers(row: dict[str, str]) -> None:
    status = row["Status"]
    assert row["Source"].startswith("http"), row["Component"]
    if status.startswith(SHIPPED):
        use = row["Commercial use"]
        allowed = use.startswith("yes") or ("demo only" in status and use == "unclear")
        assert allowed, f"{row['Component']}: {use}"
        assert not re.search(r"\b(NC|BUSL|SSPL|RSAL)", row["Licence (SPDX)"]), row["Component"]
    elif status.startswith("Rejected"):
        assert ":" in status and len(status) > 20, f"{row['Component']}: rejection needs a reason"
    else:
        assert status.startswith("Alternative"), f"{row['Component']}: unknown status {status}"


def test_planned_stack_is_listed() -> None:
    names = " ".join(r["Component"] for r in LIC)
    for comp in ["FastAPI", "PostgreSQL", "SeaweedFS", "Valkey", "Celery", "OpenBao", "ClamAV",
                 "PaddleOCR", "Tesseract", "PyTorch", "React", "Vite", "cryptography", "argon2-cffi",
                 "pyotp", "rfc3161ng", "segno", "pyzbar", "WeasyPrint", "nginx", "pypdfium2"]:
        assert comp in names, comp


def test_rejected_components_are_not_in_the_architecture() -> None:
    arch = read("ARCHITECTURE.md")
    containers = arch.split("## Containers", 1)[1].split("##", 1)[0]
    for rejected in ("minio", "redis", "vault"):
        assert rejected not in containers.lower(), rejected


# ---------------------------------------------------------------------------
# ASVS checklist
# ---------------------------------------------------------------------------

def test_asvs_checklist_is_complete_and_up_to_date() -> None:
    config, items = asvs_checklist.load_items()
    with open(ROOT / config["source_csv"], encoding="utf-8-sig", newline="") as f:
        expected = {r["req_id"] for r in csv.DictReader(f) if r["L"] in ("1", "2")}
    assert {i.req_id for i in items} == expected
    assert len(items) == 253
    assert asvs_checklist.render(config, items) == read("docs/ASVS_CHECKLIST.md")


def test_asvs_statuses_are_justified() -> None:
    _, items = asvs_checklist.load_items()
    for i in items:
        if i.status == "Planned":
            assert i.phase in VALID_PHASES and (i.phase == "S" or int(i.phase) > 2), i.req_id
        if i.status in ("Not applicable", "Accepted gap"):
            assert len(i.note) > 10, i.req_id
        if i.status == "Done":
            assert i.phase in {"2", "3", "5"} and i.ref, i.req_id  # done in a phase that has been built, with evidence


def _bad_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change) -> None:
    cfg = json.loads(asvs_checklist.STATUS_FILE.read_text(encoding="utf-8"))
    change(cfg)
    bad = tmp_path / "status.json"
    bad.write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(asvs_checklist, "STATUS_FILE", bad)


def test_asvs_generator_refuses_missing_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bad_config(tmp_path, monkeypatch, lambda c: c["sections"].pop("V3.4"))
    with pytest.raises(asvs_checklist.ChecklistError, match="no status"):
        asvs_checklist.load_items()


def test_asvs_generator_refuses_planned_without_phase(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bad_config(tmp_path, monkeypatch, lambda c: c["sections"]["V3.4"].pop("phase"))
    with pytest.raises(asvs_checklist.ChecklistError, match="valid phase"):
        asvs_checklist.load_items()


def test_asvs_generator_refuses_done_without_real_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bad_config(tmp_path, monkeypatch, lambda c: c["sections"]["V2.1"].update(ref="docs/REQUIREMENTS.md#9.9"))
    with pytest.raises(asvs_checklist.ChecklistError, match="existing document section"):
        asvs_checklist.load_items()


def test_asvs_generator_refuses_changed_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bad_config(tmp_path, monkeypatch, lambda c: c.update(source_csv_sha256="0" * 64))
    with pytest.raises(asvs_checklist.ChecklistError, match="SHA-256"):
        asvs_checklist.load_items()


# ---------------------------------------------------------------------------
# Tampering definition follows the locked rules
# ---------------------------------------------------------------------------

EXAMPLES = table_with(read("docs/TAMPERING_DEFINITION.md"), "#", "What changed", "Verdict", "Severity")


def test_worked_examples_are_numbered_and_valid() -> None:
    assert [int(r["#"]) for r in EXAMPLES] == list(range(1, len(EXAMPLES) + 1))
    assert len(EXAMPLES) >= 25
    for r in EXAMPLES:
        assert r["Verdict"] in {"Identical", "Equivalent", "Equivalent (with warning)", "Tampered",
                                "Inconclusive", "No verdict"}, r["#"]
        if r["Verdict"] == "Tampered":
            assert r["Severity"] in {"Major", "Minor", "Minor (flagged)"}, r["#"]
        else:
            assert r["Severity"] == "n/a", r["#"]


@pytest.mark.parametrize("phrase, verdict, severity", [
    ("Negation added", "Tampered", "Major"),
    ("Page added", "Tampered", "Major"),
    ("Page removed", "Tampered", "Major"),
    ("Page order changed", "Tampered", "Major"),
    ("Order of accused names swapped", "Tampered", "Minor"),
    ("Law section added", "Tampered", "Major"),
    ("Law sections listed in another order", "Equivalent", "n/a"),
    ("Honorific added", "Equivalent", "n/a"),
    ("Space inserted inside an ID", "Tampered", "Major"),
    ("Standard grouping inside a vehicle number", "Equivalent", "n/a"),
    ("Date changed inside the narrative only", "Tampered", "Major"),
    ("Handwritten note in a blank margin", "Tampered", "Minor (flagged)"),
    ("Handwritten note over a critical field", "Tampered", "Major"),
    ("One field blurred, another clearly edited", "Tampered", "Major"),
    ("Critical field too blurry, nothing else changed", "Inconclusive", "n/a"),
    ("Redacted copy", "No verdict", "n/a"),
    ("Reflowed layout", "Equivalent", "n/a"),
])
def test_locked_rules_in_worked_examples(phrase: str, verdict: str, severity: str) -> None:
    row = next(r for r in EXAMPLES if r["What changed"].startswith(phrase))
    assert (row["Verdict"], row["Severity"]) == (verdict, severity)


# ---------------------------------------------------------------------------
# Text hygiene
# ---------------------------------------------------------------------------

PHASE2_DOCS = ["docs/THREAT_MODEL.md", "docs/REQUIREMENTS.md", "docs/LICENCES.md",
               "docs/TAMPERING_DEFINITION.md", "docs/CRITICAL_FIELDS.md", "docs/SCOPE.md",
               "docs/NOVELTY.md", "LEGAL_HASH_SPEC.md", "PROJECT_BRIEF.md", "ARCHITECTURE.md",
               "PHASES.md"]
ALL_DOCS = sorted({p.relative_to(ROOT).as_posix() for p in list(ROOT.glob("*.md")) + list(DOCS.glob("*.md"))})


@pytest.mark.parametrize("name", PHASE2_DOCS)
def test_no_dashes_or_banned_words(name: str) -> None:
    text = read(name)
    assert "—" not in text and "–" not in text, "em or en dash"
    lower = text.lower()
    for word in BANNED:
        assert word not in lower, word


def test_asvs_notes_have_no_banned_words() -> None:
    notes = json.dumps(json.loads(asvs_checklist.STATUS_FILE.read_text(encoding="utf-8"))).lower()
    for word in BANNED:
        assert word not in notes, word


@pytest.mark.parametrize("name", ALL_DOCS)
def test_no_devanagari_text_and_no_hod_gates(name: str) -> None:
    text = read(name)
    assert not re.search("[ऀ-ॿ]", text), "Devanagari text found"
    if name != "DECISIONS.md":  # D54 itself records "No HOD review gates"
        assert not re.search(r"\bHOD\b|head of department", text, re.I), "HOD review gate found"
