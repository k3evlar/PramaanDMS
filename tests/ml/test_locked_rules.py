"""The dataset generator labels every locked tampering rule correctly (D40 to D48).

Each rule has at least one clean negative (format only, expected Equivalent) and one
tampered case, computed through the same diff the dataset build uses.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

import pytest

from ml.data.generator.generate import make_base_doc
from ml.data.generator.labels import diff
from ml.data.generator.model import Doc, canonical, match_name
from ml.data.generator.render import assemble
from ml.data.generator.tamper import BY_CODE, CLASSES

ROOT = Path(__file__).resolve().parents[2]


def _docs() -> list[Doc]:
    """A spread of base documents: every type, short and long narratives, several cases."""
    rng = random.Random(44)
    out = []
    for i, (t, sc) in enumerate([("FIR", "house_theft"), ("FIR", "assault"), ("CHARGESHEET", "cheating"),
                                 ("CHARGESHEET", "vehicle_theft"), ("STATEMENT", "assault"), ("STATEMENT", "cheating")]):
        out.append(make_base_doc(t, i + 1, sc, i % 2 == 0, rng))
    return out


DOCS = _docs()


def label(code: str, doc: Doc | None = None, seed: int = 1):
    """Apply class `code` to the first document it fits and return the computed label."""
    cls = BY_CODE[code]
    for d in ([doc] if doc else DOCS):
        asm = assemble(d)
        if cls.applies(d, len(asm.pages)):
            var, _ = cls.apply(d, random.Random(seed), len(asm.pages))
            return diff(d, var, asm, assemble(var), is_byte_copy=(code == "NONE"))
    pytest.fail(f"{code} applies to none of the test documents")


def verdict(code: str) -> tuple[str, str]:
    r = label(code)
    return r.verdict_capture, r.severity


# --- clean negatives: only format differs -------------------------------------------

@pytest.mark.parametrize("code", ["NONE", "F_FONT", "F_REFLOW", "F_SPACING", "F_DATETIME_FORMAT",
                                  "F_NUMBER_FORMAT", "F_SECTION_FORMAT", "F_NAME_CASE", "F_METADATA", "F_HONORIFIC"])
def test_format_only_is_equivalent(code: str) -> None:
    r = label(code)
    assert (r.verdict_capture, r.severity, r.changes) == ("Equivalent", "None", [])
    if code == "NONE":
        assert r.verdict_digital == "Identical"


# --- D41: a clear edit beats unreadable fields -----------------------------------------

def test_d41_blur_only_is_inconclusive_with_could_not_verify() -> None:
    r = label("B_BLUR_ONLY")
    assert (r.verdict_capture, r.severity) == ("Inconclusive", "None")
    assert r.could_not_verify and not r.content_changed


def test_d41_blur_plus_clear_edit_is_tampered_and_lists_the_blurred_field() -> None:
    r = label("B_BLUR_PLUS_EDIT")
    assert (r.verdict_capture, r.severity) == ("Tampered", "Major")
    assert r.could_not_verify, "the unreadable field must still be listed"


# --- D40: spacing ----------------------------------------------------------------------

def test_d40_space_inside_an_id_is_major() -> None:
    assert verdict("T_ID_SPACE") == ("Tampered", "Major")


def test_d40_spacing_between_words_and_standard_separators_are_format() -> None:
    assert verdict("F_SPACING") == ("Equivalent", "None")
    assert verdict("F_NUMBER_FORMAT") == ("Equivalent", "None")


# --- D42: negation -----------------------------------------------------------------------

def test_d42_negation_flip_is_major_but_rewording_is_minor() -> None:
    assert verdict("N_NEGATION") == ("Tampered", "Major")
    assert verdict("N_REWORD") == ("Tampered", "Minor")
    kinds = {c.kind for c in label("N_NEGATION").changes}
    assert kinds == {"negation_flipped"}


# --- D43: pages ------------------------------------------------------------------------

@pytest.mark.parametrize("code", ["P_PAGE_ADDED", "P_PAGE_REMOVED", "P_PAGE_REORDER"])
def test_d43_page_changes_are_major(code: str) -> None:
    assert verdict(code) == ("Tampered", "Major")


# --- D44: name order and law sections -----------------------------------------------------

def test_d44_name_order_is_minor_and_only_an_order_change() -> None:
    r = label("T_NAME_ORDER")
    assert (r.verdict_capture, r.severity) == ("Tampered", "Minor")
    assert {c.kind for c in r.changes} == {"order_changed"}


def test_d44_sections_compare_as_a_set() -> None:
    assert verdict("F_SECTION_FORMAT") == ("Equivalent", "None")  # reordered and reformatted
    assert verdict("T_SECTION_ADDED") == ("Tampered", "Major")
    assert verdict("T_SECTION") == ("Tampered", "Major")
    assert canonical("law_sections", ("BNS:305", "BNS:303(2)")) == canonical("law_sections", ("BNS:303(2)", "BNS:305"))


# --- D45: narrative entities ----------------------------------------------------------------

def test_d45_narrative_entity_change_is_major_but_word_swap_is_minor() -> None:
    assert verdict("N_ENTITY") == ("Tampered", "Major")
    assert verdict("N_WORD_SWAP") == ("Tampered", "Minor")


@pytest.mark.parametrize("plain, with_entity", [("N_SENTENCE_ADD", "N_SENTENCE_ADD_ENTITY"),
                                                ("N_SENTENCE_REMOVE", "N_SENTENCE_REMOVE_ENTITY")])
def test_d45_added_or_removed_sentence_is_major_only_with_an_entity(plain: str, with_entity: str) -> None:
    assert verdict(plain) == ("Tampered", "Minor")
    assert verdict(with_entity) == ("Tampered", "Major")


# --- D46: annotations -----------------------------------------------------------------------

def test_d46_margin_note_is_minor_and_flagged() -> None:
    r = label("A_MARGIN_NOTE")
    assert (r.verdict_capture, r.severity, r.flagged) == ("Tampered", "Minor", True)


def test_d46_note_over_a_critical_field_is_major_and_not_just_flagged() -> None:
    r = label("A_NOTE_OVER_FIELD")
    assert (r.verdict_capture, r.severity, r.flagged) == ("Tampered", "Major", False)
    assert any(c.kind == "annotation_over_field" for c in r.changes)


def test_d46_added_stamp_is_a_visual_change() -> None:
    assert verdict("A_COURT_STAMP") == ("Tampered", "Major")


# --- D47: redaction -------------------------------------------------------------------------

def test_d47_redacted_copy_is_not_supported_in_every_capture() -> None:
    r = label("R_REDACTED")
    assert r.verdict_capture == r.verdict_digital == "Not supported"
    assert r.severity == "None"


# --- D48: honorifics --------------------------------------------------------------------------

def test_d48_honorifics_are_stripped_for_matching_but_a_name_change_is_major() -> None:
    assert match_name("Shri  RAMESH Kumar") == match_name("Ramesh Kumar") == "ramesh kumar"
    assert match_name("Smt. Sunita Rao") == "sunita rao"
    assert verdict("F_HONORIFIC") == ("Equivalent", "None")
    assert verdict("T_NAME") == ("Tampered", "Major")


# --- Every class agrees with its worked example ------------------------------------------------

def _worked_examples() -> dict[int, tuple[str, str]]:
    rows = {}
    for line in (ROOT / "docs/TAMPERING_DEFINITION.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].isdigit():
            rows[int(cells[0])] = (cells[3], cells[4])
    return rows


@pytest.mark.parametrize("cls", [c for c in CLASSES if c.code != "NONE"], ids=lambda c: c.code)
def test_class_matches_its_worked_example(cls) -> None:
    examples = _worked_examples()
    row = int(re.match(r"\d+", cls.worked_example).group())
    doc_verdict, doc_sev = examples[row]
    doc_verdict = {"No verdict": "Not supported", "Equivalent (with warning)": "Equivalent"}.get(doc_verdict, doc_verdict)
    doc_sev = {"n/a": "None", "Minor (flagged)": "Minor"}.get(doc_sev, doc_sev)
    assert (cls.expected_verdict, cls.expected_severity) == (doc_verdict, doc_sev), f"row {row}"


def test_every_class_names_a_decision_or_none() -> None:
    for c in CLASSES:
        assert c.rule_ref == "" or re.fullmatch(r"D\d+", c.rule_ref), c.code
