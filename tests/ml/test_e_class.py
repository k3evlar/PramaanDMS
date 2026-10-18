"""Tests for the E-class mapping (ml/data/e_class.py, D94)."""

from __future__ import annotations

import pytest

from ml.data.e_class import E_NAMES, SUBTYPE_TO_E, VERDICT_3LEVEL, e_class_for, entity_e_class
from ml.data.generator.labels import TASK_VERDICT
from ml.data.generator.narrative import ENTITY_SLOTS
from ml.data.generator.tamper import CLASSES


def test_every_generator_class_has_an_e_class() -> None:
    for cls in CLASSES:
        if cls.code == "N_ENTITY":
            continue
        assert cls.code in SUBTYPE_TO_E, cls.code
        assert SUBTYPE_TO_E[cls.code] in E_NAMES


def test_harmless_classes_map_to_e0_and_only_they_do() -> None:
    for cls in CLASSES:
        if cls.code == "N_ENTITY":
            continue
        is_harmless = cls.group in ("none", "format")
        assert (SUBTYPE_TO_E[cls.code] == "E0") == is_harmless, cls.code


@pytest.mark.parametrize("slot", sorted(ENTITY_SLOTS))
def test_every_narrative_entity_slot_maps(slot: str) -> None:
    changes = [{"kind": "narrative_entity_changed", "old": {slot: "x"}, "new": {slot: "y"}}]
    assert entity_e_class(changes) in {"E1", "E2", "E3", "E4"}


def test_entity_slot_examples() -> None:
    def one(slot: str) -> str:
        return e_class_for("N_ENTITY", [{"kind": "narrative_entity_changed", "old": {slot: 1}, "new": {slot: 2}}])
    assert one("date_incident") == "E2"
    assert one("time_incident") == "E3"
    assert one("accused") == "E1"
    assert one("amount") == "E4"


def test_n_entity_without_entity_change_is_an_error() -> None:
    with pytest.raises(ValueError):
        entity_e_class([{"kind": "narrative_changed", "old": "sentence 1", "new": "sentence 1"}])


def test_unknown_class_is_an_error() -> None:
    with pytest.raises(KeyError):
        e_class_for("NOT_A_CLASS", [])


def test_every_locked_verdict_has_a_3level_name() -> None:
    assert set(VERDICT_3LEVEL) == set(TASK_VERDICT)
    assert VERDICT_3LEVEL["Tampered"] == "Materially Altered"
