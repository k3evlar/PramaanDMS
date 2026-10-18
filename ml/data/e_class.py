"""Add the paper's E-class names and the 3-level verdict to a built FIR-Tamper dataset.

Usage (from the repo root):
    .venv/Scripts/python -m ml.data.e_class --data dataset_v3

Reads labels.csv and labels.json, writes labels_eclass.csv next to them (plain UTF-8).
The generator's own labels are not changed (D94).

E0 to E15 follow the dataset task's class list; E16 to E19 hold the locked-rule cases
that have no E0 to E15 class. E7, E9, E12, E13 and E14 were added in Stage 2 (D96).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

E_NAMES: dict[str, str] = {
    "E0": "Format only or exact copy", "E1": "Name substitution", "E2": "Date alteration",
    "E3": "Time alteration", "E4": "Amount or number change", "E5": "Legal provision change",
    "E6": "Negation flip", "E7": "Role reversal", "E8": "Location change",
    "E9": "Evidence ID or description edit", "E10": "Clause insertion", "E11": "Clause deletion",
    "E12": "Modal or quantifier shift", "E13": "Custody chain edit", "E14": "Backdating",
    "E15": "Seal or signature tampering", "E16": "Other content edit (wording, order, minor field)",
    "E17": "Page change", "E18": "Annotation", "E19": "Unreadable or redacted",
}

SUBTYPE_TO_E: dict[str, str] = {
    "NONE": "E0", "F_FONT": "E0", "F_REFLOW": "E0", "F_SPACING": "E0", "F_DATETIME_FORMAT": "E0",
    "F_NUMBER_FORMAT": "E0", "F_SECTION_FORMAT": "E0", "F_NAME_CASE": "E0", "F_METADATA": "E0",
    "F_HONORIFIC": "E0",
    "T_NAME": "E1", "T_NAME_ADDED": "E1",
    "T_DATE": "E2",
    "T_TIME": "E3",
    "T_AMOUNT": "E4", "T_AGE": "E4", "T_ID": "E4", "T_VEHICLE": "E4", "T_ID_SPACE": "E4",
    "T_SECTION": "E5", "T_SECTION_ADDED": "E5",
    "N_NEGATION": "E6",
    "T_PLACE": "E8",
    "N_SENTENCE_ADD": "E10", "N_SENTENCE_ADD_ENTITY": "E10",
    "N_SENTENCE_REMOVE": "E11", "N_SENTENCE_REMOVE_ENTITY": "E11",
    "V_STAMP_REMOVED": "E15", "V_STAMP_SWAPPED": "E15", "V_SIGNATURE_SWAPPED": "E15",
    "A_COURT_STAMP": "E15",
    "N_WORD_SWAP": "E16", "N_REWORD": "E16", "N_PUNCT": "E16", "T_NAME_ORDER": "E16",
    "T_ADDRESS": "E16", "T_RANK": "E16",
    "P_PAGE_ADDED": "E17", "P_PAGE_REMOVED": "E17", "P_PAGE_REORDER": "E17",
    "A_MARGIN_NOTE": "E18", "A_NOTE_OVER_FIELD": "E18",
    "B_BLUR_ONLY": "E19", "B_BLUR_PLUS_EDIT": "E19", "R_REDACTED": "E19",
    # Stage 2 (D96)
    "N_ENTITY_NAME": "E1", "N_ENTITY_DATE": "E2", "N_ENTITY_TIME": "E3", "N_ENTITY_NUMBER": "E4",
    "E_ROLE_SWAP": "E7", "E_EXHIBIT_ID": "E9", "E_EXHIBIT_DESC": "E9", "N_MODAL": "E12",
    "C_CUSTODY_HOLDER": "E13", "C_CUSTODY_DATE": "E13", "C_CUSTODY_ENTRY_REMOVED": "E13",
    "T_BACKDATE": "E14",
    # N_ENTITY depends on which narrative entity changed; see entity_e_class().
}

# Narrative entity slot -> E-class (slots from ml/data/generator/narrative.py ENTITY_SLOTS).
ENTITY_SLOT_TO_E: dict[str, str] = {
    "accused": "E1", "complainant": "E1", "witness": "E1",
    "date_incident": "E2", "time_incident": "E3", "amount": "E4", "vehicle": "E4",
}

VERDICT_3LEVEL: dict[str, str] = {
    "Identical": "Identical", "Equivalent": "Equivalent", "Tampered": "Materially Altered",
    "Inconclusive": "Inconclusive", "Not supported": "Not supported",
}

EXTRA_COLUMNS = ["e_class", "e_class_name", "verdict_3level", "original_path"]


def entity_e_class(changes: list[dict[str, Any]]) -> str:
    """E-class of an N_ENTITY version, from the slot of the changed narrative entity."""
    for c in changes:
        if c.get("kind") == "narrative_entity_changed" and isinstance(c.get("old"), dict):
            for slot in c["old"]:
                if slot in ENTITY_SLOT_TO_E:
                    return ENTITY_SLOT_TO_E[slot]
    raise ValueError("N_ENTITY version has no recognised narrative entity change")


def e_class_for(subtype: str, changes: list[dict[str, Any]]) -> str:
    if subtype == "N_ENTITY":
        return entity_e_class(changes)
    if subtype not in SUBTYPE_TO_E:
        raise KeyError(f"no E-class for generator class {subtype!r}; add it to SUBTYPE_TO_E")
    return SUBTYPE_TO_E[subtype]


def add_e_classes(data: Path) -> dict[str, Any]:
    with open(data / "labels.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        rows = list(reader)
    versions = {v["version_id"]: v for v in json.loads((data / "labels.json").read_text(encoding="utf-8"))["versions"]}
    for r in rows:
        v = versions[r["version_id"]]
        e = e_class_for(r["tamper_class"], v["changes"])
        r["e_class"] = e
        r["e_class_name"] = E_NAMES[e]
        r["verdict_3level"] = VERDICT_3LEVEL[r["expected_verdict"]]
        r["original_path"] = f"base_docs/{r['original_id']}.pdf"
    with open(data / "labels_eclass.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns + EXTRA_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return {"rows": len(rows), "e_class": dict(sorted(Counter(r["e_class"] for r in rows).items(),
                                                      key=lambda kv: int(kv[0][1:]))),
            "verdict_3level": dict(Counter(r["verdict_3level"] for r in rows))}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    a = ap.parse_args(argv)
    json.dump(add_e_classes(a.data), sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
