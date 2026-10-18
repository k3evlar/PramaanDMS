"""Tamper and format classes for the FIR-Tamper dataset.

Each class names the worked example it comes from in docs/TAMPERING_DEFINITION.md
(section 6) and the locked decision it exercises (D40 to D48 in DECISIONS.md). Labels are
not taken from these declarations: they are computed from the model diff in labels.py.
The declared expectation is a second, independent statement, and the build stops if the
two disagree.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any, Callable

from . import fakedata as fd
from .generate import SECTION_POOL
from .model import (AMOUNT_FORMATS, DATE_FORMATS, FIELD_SPECS, FIR_FORMATS, FONTS,
                    PHONE_FORMATS, SECTION_FORMATS, TIME_FORMATS, VEHICLE_FORMATS, Annotation,
                    Doc, Sentence, Signature, Stamp, Style, fmt_amount)
from .narrative import ALL_TEMPLATES, ENTITY_SLOTS, make_sentence, sentence_entities, unused_templates


@dataclass(frozen=True)
class TamperClass:
    code: str
    group: str  # none, format, field, narrative, visual, page, annotation, redaction, blur
    worked_example: str  # row number(s) in TAMPERING_DEFINITION.md section 5
    rule_ref: str  # locked decision this class exercises, for example "D42" ("" if none)
    expected_verdict: str | None  # None: depends on capture (NONE class)
    expected_severity: str | None  # None: computed from page contents (page removed)
    description: str
    applies: Callable[[Doc, int], bool]
    apply: Callable[[Doc, random.Random, int], tuple[Doc, dict[str, Any]]]


def _clone(doc: Doc) -> Doc:
    return copy.deepcopy(doc)


def _always(doc: Doc, n_pages: int) -> bool:
    return True


# ---------------------------------------------------------------------------
# Value edits
# ---------------------------------------------------------------------------

def _shift_date(iso: str, rng: random.Random, max_days: int = 1) -> str:
    d = date.fromisoformat(iso)
    delta = rng.choice([-1, 1]) * rng.randint(1, max_days)
    return (d + timedelta(days=delta)).isoformat()


def _shift_time(hhmm: str, rng: random.Random) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    h2 = (h + rng.choice([-2, -1, 1, 2])) % 24
    return f"{h2:02d}:{m:02d}"


def _one_digit(n: int, rng: random.Random) -> int:
    """Change exactly one digit (never the leading digit to zero)."""
    s = list(str(n))
    while True:
        i = rng.randrange(len(s))
        d = rng.choice([c for c in "0123456789" if c != s[i] and not (i == 0 and c == "0")])
        t = s.copy()
        t[i] = d
        return int("".join(t))


def _one_digit_str(v: str, rng: random.Random) -> str:
    idx = [i for i, c in enumerate(v) if c.isdigit()]
    i = rng.choice(idx)
    d = rng.choice([c for c in "0123456789" if c != v[i]])
    return v[:i] + d + v[i + 1:]


def _new_first_name(name: str, rng: random.Random) -> str:
    parts = name.split()
    hon = parts[0] if parts[0] in ("Shri", "Smt") else ""
    core = parts[1:] if hon else parts
    first = core[0]
    pool = fd.FEMALE_FIRST if first in fd.FEMALE_FIRST else fd.MALE_FIRST
    new_first = rng.choice([p for p in pool if p != first])
    out = [new_first] + core[1:]
    return " ".join(([hon] if hon else []) + out)


def _set_field(doc: Doc, key: str, value: Any, index: int | None = None) -> None:
    if index is None:
        doc.fields[key] = value
    else:
        lst = list(doc.fields[key])
        lst[index] = value
        doc.fields[key] = tuple(lst)


def _pick(doc: Doc, keys: list[str]) -> list[str]:
    return [k for k in keys if k in doc.fields]


def _field_edit(keys: list[str], change: Callable[[str, Any, random.Random], Any]):
    def applies(doc: Doc, n: int) -> bool:
        return bool(_pick(doc, keys))

    def apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
        d = _clone(doc)
        key = rng.choice(_pick(d, keys))
        if FIELD_SPECS[key].is_list:
            i = rng.randrange(len(d.fields[key]))
            old = d.fields[key][i]
            _set_field(d, key, change(key, old, rng), i)
            return d, {"field": key, "index": i}
        old = d.fields[key]
        _set_field(d, key, change(key, old, rng))
        return d, {"field": key}
    return applies, apply


def _chg_date(key: str, v: str, rng: random.Random) -> str:
    return _shift_date(v, rng, 1)


def _chg_time(key: str, v: str, rng: random.Random) -> str:
    return _shift_time(v, rng)


def _chg_number(key: str, v: int, rng: random.Random) -> int:
    return _one_digit(v, rng)


def _chg_name(key: str, v: str, rng: random.Random) -> str:
    return _new_first_name(v, rng)


def _chg_id(key: str, v: str, rng: random.Random) -> str:
    if key == "fir_number" or key == "charge_sheet_number":
        num, year = v.split("/")
        return f"{_one_digit(int(num), rng)}/{year}"
    if key == "phone_numbers":
        # Keep the invented "10" prefix so the edited number cannot look like a real mobile number.
        return v[:2] + _one_digit_str(v[2:], rng)
    return _one_digit_str(v, rng)


def _chg_place(key: str, v: str, rng: random.Random) -> str:
    if key == "police_station":
        return rng.choice([s for s in fd.STATION_NAMES if s != v])
    if key == "court_name":
        ctype, dist = v.rsplit(", ", 1)
        return f"{rng.choice([c for c in fd.COURT_TYPES if c != ctype])}, {dist}"
    loc, rest = v.split(", ", 1)
    return f"{rng.choice([x for x in fd.LOCALITIES if x != loc])}, {rest}"


def _chg_rank(key: str, v: str, rng: random.Random) -> str:
    return rng.choice([r for r in fd.RANKS.values() if r != v])


def _chg_address(key: str, v: str, rng: random.Random) -> str:
    head, rest = v.split(", ", 1)
    num = int(head.replace("House No. ", ""))
    return f"House No. {_one_digit(num, rng)}, {rest}"


def _section_applies(doc: Doc, n: int) -> bool:
    return "law_sections" in doc.fields


def _section_apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    secs = list(d.fields["law_sections"])
    i = rng.randrange(len(secs))
    secs[i] = rng.choice([s for s in SECTION_POOL if s not in secs])
    d.fields["law_sections"] = tuple(secs)
    return d, {"field": "law_sections", "index": i}


def _name_added_applies(doc: Doc, n: int) -> bool:
    return "accused_names" in doc.fields and len(doc.fields["accused_names"]) < 4


def _name_added_apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    used = {" ".join(x.split()[-2:]) for k in ("accused_names", "victim_names", "witness_names")
            if k in d.fields for x in d.fields[k]}
    p = fd.make_person(rng, gender="M", used=used, honorific_rate=0.15)
    d.fields["accused_names"] = d.fields["accused_names"] + (p.name,)
    if "accused_relative_names" in d.fields:
        r = fd.make_person(rng, gender="M", used=used, honorific_rate=0.3)
        d.fields["accused_relative_names"] = d.fields["accused_relative_names"] + (r.name,)
        d.relations["accused"] = tuple(d.relations["accused"]) + ("S/o",)
    if "accused_ages" in d.fields:
        d.fields["accused_ages"] = d.fields["accused_ages"] + (rng.randint(19, 60),)
    return d, {"field": "accused_names", "added": p.name}


# ---------------------------------------------------------------------------
# Narrative edits
# ---------------------------------------------------------------------------

def _narr_idx(doc: Doc, pred: Callable[[Sentence], bool]) -> list[int]:
    return [i for i, s in enumerate(doc.narrative) if pred(s)]


def _has_choice(s: Sentence) -> bool:
    return bool(ALL_TEMPLATES[s.template_id].choices)


def _has_neg(s: Sentence) -> bool:
    t = ALL_TEMPLATES[s.template_id]
    return any(s.value(k) == pos for k, (pos, _) in t.negs.items())


def _has_comma(s: Sentence) -> bool:
    return "," in ALL_TEMPLATES[s.template_id].phrasings[s.phrasing] and not s.punct_edit


def _any_sentence(s: Sentence) -> bool:
    return not s.punct_edit


def _has_entity(s: Sentence) -> bool:
    return any(k in ENTITY_SLOTS for k, _ in s.values)


def _narr_class(pred: Callable[[Sentence], bool], edit: Callable[[Sentence, random.Random], Sentence]):
    def applies(doc: Doc, n: int) -> bool:
        return bool(_narr_idx(doc, pred))

    def apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
        d = _clone(doc)
        i = rng.choice(_narr_idx(d, pred))
        sents = list(d.narrative)
        sents[i] = edit(sents[i], rng)
        d.narrative = tuple(sents)
        return d, {"sentence": i}
    return applies, apply


def _swap_word(s: Sentence, rng: random.Random) -> Sentence:
    t = ALL_TEMPLATES[s.template_id]
    slot = rng.choice(sorted(t.choices))
    return s.with_value(slot, rng.choice([c for c in t.choices[slot] if c != s.value(slot)]))


def _negate(s: Sentence, rng: random.Random) -> Sentence:
    t = ALL_TEMPLATES[s.template_id]
    slot = rng.choice([k for k, (pos, _) in t.negs.items() if s.value(k) == pos])
    return s.with_value(slot, t.negs[slot][1])


def _reword(s: Sentence, rng: random.Random) -> Sentence:
    return Sentence(s.template_id, 1 - s.phrasing, s.values, False)


def _punct(s: Sentence, rng: random.Random) -> Sentence:
    return Sentence(s.template_id, s.phrasing, s.values, True)


def _family(doc: Doc) -> str:
    return doc.meta.get("family", "A")


def _entity(s: Sentence, rng: random.Random, kinds: tuple[str, ...] | None = None) -> Sentence:
    slot = rng.choice([k for k, _ in s.values if k in ENTITY_SLOTS and (kinds is None or ENTITY_SLOTS[k] in kinds)])
    v = s.value(slot)
    kind = ENTITY_SLOTS[slot]
    if kind == "date":
        new: Any = _shift_date(v, rng, 3)
    elif kind == "time":
        new = _shift_time(v, rng)
    elif kind == "number":
        new = _one_digit(v, rng)
    elif kind == "name":
        new = _new_first_name(v, rng)
    else:
        new = _one_digit_str(v, rng)
    return s.with_value(slot, new)


def _sent_add(with_entity: bool):
    """Add one sentence. With an entity (a name, date, amount...) the change is Major (D45)."""
    def applies(doc: Doc, n: int) -> bool:
        used = {s.template_id for s in doc.narrative}
        return len(doc.narrative) >= 2 and bool(unused_templates(doc.doc_type, used, with_entity, _family(doc)))

    def apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
        d = _clone(doc)
        used = {s.template_id for s in d.narrative}
        tpl = rng.choice(unused_templates(d.doc_type, used, with_entity, _family(d)))
        new = make_sentence(tpl, _case_from(d), rng)
        pos = rng.randint(1, len(d.narrative) - 1)
        sents = list(d.narrative)
        sents.insert(pos, new)
        d.narrative = tuple(sents)
        return d, {"inserted_at": pos, "template": tpl.tid}
    return applies, apply


def _removable(doc: Doc, with_entity: bool) -> list[int]:
    """Middle sentences (not the first or last) with or without a narrative entity."""
    return [i for i in range(1, len(doc.narrative) - 1)
            if bool(sentence_entities(doc.narrative[i])) == with_entity]


def _sent_remove(with_entity: bool):
    def applies(doc: Doc, n: int) -> bool:
        return len(doc.narrative) >= 3 and bool(_removable(doc, with_entity))

    def apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
        d = _clone(doc)
        pos = rng.choice(_removable(d, with_entity))
        sents = list(d.narrative)
        del sents[pos]
        d.narrative = tuple(sents)
        return d, {"removed_at": pos}
    return applies, apply


def _case_from(doc: Doc) -> dict[str, Any]:
    """Slot values for new sentences: from the narrative first, then from the fields."""
    case: dict[str, Any] = {}
    for s in doc.narrative:
        for k, v in s.values:
            if not (k.startswith("c_") or k.startswith("n_")):
                case.setdefault(k, v)
    case.setdefault("district", doc.fields.get("district", ""))
    case.setdefault("landmark", doc.fields.get("place_of_incident", ", near the market").split(", near ")[-1])
    case.setdefault("time_incident", doc.fields.get("time_of_incident", "10:00"))
    case.setdefault("accused", doc.fields["accused_names"][0])
    case.setdefault("amount", doc.fields.get("property_value", 10000))
    return case


# ---------------------------------------------------------------------------
# Locked-rule edits added for Phase 4 (D40, D44, D46, D48)
# ---------------------------------------------------------------------------

HONORIFIC_KEYS = ["complainant_name", "complainant_relative_name", "officer_name",
                  "accused_names", "victim_names", "witness_names", "accused_relative_names"]


def _toggle_honorific(name: str) -> str:
    parts = name.split()
    if parts[0] in ("Shri", "Smt"):
        return " ".join(parts[1:])
    return ("Smt " if parts[0] in fd.FEMALE_FIRST else "Shri ") + name


def _honorific_applies(doc: Doc, n: int) -> bool:
    return bool(_pick(doc, HONORIFIC_KEYS))


def _honorific(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """Add or remove Shri or Smt on one name. Honorifics are removed before matching (D48)."""
    d = _clone(doc)
    key = rng.choice(_pick(d, HONORIFIC_KEYS))
    if FIELD_SPECS[key].is_list:
        i = rng.randrange(len(d.fields[key]))
        _set_field(d, key, _toggle_honorific(d.fields[key][i]), i)
        return d, {"field": key, "index": i}
    _set_field(d, key, _toggle_honorific(d.fields[key]))
    return d, {"field": key}


def _section_added_apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    secs = list(d.fields["law_sections"])
    added = rng.choice([x for x in SECTION_POOL if x not in secs])
    d.fields["law_sections"] = tuple(secs + [added])
    return d, {"field": "law_sections", "added": added}


ORDER_KEYS = ["accused_names", "witness_names", "victim_names"]


def _order_applies(doc: Doc, n: int) -> bool:
    return any(len(doc.fields.get(k, ())) >= 2 for k in ORDER_KEYS)


def _name_order(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """Swap two names in a list. Only the order changes, so it is Minor (D44)."""
    d = _clone(doc)
    key = rng.choice([k for k in ORDER_KEYS if len(d.fields.get(k, ())) >= 2])
    i, j = sorted(rng.sample(range(len(d.fields[key])), 2))

    def swapped(seq):
        lst = list(seq)
        lst[i], lst[j] = lst[j], lst[i]
        return tuple(lst)

    d.fields[key] = swapped(d.fields[key])
    if key == "accused_names":
        # Father's names, ages and relation markers stay paired with their accused.
        for paired in ("accused_relative_names", "accused_ages"):
            if paired in d.fields:
                d.fields[paired] = swapped(d.fields[paired])
        d.relations["accused"] = swapped(d.relations["accused"])
    return d, {"field": key, "swapped": [i, j]}


def _id_space_applies(doc: Doc, n: int) -> bool:
    return len(doc.fields["fir_number"].split("/")[0]) >= 2 or "officer_id" in doc.fields


def _id_space(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """Insert a space inside an ID. Inside a value this is content, not format (D40)."""
    d = _clone(doc)
    num, year = d.fields["fir_number"].split("/")
    if len(num) >= 2 and rng.random() < 0.6:
        k = rng.randint(1, len(num) - 1)
        d.fields["fir_number"] = f"{num[:k]} {num[k:]}/{year}"
        return d, {"field": "fir_number"}
    oid = d.fields["officer_id"]
    k = rng.randint(4, len(oid) - 1)  # inside the digits after the "ZZP" prefix
    d.fields["officer_id"] = f"{oid[:k]} {oid[k:]}"
    return d, {"field": "officer_id"}


OVER_KEYS = ["date_of_incident", "date_of_report", "property_value", "fir_number", "police_station"]


def _note_over_applies(doc: Doc, n: int) -> bool:
    return bool(_pick(doc, OVER_KEYS))


def _note_over_field(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """An unsealed ink note over a critical field is Major (D46)."""
    d = _clone(doc)
    key = rng.choice(_pick(d, OVER_KEYS))
    d.annotations = d.annotations + (Annotation("over_field", (rng.choice(["corrected", "see note", "checked"]),), 0, over=key),)
    return d, {"over": key}


# ---------------------------------------------------------------------------
# Visual, page, annotation, redaction and blur edits
# ---------------------------------------------------------------------------

def _stamp_removed(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    d.stamps = tuple(s for s in d.stamps if s.kind != "ps")
    return d, {"stamp": "ps"}


def _stamp_swapped(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    new_station = rng.choice([s for s in fd.STATION_NAMES if s != d.fields["police_station"]])
    out = []
    for s in d.stamps:
        if s.kind == "ps":
            ring = f"POLICE STATION {new_station.upper()} * {d.fields['district'].upper()} *"
            s = replace(s, ring_text=ring)
        out.append(s)
    d.stamps = tuple(out)
    return d, {"stamp": "ps", "new_station": new_station}


def _sig_swapped(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    i = rng.randrange(len(d.signatures))
    sigs = list(d.signatures)
    sigs[i] = Signature(sigs[i].who, rng.randint(1, 10**9))
    d.signatures = tuple(sigs)
    return d, {"signature": sigs[i].who}


def _pages_at_least(k: int) -> Callable[[Doc, int], bool]:
    return lambda doc, n: n >= k


def _page_added(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    used = {s.template_id for s in d.narrative}
    pool = unused_templates(d.doc_type, used, family=_family(d))
    case = _case_from(d)
    k = min(len(pool), rng.randint(4, 6))
    d.extra_page = tuple(make_sentence(t, case, rng) for t in rng.sample(pool, k))
    d.extra_page_after = rng.randint(0, n - 2) if n >= 2 else 0
    return d, {"after_page": d.extra_page_after + 1, "sentences": k}


def _page_removed(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    d.removed_page = rng.randrange(n)
    return d, {"page": d.removed_page + 1}


def _page_reorder(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    i, j = sorted(rng.sample(range(n), 2))
    d.swapped_pages = (i, j)
    return d, {"pages": [i + 1, j + 1]}


NOTES: list[tuple[str, ...]] = [
    ("Seen.", "Put up with file.", "-- initials"),
    ("Copy received.", "Checked with original.",),
    ("Noted.", "Keep in case file.", "-- SHO"),
]


def _margin_note(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    d.annotations = d.annotations + (Annotation("margin_note", rng.choice(NOTES), 0),)
    return d, {"page": 1}


def _court_stamp(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    dist = d.fields["district"]
    base = date.fromisoformat(d.fields.get("charge_sheet_date") or d.fields.get("date_of_statement")
                              or d.fields["date_of_report"])
    recv = base + timedelta(days=rng.randint(1, 10))
    st = Stamp(kind="court", ring_text=f"COURT OF JMFC, {dist.upper()}",
               center_text=f"Date: {recv.day:02d}/{recv.month:02d}/{recv.year}", page=0,
               color=(0.72, 0.1, 0.12), angle=rng.uniform(-6, 6))
    d.stamps = d.stamps + (st,)
    return d, {"page": 1}


REDACT_KEYS = ["victim_names", "witness_names"]


def _redact_applies(doc: Doc, n: int) -> bool:
    return bool(_pick(doc, REDACT_KEYS))


def _redact(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    key = _pick(d, REDACT_KEYS)[0]
    i = rng.randrange(len(d.fields[key]))
    d.redacted = frozenset({f"{key}[{i}]"})
    return d, {"field": key, "index": i}


# Fields that are always on page 1 and short enough to blur cleanly.
BLUR_KEYS = ["fir_number", "date_of_incident", "date_of_report", "property_value",
             "date_of_statement", "charge_sheet_number", "police_station"]


def _blur_applies(doc: Doc, n: int) -> bool:
    return len(_pick(doc, BLUR_KEYS)) >= 2


def _blur_only(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    key = rng.choice(_pick(d, BLUR_KEYS))
    d.blurred = frozenset({key})
    return d, {"blurred": key}


EDIT_FOR_BLUR: dict[str, Callable[[str, Any, random.Random], Any]] = {
    "date_of_incident": _chg_date, "date_of_report": _chg_date, "date_of_statement": _chg_date,
    "property_value": _chg_number, "fir_number": _chg_id, "charge_sheet_number": _chg_id,
    "police_station": _chg_place,
}


def _blur_plus_edit(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    blur_key, edit_key = rng.sample(_pick(d, BLUR_KEYS), 2)
    _set_field(d, edit_key, EDIT_FOR_BLUR[edit_key](edit_key, d.fields[edit_key], rng))
    d.blurred = frozenset({blur_key})
    return d, {"blurred": blur_key, "field": edit_key}


# ---------------------------------------------------------------------------
# Format edits (content unchanged)
# ---------------------------------------------------------------------------

def _style_edit(change: Callable[[Style, Doc, random.Random], Style]):
    def apply(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
        d = _clone(doc)
        d.style = change(d.style, d, rng)
        return d, {"style": {k: v for k, v in d.style.__dict__.items() if doc.style.__dict__[k] != v}}
    return apply


def _other(cur: Any, options: tuple[Any, ...] | list[Any], rng: random.Random) -> Any:
    return rng.choice([o for o in options if o != cur])


def _f_font(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, font=_other(s.font, FONTS, rng))


def _f_reflow(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, font_size=_other(s.font_size, [10.0, 10.5, 11.0, 11.5], rng),
                   margin=_other(s.margin, [52.0, 56.0, 62.0, 70.0, 76.0], rng))


def _f_spacing(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, leading=_other(s.leading, [1.25, 1.3, 1.4, 1.55], rng),
                   word_space=_other(s.word_space, [0.0, 1.5, 2.5], rng))


def _f_datetime(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, date_fmt=_other(s.date_fmt, DATE_FORMATS, rng),
                   time_fmt=_other(s.time_fmt, TIME_FORMATS, rng))


def _f_number(s: Style, d: Doc, rng: random.Random) -> Style:
    amount = d.fields.get("property_value")
    fmts = [f for f in AMOUNT_FORMATS if amount is None or
            fmt_amount(amount, replace(s, amount_fmt=f)) != fmt_amount(amount, s)]
    out = replace(s, vehicle_fmt=_other(s.vehicle_fmt, VEHICLE_FORMATS, rng),
                  fir_fmt=_other(s.fir_fmt, FIR_FORMATS, rng),
                  phone_fmt=_other(s.phone_fmt, PHONE_FORMATS, rng))
    if fmts:
        out = replace(out, amount_fmt=rng.choice(fmts))
    return out


def _f_section(s: Style, d: Doc, rng: random.Random) -> Style:
    n = len(d.fields.get("law_sections", ()))
    order = None
    if n >= 2:
        perm = list(range(n))
        while perm == list(range(n)):
            rng.shuffle(perm)
        order = tuple(perm)
    return replace(s, section_fmt=_other(s.section_fmt, SECTION_FORMATS, rng), section_order=order)


def _f_name_case(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, name_upper=not s.name_upper)


def _f_metadata(s: Style, d: Doc, rng: random.Random) -> Style:
    return replace(s, pdf_title=s.pdf_title + " (copy)", pdf_author="Records section",
                   pdf_subject="Copy for file", pdf_creator=f"scanner-suite {rng.randint(2, 9)}.{rng.randint(0, 9)}")


# ---------------------------------------------------------------------------
# FIR-Tamper v3 Stage 2 classes (D96): E7, E9, E12, E13, E14 and entity kinds
# ---------------------------------------------------------------------------

def _has_entity_kind(kinds: tuple[str, ...]) -> Callable[[Sentence], bool]:
    return lambda s: any(k in ENTITY_SLOTS and ENTITY_SLOTS[k] in kinds for k, _ in s.values)


def _entity_kind(kinds: tuple[str, ...]) -> Callable[[Sentence, random.Random], Sentence]:
    return lambda s, rng: _entity(s, rng, kinds)


def _has_modal(s: Sentence) -> bool:
    t = ALL_TEMPLATES[s.template_id]
    return any(s.value(k) == base for k, (base, _) in t.mods.items())


def _modal(s: Sentence, rng: random.Random) -> Sentence:
    """Shift one modal or quantifier in place ("saw" to "think I saw", "all" to "some of")."""
    t = ALL_TEMPLATES[s.template_id]
    slot = rng.choice([k for k, (base, _) in t.mods.items() if s.value(k) == base])
    return s.with_value(slot, t.mods[slot][1])


def _first_name_of(name: str) -> str:
    parts = name.split()
    return parts[1] if parts[0] in ("Shri", "Smt") and len(parts) > 1 else parts[0]


def _role_swap_applies(doc: Doc, n: int) -> bool:
    # Only a male complainant: the narratives refer to the accused as "he".
    return ("complainant_name" in doc.fields and "accused_names" in doc.fields
            and _first_name_of(doc.fields["complainant_name"]) in fd.MALE_FIRST)


def _role_swap(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """Complainant and first accused swap roles in the fields and in the narrative (E7)."""
    d = _clone(doc)
    comp, acc = d.fields["complainant_name"], d.fields["accused_names"][0]
    d.fields["complainant_name"] = acc
    _set_field(d, "accused_names", comp, 0)
    if "complainant_relative_name" in d.fields and "accused_relative_names" in d.fields:
        c_rel, a_rel = d.fields["complainant_relative_name"], d.fields["accused_relative_names"][0]
        d.fields["complainant_relative_name"] = a_rel
        _set_field(d, "accused_relative_names", c_rel, 0)
        acc_rel = list(d.relations["accused"])
        d.relations["complainant"], acc_rel[0] = acc_rel[0], d.relations["complainant"]
        d.relations["accused"] = tuple(acc_rel)
    sents = []
    for sen in d.narrative:
        vals = dict(sen.values)
        if vals.get("complainant") == comp:
            sen = sen.with_value("complainant", acc)
        if vals.get("accused") == acc:
            sen = sen.with_value("accused", comp)
        sents.append(sen)
    d.narrative = tuple(sents)
    return d, {"fields": ["complainant_name", "accused_names"]}


def _swap_item_word(item: str, rng: random.Random) -> str:
    """Change the colour or the quantity word of a property item description."""
    name, rest = item.split(" (", 1)
    colour, qty = rest.split("), quantity: ")
    if rng.random() < 0.5:
        colour = rng.choice([c for c in fd.ITEM_COLOURS if c != colour])
    else:
        qty = rng.choice([q for q in fd.QTY_WORDS if q != qty])
    return f"{name} ({colour}), quantity: {qty}"


def _custody_applies(min_entries: int) -> Callable[[Doc, int], bool]:
    return lambda doc, n: len(doc.fields.get("custody_holders", ())) >= min_entries


def _custody_holder(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    i = rng.randrange(len(d.fields["custody_holders"]))
    _set_field(d, "custody_holders", _new_first_name(d.fields["custody_holders"][i], rng), i)
    return d, {"field": "custody_holders", "index": i}


def _custody_date(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    d = _clone(doc)
    i = rng.randrange(len(d.fields["custody_dates"]))
    _set_field(d, "custody_dates", _shift_date(d.fields["custody_dates"][i], rng, 3), i)
    return d, {"field": "custody_dates", "index": i}


def _custody_removed(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """One custody entry (holder, date and purpose) removed from the chain."""
    d = _clone(doc)
    i = rng.randrange(1, len(d.fields["custody_holders"]))
    for key in ("custody_holders", "custody_dates"):
        lst = list(d.fields[key])
        del lst[i]
        d.fields[key] = tuple(lst)
    purposes = list(d.relations["custody"])
    del purposes[i]
    d.relations["custody"] = tuple(purposes)
    return d, {"removed_entry": i + 1}


# BNS commencement date (D26, D34). TODO: verify against the official notification (Phase 25).
BNS_START = date(2024, 7, 1)
DATE_KEYS = ["date_of_report", "date_of_incident", "date_of_statement", "charge_sheet_date", "seizure_date"]


def _backdate_applies(doc: Doc, n: int) -> bool:
    return "law_sections" in doc.fields and "date_of_report" in doc.fields


def _backdate(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    """Move every date of the document to before the BNS commencement date (E14).

    The document still cites BNS sections, so the printed dates are an anachronism (the
    backdating rule of Phase 25). FIR and charge sheet years follow the new dates.
    """
    d = _clone(doc)
    # Shift by the latest date in the document, so that every date (including the charge
    # sheet date and the custody chain) lands before the commencement date.
    all_dates = [d.fields[k] for k in DATE_KEYS if k in d.fields] + list(d.fields.get("custody_dates", ()))
    latest = max(date.fromisoformat(x) for x in all_dates)
    offset = (BNS_START - timedelta(days=rng.randint(10, 400))) - latest
    target = date.fromisoformat(d.fields["date_of_report"]) + offset

    def move(iso: str) -> str:
        return (date.fromisoformat(iso) + offset).isoformat()

    for key in DATE_KEYS:
        if key in d.fields:
            d.fields[key] = move(d.fields[key])
    if "custody_dates" in d.fields:
        d.fields["custody_dates"] = tuple(move(x) for x in d.fields["custody_dates"])
    num, _ = d.fields["fir_number"].split("/")
    d.fields["fir_number"] = f"{num}/{target.year}"
    if "charge_sheet_number" in d.fields:
        cs_num, _ = d.fields["charge_sheet_number"].split("/")
        d.fields["charge_sheet_number"] = f"{cs_num}/{date.fromisoformat(d.fields['charge_sheet_date']).year}"
    d.narrative = tuple(sen.with_value("date_incident", move(sen.value("date_incident")))
                        if "date_incident" in dict(sen.values) else sen for sen in d.narrative)
    return d, {"date_of_report": d.fields["date_of_report"], "bns_start": BNS_START.isoformat(),
               "anachronism": True}


def _none(doc: Doc, rng: random.Random, n: int) -> tuple[Doc, dict[str, Any]]:
    return _clone(doc), {}


def _sections_present(doc: Doc, n: int) -> bool:
    return "law_sections" in doc.fields


_ap = _field_edit  # short alias
_T, _M = "Tampered", "Major"

# Columns: code, group, worked example row(s) in TAMPERING_DEFINITION.md section 6,
# locked decision it implements, expected verdict, expected severity, description.
CLASSES: list[TamperClass] = [
    TamperClass("NONE", "none", "1", "", None, "None", "Unchanged copy", _always, _none),
    # Format and capture only. Expected Equivalent.
    TamperClass("F_FONT", "format", "4", "", "Equivalent", "None", "Reprint in another font", _always, _style_edit(_f_font)),
    TamperClass("F_REFLOW", "format", "12", "D40", "Equivalent", "None", "Font size and margins changed, text reflows", _always, _style_edit(_f_reflow)),
    TamperClass("F_SPACING", "format", "12", "D40", "Equivalent", "None", "Line and word spacing changed only", _always, _style_edit(_f_spacing)),
    TamperClass("F_DATETIME_FORMAT", "format", "6, 8", "", "Equivalent", "None", "Same dates and times written in another format", _always, _style_edit(_f_datetime)),
    TamperClass("F_NUMBER_FORMAT", "format", "7, 13", "D40", "Equivalent", "None", "Same amount, vehicle, phone and FIR numbers written with other standard separators", _always, _style_edit(_f_number)),
    TamperClass("F_SECTION_FORMAT", "format", "10, 14", "D44", "Equivalent", "None", "Same law sections written another way and listed in another order", _sections_present, _style_edit(_f_section)),
    TamperClass("F_NAME_CASE", "format", "11", "", "Equivalent", "None", "Names in field rows printed in another letter case", _always, _style_edit(_f_name_case)),
    TamperClass("F_METADATA", "format", "5", "", "Equivalent", "None", "PDF metadata changed only", _always, _style_edit(_f_metadata)),
    TamperClass("F_HONORIFIC", "format", "9", "D48", "Equivalent", "None", "Shri or Smt added to or removed from one name", _honorific_applies, _honorific),
    # Field edits.
    TamperClass("T_DATE", "field", "16", "", _T, _M, "A date field changed by one day",
                *_ap(["date_of_incident", "date_of_report", "date_of_statement", "charge_sheet_date"], _chg_date)),
    TamperClass("T_TIME", "field", "17", "", _T, _M, "A time field changed",
                *_ap(["time_of_incident", "time_of_report"], _chg_time)),
    TamperClass("T_AMOUNT", "field", "18", "", _T, _M, "Property value changed by one digit",
                *_ap(["property_value"], _chg_number)),
    TamperClass("T_AGE", "field", "18 (same rule)", "", _T, _M, "Age of an accused changed by one digit",
                *_ap(["accused_ages"], _chg_number)),
    TamperClass("T_NAME", "field", "19", "", _T, _M, "A person's first name changed",
                *_ap(["complainant_name", "complainant_relative_name", "accused_names", "accused_relative_names",
                      "victim_names", "witness_names", "officer_name"], _chg_name)),
    TamperClass("T_NAME_ADDED", "field", "20", "", _T, _M, "An extra accused added", _name_added_applies, _name_added_apply),
    TamperClass("T_SECTION", "field", "21", "D44", _T, _M, "One law section replaced by another", _section_applies, _section_apply),
    TamperClass("T_SECTION_ADDED", "field", "22", "D44", _T, _M, "A law section added", _section_applies, _section_added_apply),
    TamperClass("T_VEHICLE", "field", "23", "", _T, _M, "One character of a vehicle number changed",
                *_ap(["vehicle_numbers"], lambda k, v, r: _one_digit_str(v, r))),
    TamperClass("T_ID", "field", "23 (same rule)", "", _T, _M, "One digit of an FIR, charge sheet, officer ID or phone number changed",
                *_ap(["fir_number", "charge_sheet_number", "officer_id", "phone_numbers"], _chg_id)),
    TamperClass("T_ID_SPACE", "field", "24", "D40", _T, _M, "A space inserted inside an FIR number or officer ID", _id_space_applies, _id_space),
    TamperClass("T_PLACE", "field", "16 (same rule)", "", _T, _M, "Police station, place of incident or court changed",
                *_ap(["police_station", "place_of_incident", "court_name"], _chg_place)),
    TamperClass("T_RANK", "field", "16 (same rule)", "", _T, _M, "Officer rank changed",
                *_ap(["officer_rank"], _chg_rank)),
    TamperClass("T_ADDRESS", "field", "26", "", _T, "Minor", "Complainant address changed (non-critical field)",
                *_ap(["complainant_address"], _chg_address)),
    TamperClass("T_NAME_ORDER", "field", "25", "D44", _T, "Minor", "Two names in a list swapped (order only)", _order_applies, _name_order),
    # Narrative edits.
    TamperClass("N_WORD_SWAP", "narrative", "27", "", _T, "Minor", "One word swapped in the narrative", *_narr_class(_has_choice, _swap_word)),
    TamperClass("N_NEGATION", "narrative", "28", "D42", _T, _M, "Negation added (did -> did not)", *_narr_class(_has_neg, _negate)),
    TamperClass("N_ENTITY", "narrative", "29, 30", "D45", _T, _M, "A date, time, name, amount or vehicle changed inside the narrative only", *_narr_class(_has_entity, _entity)),
    TamperClass("N_SENTENCE_ADD", "narrative", "31", "", _T, "Minor", "A sentence with no narrative entity added", *_sent_add(False)),
    TamperClass("N_SENTENCE_ADD_ENTITY", "narrative", "32", "D45", _T, _M, "A sentence with a narrative entity added", *_sent_add(True)),
    TamperClass("N_SENTENCE_REMOVE", "narrative", "33", "", _T, "Minor", "A sentence with no narrative entity removed", *_sent_remove(False)),
    TamperClass("N_SENTENCE_REMOVE_ENTITY", "narrative", "32 (removal)", "D45", _T, _M, "A sentence with a narrative entity removed", *_sent_remove(True)),
    TamperClass("N_REWORD", "narrative", "34", "", _T, "Minor", "A sentence reworded with the same meaning", *_narr_class(_any_sentence, _reword)),
    TamperClass("N_PUNCT", "narrative", "35", "", _T, "Minor", "One comma removed", *_narr_class(_has_comma, _punct)),
    # Visual edits.
    TamperClass("V_STAMP_REMOVED", "visual", "36", "", _T, _M, "Police station seal removed", _always, _stamp_removed),
    TamperClass("V_STAMP_SWAPPED", "visual", "37", "", _T, _M, "Seal of another police station", _always, _stamp_swapped),
    TamperClass("V_SIGNATURE_SWAPPED", "visual", "38", "", _T, _M, "A signature replaced by a different one", _always, _sig_swapped),
    TamperClass("A_COURT_STAMP", "annotation", "39", "D46", _T, _M, "Court receipt stamp added (a stamp or seal is a visual change)", _always, _court_stamp),
    # Page edits (D43).
    TamperClass("P_PAGE_ADDED", "page", "40", "D43", _T, _M, "A page of extra narrative inserted", _pages_at_least(2), _page_added),
    TamperClass("P_PAGE_REMOVED", "page", "41", "D43", _T, _M, "A page removed", _pages_at_least(2), _page_removed),
    TamperClass("P_PAGE_REORDER", "page", "42", "D43", _T, _M, "Two pages swapped", _pages_at_least(2), _page_reorder),
    # Unsealed annotations (D46).
    TamperClass("A_MARGIN_NOTE", "annotation", "43", "D46", _T, "Minor", "Handwritten-style note in a blank margin (flagged)", _always, _margin_note),
    TamperClass("A_NOTE_OVER_FIELD", "annotation", "44", "D46", _T, _M, "Handwritten-style note and pen stroke over a critical field", _note_over_applies, _note_over_field),
    # Blur: a clear edit wins; unreadable fields are listed as "could not verify" (D41).
    TamperClass("B_BLUR_ONLY", "blur", "47", "D41", "Inconclusive", "None", "One critical field blurred, nothing edited", _blur_applies, _blur_only),
    TamperClass("B_BLUR_PLUS_EDIT", "blur", "48", "D41", _T, _M, "One critical field blurred while another has a clear edit", _blur_applies, _blur_plus_edit),
    # Redaction: not supported in v1 (D47).
    TamperClass("R_REDACTED", "redaction", "51", "D47", "Not supported", "None", "A victim or witness name blacked out", _redact_applies, _redact),
    # v3 Stage 2 (D96). Entity edits of one kind, so E1 to E4 can be assigned directly.
    TamperClass("N_ENTITY_NAME", "narrative", "30", "D45", _T, _M, "A name changed inside the narrative only",
                *_narr_class(_has_entity_kind(("name",)), _entity_kind(("name",)))),
    TamperClass("N_ENTITY_DATE", "narrative", "29", "D45", _T, _M, "A date changed inside the narrative only",
                *_narr_class(_has_entity_kind(("date",)), _entity_kind(("date",)))),
    TamperClass("N_ENTITY_TIME", "narrative", "29 (same rule)", "D45", _T, _M, "A time changed inside the narrative only",
                *_narr_class(_has_entity_kind(("time",)), _entity_kind(("time",)))),
    TamperClass("N_ENTITY_NUMBER", "narrative", "29 (same rule)", "D45", _T, _M, "An amount or vehicle number changed inside the narrative only",
                *_narr_class(_has_entity_kind(("number", "id")), _entity_kind(("number", "id")))),
    TamperClass("E_ROLE_SWAP", "field", "19 (same rule)", "", _T, _M, "Complainant and accused swap roles (fields and narrative)",
                _role_swap_applies, _role_swap),
    TamperClass("E_EXHIBIT_ID", "field", "23 (same rule)", "", _T, _M, "One digit of an exhibit ID changed",
                *_ap(["exhibit_ids"], _chg_id)),
    TamperClass("E_EXHIBIT_DESC", "field", "16 (same rule)", "", _T, _M, "Colour or quantity of a property item changed",
                *_ap(["property_items"], lambda k, v, r: _swap_item_word(v, r))),
    TamperClass("N_MODAL", "narrative", "27 (same rule)", "", _T, "Minor", "One modal or quantifier shifted (saw to think I saw, all to some of)",
                *_narr_class(_has_modal, _modal)),
    TamperClass("C_CUSTODY_HOLDER", "field", "19 (same rule)", "", _T, _M, "A custody holder's name changed",
                _custody_applies(1), _custody_holder),
    TamperClass("C_CUSTODY_DATE", "field", "16 (same rule)", "", _T, _M, "A custody date shifted",
                _custody_applies(1), _custody_date),
    TamperClass("C_CUSTODY_ENTRY_REMOVED", "field", "20 (same rule)", "", _T, _M, "One custody entry removed from the chain",
                _custody_applies(2), _custody_removed),
    TamperClass("T_BACKDATE", "field", "16 (same rule)", "D52", _T, _M, "All dates moved before the BNS commencement date while BNS is cited",
                _backdate_applies, _backdate),
]

BY_CODE: dict[str, TamperClass] = {c.code: c for c in CLASSES}
FORMAT_CODES: list[str] = [c.code for c in CLASSES if c.group == "format"]
CONTENT_CODES: list[str] = [c.code for c in CLASSES if c.group not in ("none", "format")]
