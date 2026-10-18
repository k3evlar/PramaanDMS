"""Document model for the FIR-Tamper dataset.

A document is stored as canonical values (ISO dates, integers, rank codes and so
on). How it looks on the page is set by a separate Style. So a format change
only touches the Style, and a content change only touches the canonical values.
Labels are computed by comparing canonical values (see labels.py), which keeps
them correct by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .fakedata import RANKS

DOC_TYPES: tuple[str, ...] = ("FIR", "STATEMENT", "CHARGESHEET")
DOC_PREFIX: dict[str, str] = {"FIR": "FIR", "STATEMENT": "STM", "CHARGESHEET": "CS"}


@dataclass(frozen=True)
class FieldSpec:
    row: int  # row number in docs/CRITICAL_FIELDS.md
    ftype: str  # date, time, number, name, place, section, id, text
    critical: bool
    found_in: frozenset[str]
    is_list: bool = False


_F, _S, _C = "FIR", "STATEMENT", "CHARGESHEET"

# Field keys mirror docs/CRITICAL_FIELDS.md section 1. Row 24 is split into two keys.
# Row 27 (narrative) is not a field; it is the narrative sentence list. Row 31 is split
# into two paired lists (holder and date of each custody entry).
FIELD_SPECS: dict[str, FieldSpec] = {
    "fir_number": FieldSpec(1, "id", True, frozenset({_F, _S, _C})),
    "police_station": FieldSpec(2, "place", True, frozenset({_F, _S, _C})),
    "district": FieldSpec(3, "place", True, frozenset({_F, _S, _C})),
    "date_of_report": FieldSpec(4, "date", True, frozenset({_F, _C})),
    "time_of_report": FieldSpec(5, "time", True, frozenset({_F})),
    "date_of_incident": FieldSpec(6, "date", True, frozenset({_F, _S, _C})),
    "time_of_incident": FieldSpec(7, "time", True, frozenset({_F, _S})),
    "place_of_incident": FieldSpec(8, "place", True, frozenset({_F, _S, _C})),
    "complainant_name": FieldSpec(9, "name", True, frozenset({_F, _C})),
    "complainant_relative_name": FieldSpec(10, "name", True, frozenset({_F})),
    "accused_names": FieldSpec(11, "name", True, frozenset({_F, _S, _C}), is_list=True),
    "accused_relative_names": FieldSpec(12, "name", True, frozenset({_F, _C}), is_list=True),
    "accused_ages": FieldSpec(13, "number", True, frozenset({_F, _C}), is_list=True),
    "victim_names": FieldSpec(14, "name", True, frozenset({_F, _C}), is_list=True),
    "witness_names": FieldSpec(15, "name", True, frozenset({_S, _C}), is_list=True),
    "law_sections": FieldSpec(16, "section", True, frozenset({_F, _C}), is_list=True),
    "property_value": FieldSpec(17, "number", True, frozenset({_F, _C})),
    "vehicle_numbers": FieldSpec(18, "id", True, frozenset({_F, _S, _C}), is_list=True),
    "phone_numbers": FieldSpec(19, "id", True, frozenset({_F, _S}), is_list=True),
    "officer_name": FieldSpec(20, "name", True, frozenset({_F, _S, _C})),
    "officer_rank": FieldSpec(21, "text", True, frozenset({_F, _S, _C})),
    "officer_id": FieldSpec(22, "id", True, frozenset({_F, _S, _C})),
    "date_of_statement": FieldSpec(23, "date", True, frozenset({_S})),
    "charge_sheet_number": FieldSpec(24, "id", True, frozenset({_C})),
    "charge_sheet_date": FieldSpec(24, "date", True, frozenset({_C})),
    "court_name": FieldSpec(25, "place", True, frozenset({_C})),
    "complainant_address": FieldSpec(26, "place", False, frozenset({_F})),
    # Rows 28 to 31 were added for FIR-Tamper v3 Stage 2 (D96): evidence and custody.
    "property_items": FieldSpec(28, "text", True, frozenset({_F, _C}), is_list=True),
    "exhibit_ids": FieldSpec(29, "id", True, frozenset({_C}), is_list=True),
    "seizure_date": FieldSpec(30, "date", True, frozenset({_C})),
    "custody_holders": FieldSpec(31, "name", True, frozenset({_C}), is_list=True),
    "custody_dates": FieldSpec(31, "date", True, frozenset({_C}), is_list=True),
}


def fields_for(doc_type: str) -> list[str]:
    return [k for k, s in FIELD_SPECS.items() if doc_type in s.found_in]


@dataclass(frozen=True)
class Style:
    """Everything about how a document looks. None of it is content."""

    font: str = "Helvetica"
    font_size: float = 10.5
    leading: float = 1.35
    margin: float = 60.0
    word_space: float = 0.0
    date_fmt: str = "dmy_slash"
    time_fmt: str = "24h"
    amount_fmt: str = "indian_rs"
    vehicle_fmt: str = "spaced"
    phone_fmt: str = "plain"
    fir_fmt: str = "slash"
    section_fmt: str = "us"
    section_order: tuple[int, ...] | None = None  # display order of law sections
    name_upper: bool = False
    pdf_title: str = ""
    pdf_author: str = "Pramaan FIR-Tamper generator"
    pdf_subject: str = "Synthetic document"
    pdf_creator: str = "pramaan-dataset"


@dataclass(frozen=True)
class Sentence:
    """One narrative sentence: a template, which phrasing of it, and its slot values."""

    template_id: str
    phrasing: int
    values: tuple[tuple[str, Any], ...]
    punct_edit: bool = False  # True when one comma has been removed

    def value(self, slot: str) -> Any:
        return dict(self.values)[slot]

    def with_value(self, slot: str, new: Any) -> "Sentence":
        vals = tuple((k, new if k == slot else v) for k, v in self.values)
        return Sentence(self.template_id, self.phrasing, vals, self.punct_edit)

    def identity(self) -> tuple[Any, ...]:
        """What makes this sentence's content. Phrasing and punctuation are content."""
        return (self.template_id, self.phrasing, self.values, self.punct_edit)


@dataclass(frozen=True)
class Stamp:
    kind: str  # "ps" (police station seal) or "court" (court receipt stamp)
    ring_text: str
    center_text: str
    page: int  # -1 means last page
    color: tuple[float, float, float]
    angle: float


@dataclass(frozen=True)
class Signature:
    who: str  # "officer", "complainant" or "witness"
    seed: int


@dataclass(frozen=True)
class Annotation:
    kind: str  # "margin_note" (blank margin) or "over_field" (ink over a field)
    lines: tuple[str, ...]
    page: int
    over: str | None = None  # box key of the field the note covers, if any (D46)


@dataclass
class Doc:
    doc_id: str
    doc_type: str
    scenario: str
    fields: dict[str, Any]
    relations: dict[str, Any]  # printed relation markers (S/o, D/o, W/o); not fields
    narrative: tuple[Sentence, ...]
    stamps: tuple[Stamp, ...]
    signatures: tuple[Signature, ...]
    style: Style
    annotations: tuple[Annotation, ...] = ()
    redacted: frozenset[str] = frozenset()  # box keys such as "victim_names[0]"
    blurred: frozenset[str] = frozenset()  # box keys blurred at raster stage
    removed_page: int | None = None  # 0-based original page index
    swapped_pages: tuple[int, int] | None = None
    extra_page: tuple[Sentence, ...] = ()
    extra_page_after: int | None = None  # insert after this 0-based page index
    meta: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Display formatting (style -> printed text). Normalization is the inverse.
# ---------------------------------------------------------------------------

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

DATE_FORMATS = ("dmy_slash", "dmy_dash", "dmy_dot", "d_month_y", "dth_mon_y")
TIME_FORMATS = ("24h", "12h", "hrs")
AMOUNT_FORMATS = ("indian_rs", "plain_rs", "indian_dec", "lakh_words")
VEHICLE_FORMATS = ("spaced", "dashed", "compact")
PHONE_FORMATS = ("plain", "plus91")
FIR_FORMATS = ("slash", "padded")
SECTION_FORMATS = ("us", "section_of", "plain", "bns_sec")
FONTS = ("Helvetica", "Times-Roman", "Courier")


def _ordinal(d: int) -> str:
    if 10 <= d % 100 <= 20:
        return f"{d}th"
    return f"{d}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th') }"


def fmt_date(iso: str, style: Style) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    f = style.date_fmt
    if f == "dmy_slash":
        return f"{d:02d}/{m:02d}/{y}"
    if f == "dmy_dash":
        return f"{d:02d}-{m:02d}-{y}"
    if f == "dmy_dot":
        return f"{d:02d}.{m:02d}.{y}"
    if f == "d_month_y":
        return f"{d} {MONTHS[m - 1]} {y}"
    return f"{_ordinal(d)} {MONTHS[m - 1][:3]} {y}"


def fmt_time(hhmm: str, style: Style) -> str:
    h, mi = (int(x) for x in hhmm.split(":"))
    if style.time_fmt == "24h":
        return f"{h:02d}:{mi:02d}"
    if style.time_fmt == "hrs":
        return f"{h:02d}.{mi:02d} hrs"
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{mi:02d} {suffix}"


def _indian_group(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def fmt_amount(n: int, style: Style) -> str:
    f = style.amount_fmt
    if f == "lakh_words" and n >= 100000 and n % 100000 == 0:
        return f"Rs {n // 100000} lakh"
    if f == "plain_rs":
        return f"Rs. {n}"
    if f == "indian_dec":
        return f"Rs. {_indian_group(n)}.00"
    return f"Rs {_indian_group(n)}/-"


def fmt_vehicle(v: str, style: Style) -> str:
    parts = [v[0:2], v[2:4], v[4:6], v[6:]]
    if style.vehicle_fmt == "dashed":
        return "-".join(parts)
    if style.vehicle_fmt == "compact":
        return v
    return " ".join(parts)


def fmt_phone(p: str, style: Style) -> str:
    if style.phone_fmt == "plus91":
        return f"+91 {p[:5]} {p[5:]}"
    return p


def fmt_fir(fir: str, style: Style) -> str:
    num, _, year = fir.partition("/")
    if not num.isdigit():
        # A tampered value such as "14 2/2026" is printed exactly as it is (D40).
        return fir
    if style.fir_fmt == "padded":
        return f"{int(num):04d}/{year}"
    return f"{int(num)}/{year}"


def _sec_num(code: str) -> str:
    return code.split(":", 1)[1]


def ordered_sections(sections: tuple[str, ...], style: Style) -> list[str]:
    if style.section_order and len(style.section_order) == len(sections):
        return [sections[i] for i in style.section_order]
    return list(sections)


def fmt_sections(sections: tuple[str, ...], style: Style) -> str:
    nums = [_sec_num(c) for c in ordered_sections(sections, style)]
    f = style.section_fmt
    if f == "section_of":
        if len(nums) == 1:
            return f"Section {nums[0]} of BNS"
        return "Sections " + ", ".join(nums[:-1]) + f" and {nums[-1]} of BNS"
    if f == "plain":
        return ", ".join(f"{n} BNS" for n in nums)
    if f == "bns_sec":
        return "BNS Sec. " + ", ".join(nums)
    return "u/s " + ", ".join(nums) + " BNS"


def fmt_name(name: str, style: Style) -> str:
    return name.upper() if style.name_upper else name


RANK_DISPLAY: dict[str, str] = {code: disp for disp, code in RANKS.items()}


def fmt_rank(code: str, style: Style) -> str:
    return RANK_DISPLAY[code]


def fmt_value(ftype: str, key: str, value: Any, style: Style) -> str:
    """Printed text for one scalar value of a field."""
    if ftype == "date":
        return fmt_date(value, style)
    if ftype == "time":
        return fmt_time(value, style)
    if key == "property_value":
        return fmt_amount(value, style)
    if key == "accused_ages":
        return f"{value} years"
    if key == "vehicle_numbers":
        return fmt_vehicle(value, style)
    if key == "phone_numbers":
        return fmt_phone(value, style)
    if key == "fir_number":
        return fmt_fir(value, style)
    if ftype == "name":
        return fmt_name(value, style)
    if key == "property_items":
        return str(value)
    if ftype == "text":
        return fmt_rank(value, style)
    return str(value)


# Honorifics removed before matching names; the raw text is kept in the document (D48).
HONORIFICS = {"shri", "smt", "sri", "shrimati", "kumari", "mr", "mrs", "ms", "dr"}


def match_name(name: str) -> str:
    """Name as compared: whitespace collapsed, case folded, leading honorifics removed."""
    tokens = " ".join(str(name).split()).casefold().split(" ")
    while len(tokens) > 1 and tokens[0].rstrip(".") in HONORIFICS:
        tokens = tokens[1:]
    return " ".join(tokens)


def canonical(key: str, value: Any) -> Any:
    """Comparable form of a field value, following docs/CRITICAL_FIELDS.md section 3.

    Lists keep their order here; the label code decides whether a difference is only an
    order change (Minor, D44) or a real value change.
    """
    spec = FIELD_SPECS[key]
    if spec.ftype == "section":
        return tuple(sorted(value))  # compared as a set (D44)
    if spec.ftype == "name":
        if spec.is_list:
            return tuple(match_name(v) for v in value)
        return match_name(value)
    if spec.ftype == "place":
        return " ".join(str(value).split()).casefold()
    if spec.is_list:
        return tuple(value)
    return value
