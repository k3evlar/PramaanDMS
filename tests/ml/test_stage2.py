"""FIR-Tamper v3 Stage 2 (D96): new classes, template families, E-class plan, no label leaks."""

from __future__ import annotations

import csv
import json
import random
import string
from datetime import date
from pathlib import Path

import pytest

from ml.data.e_class import add_e_classes
from ml.data.generator import check
from ml.data.generator.build import build, version_id
from ml.data.generator.generate import HELD_OUT_SCENARIOS, SCENARIOS, make_base_doc
from ml.data.generator.labels import diff
from ml.data.generator.narrative import (ALL_TEMPLATES, GENERIC, build_narrative, family_of,
                                        sentence_modals, unused_templates)
from ml.data.generator.render import FOOTER, assemble
from ml.data.generator.tamper import BNS_START, BY_CODE, CLASSES

SEEN = {"FIR": 4, "CHARGESHEET": 4, "STATEMENT": 4}
UNSEEN = {"FIR": 1, "CHARGESHEET": 1, "STATEMENT": 1}


def _slots(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def _family_ids(fam: str) -> set[str]:
    g = GENERIC[fam]
    ids = {g[k].tid for k in ("fir_intro", "fir_close", "stm_intro", "stm_close", "cs_open", "cs_close")}
    for k in ("stm_core", "cs_core", "first_extras", "third_extras", "added"):
        ids |= {t.tid for t in g[k]}
    return ids


def test_every_template_uses_the_same_slots_in_both_phrasings() -> None:
    # Otherwise an edit to a slot missing from the printed phrasing would change the label
    # but not the page.
    for t in ALL_TEMPLATES.values():
        assert _slots(t.phrasings[0]) == _slots(t.phrasings[1]), t.tid
        for slot in list(t.choices) + list(t.negs) + list(t.mods):
            assert slot in _slots(t.phrasings[0]), (t.tid, slot)


def test_generic_template_families_are_disjoint() -> None:
    assert not _family_ids("A") & _family_ids("B")


@pytest.mark.parametrize("scenario", SCENARIOS + HELD_OUT_SCENARIOS)
@pytest.mark.parametrize("doc_type", ["FIR", "STATEMENT", "CHARGESHEET"])
def test_narratives_use_only_their_own_family(scenario: str, doc_type: str) -> None:
    other = _family_ids("B" if family_of(scenario) == "A" else "A")
    for long in (True, False):
        case = {"complainant": "Ravi Sharma", "accused": "Amit Verma", "witness": "Neha Joshi",
                "date_incident": "2025-03-04", "time_incident": "10:15", "amount": 25000,
                "vehicle": "ZZ12AB3456", "landmark": "the bus stand", "place": "Ram Nagar, near the bus stand",
                "district": "Navgarh"}
        ids = {s.template_id for s in build_narrative(doc_type, scenario, case, random.Random(3), long)}
        assert not ids & other, (scenario, doc_type, ids & other)
        fam = family_of(scenario)
        for t in unused_templates(doc_type, ids, family=fam):
            assert t.tid not in other


def test_held_out_scenarios_are_not_seen_scenarios() -> None:
    assert not set(SCENARIOS) & set(HELD_OUT_SCENARIOS)
    assert all(family_of(s) == "B" for s in HELD_OUT_SCENARIOS)


def _label(code: str, doc_type: str, scenario: str, seed: int = 1):
    for k in range(20):
        base = make_base_doc(doc_type, k + 1, scenario, True, random.Random(seed * 100 + k))
        asm = assemble(base)
        cls = BY_CODE[code]
        if cls.applies(base, len(asm.pages)):
            var, params = cls.apply(base, random.Random(seed), len(asm.pages))
            return base, var, diff(base, var, asm, assemble(var), is_byte_copy=False), params
    pytest.fail(f"{code} never applied")


def test_role_swap_swaps_fields_and_narrative() -> None:
    base, var, res, _ = _label("E_ROLE_SWAP", "FIR", "assault")
    assert var.fields["complainant_name"] == base.fields["accused_names"][0]
    assert var.fields["accused_names"][0] == base.fields["complainant_name"]
    for so, sv in zip(base.narrative, var.narrative):
        vo, vv = dict(so.values), dict(sv.values)
        if "accused" in vo and vo["accused"] == base.fields["accused_names"][0]:
            assert vv["accused"] == base.fields["complainant_name"]
    assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


def test_role_swap_only_for_a_male_complainant() -> None:
    cls = BY_CODE["E_ROLE_SWAP"]
    for k in range(30):
        d = make_base_doc("FIR", k + 1, "cheating", True, random.Random(k))
        first = [p for p in d.fields["complainant_name"].split() if p not in ("Shri", "Smt")][0]
        from ml.data.generator import fakedata as fd
        assert cls.applies(d, 2) == (first in fd.MALE_FIRST)


def test_backdate_moves_all_dates_before_bns_and_keeps_bns_sections() -> None:
    base, var, res, params = _label("T_BACKDATE", "CHARGESHEET", "cheating")
    assert params["anachronism"] is True
    for key in ("date_of_report", "date_of_incident", "charge_sheet_date", "seizure_date"):
        assert date.fromisoformat(var.fields[key]) < BNS_START, key
    assert all(date.fromisoformat(x) < BNS_START for x in var.fields["custody_dates"])
    assert var.fields["law_sections"] == base.fields["law_sections"]
    assert all(s.startswith("BNS:") for s in var.fields["law_sections"])
    assert var.fields["fir_number"].endswith(var.fields["date_of_report"][:4])
    assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


def test_custody_entry_removed_shortens_the_chain_consistently() -> None:
    base, var, res, _ = _label("C_CUSTODY_ENTRY_REMOVED", "CHARGESHEET", "house_theft")
    n = len(base.fields["custody_holders"])
    assert len(var.fields["custody_holders"]) == len(var.fields["custody_dates"]) == len(var.relations["custody"]) == n - 1
    assert var.fields["custody_holders"][0] == base.fields["custody_holders"][0]  # the seizure entry stays
    assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


def test_modal_shift_changes_only_one_modal_slot_and_is_minor() -> None:
    base, var, res, params = _label("N_MODAL", "STATEMENT", "upi_fraud")
    i = params["sentence"]
    so, sv = base.narrative[i], var.narrative[i]
    assert so.template_id == sv.template_id
    changed = [k for (k, a), (_, b) in zip(so.values, sv.values) if a != b]
    assert len(changed) == 1 and changed[0].startswith("m_")
    assert sentence_modals(so) != sentence_modals(sv)
    assert (res.verdict_capture, res.severity) == ("Tampered", "Minor")


def test_exhibit_description_edit_changes_one_word() -> None:
    base, var, res, params = _label("E_EXHIBIT_DESC", "CHARGESHEET", "mobile_theft")
    i = params["index"]
    a, b = base.fields["property_items"][i].split(), var.fields["property_items"][i].split()
    assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
    assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


@pytest.mark.parametrize("kind_code, slots", [("N_ENTITY_NAME", {"accused", "complainant", "witness"}),
                                              ("N_ENTITY_DATE", {"date_incident"}),
                                              ("N_ENTITY_TIME", {"time_incident"}),
                                              ("N_ENTITY_NUMBER", {"amount", "vehicle"})])
def test_entity_kind_edits_touch_only_their_kind(kind_code: str, slots: set[str]) -> None:
    base, var, res, params = _label(kind_code, "FIR", "shop_burglary")
    so, sv = base.narrative[params["sentence"]], var.narrative[params["sentence"]]
    changed = {k for (k, a), (_, b) in zip(so.values, sv.values) if a != b}
    assert changed and changed <= slots
    assert (res.verdict_capture, res.severity) == ("Tampered", "Major")


def test_version_ids_do_not_show_the_class() -> None:
    for c in CLASSES:
        vid = version_id(1, "FIR-0001", 0, c.code)
        assert c.code not in vid and "_" not in vid
    assert version_id(1, "FIR-0001", 0, "NONE") != version_id(1, "FIR-0001", 1, "NONE")


def test_footer_is_neutral() -> None:
    assert "v0" not in FOOTER and "Tamper" not in FOOTER


@pytest.fixture(scope="module")
def stage2_build(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("s2")
    build(out, 77, SEEN, content_per_doc=0, format_per_doc=8, captures=False, workers=1,
          eclass_plan=True, unseen_counts=UNSEEN)
    add_e_classes(out)
    return out


def test_stage2_build_covers_every_e_class(stage2_build: Path) -> None:
    with open(stage2_build / "labels_eclass.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["e_class"] for r in rows} == {f"E{i}" for i in range(20)}
    assert {r["split"] for r in rows} == {"train", "val", "test", "test_unseen"}


def test_stage2_files_and_ids_do_not_show_the_class(stage2_build: Path) -> None:
    versions = json.loads((stage2_build / "labels.json").read_text(encoding="utf-8"))["versions"]
    for v in versions:
        for code in BY_CODE:
            assert code not in v["version_id"]
            assert code not in v["files"]["digital"]


def test_test_unseen_shares_no_template_with_train(stage2_build: Path) -> None:
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (stage2_build / "base_docs").glob("*.json")]
    split = {}
    for v in json.loads((stage2_build / "labels.json").read_text(encoding="utf-8"))["versions"]:
        split[v["original_id"]] = v["split"]
    train_ids = {t for r in recs if split[r["doc_id"]] == "train" for t in r["template_ids"]}
    unseen = [r for r in recs if split[r["doc_id"]] == "test_unseen"]
    assert unseen and all(r["family"] == "B" for r in unseen)
    assert all(r["family"] == "A" for r in recs if split[r["doc_id"]] != "test_unseen")
    for r in unseen:
        assert not set(r["template_ids"]) & train_ids


def test_stage2_text_layer_and_personal_data(stage2_build: Path) -> None:
    versions = json.loads((stage2_build / "labels.json").read_text(encoding="utf-8"))["versions"]
    checked, failures = check.text_layer_check(stage2_build, versions)
    assert checked > 100 and failures == []
    assert check.pii_check(stage2_build, versions) == []


def test_old_sentence_inside_a_new_sentence_is_not_a_failure(tmp_path: Path) -> None:
    # Regression: "I know X" -> "I think I know X" keeps the old sentence as a substring.
    base, var, _, _ = _label("N_MODAL", "STATEMENT", "assault", seed=3)
    assert any(sentence_modals(s) for s in var.narrative)
