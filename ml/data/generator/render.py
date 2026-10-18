"""Lay out a Doc on A4 pages and write it as a PDF with ReportLab.

The layout step records a bounding box for every field value, every narrative
sentence, every stamp and every signature. Boxes are in PDF points with the
origin at the top-left of the page. These boxes give the labels their page
and location.

FIR rows follow the field order of the FIR format in Annexure-1 of Meghalaya
Police Circular No. 03/2024 (see dataset/templates/SOURCES.md). The layouts are
our own drawings, not copies of any official form.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import getAscentDescent, stringWidth
from reportlab.pdfgen import canvas

from .model import FIELD_SPECS, Doc, Sentence, Stamp, Style, fmt_sections, fmt_value
from .narrative import render_sentence

PAGE_W, PAGE_H = A4
# The same footer on every sample of every version, so it carries no label (D96).
FOOTER = "Synthetic document. Not a real record."

BOLD = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}


@dataclass(frozen=True)
class Box:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float

    def as_list(self) -> list[float]:
        return [round(self.x0, 2), round(self.y0, 2), round(self.x1, 2), round(self.y1, 2)]


@dataclass
class TextOp:
    x: float
    y: float  # baseline, PDF coordinates (origin bottom-left)
    text: str
    font: str
    size: float
    word_space: float = 0.0
    color: tuple[float, float, float] = (0, 0, 0)


@dataclass
class RectOp:
    x: float
    y: float
    w: float
    h: float
    color: tuple[float, float, float] = (0, 0, 0)


@dataclass
class StampOp:
    stamp: Stamp
    cx: float
    cy: float


@dataclass
class SigOp:
    seed: int
    x: float
    y: float
    w: float
    h: float


@dataclass
class NoteOp:
    lines: tuple[str, ...]
    x: float
    y: float
    strike: float = 0.0  # length of a pen stroke drawn through a field (note over a field)
    angle: float = 5.0


Op = TextOp | RectOp | StampOp | SigOp | NoteOp


@dataclass
class Layout:
    pages: list[list[Op]]
    boxes: dict[str, list[Box]] = field(default_factory=dict)  # box key -> boxes

    def add_box(self, key: str, box: Box) -> None:
        self.boxes.setdefault(key, []).append(box)

    def keys_on_page(self, page: int) -> set[str]:
        return {k for k, bs in self.boxes.items() if any(b.page == page for b in bs)}

    def pages_of(self, key: str) -> list[int]:
        return sorted({b.page for b in self.boxes.get(key, [])})


Run = tuple[str, str | None]  # (text, box key or None)


class Builder:
    """Places text line by line and starts new pages when needed."""

    def __init__(self, style: Style, redacted: frozenset[str] = frozenset(), page_offset: int = 0):
        self.s = style
        self.redacted = redacted
        self.page_offset = page_offset
        self.layout = Layout(pages=[[]])
        self.top = PAGE_H - style.margin
        self.bottom = style.margin + 30
        self.y = self.top
        self.line_h = style.font_size * style.leading

    @property
    def page(self) -> int:
        return len(self.layout.pages) - 1 + self.page_offset

    def new_page(self) -> None:
        self.layout.pages.append([])
        self.y = self.top

    def ensure(self, h: float) -> None:
        if self.y - h < self.bottom:
            self.new_page()

    def _ops(self) -> list[Op]:
        return self.layout.pages[-1]

    def title(self, text: str, sub: str | None = None) -> None:
        f = BOLD[self.s.font]
        size = self.s.font_size + 4
        w = stringWidth(text, f, size)
        self.y -= size
        self._ops().append(TextOp((PAGE_W - w) / 2, self.y, text, f, size))
        if sub:
            size2 = self.s.font_size - 1
            w2 = stringWidth(sub, self.s.font, size2)
            self.y -= size2 * 1.6
            self._ops().append(TextOp((PAGE_W - w2) / 2, self.y, sub, self.s.font, size2))
        self.y -= self.line_h * 1.2

    def gap(self, lines: float = 0.5) -> None:
        self.y -= self.line_h * lines

    def flow(self, runs: list[Run], x: float, width: float, font: str | None = None) -> None:
        """Lay out runs with word wrap, recording a box per key per line."""
        font = font or self.s.font
        size = self.s.font_size
        ws = self.s.word_space
        text = "".join(t for t, _ in runs)
        keys: list[str | None] = []
        for t, k in runs:
            keys.extend([k] * len(t))
        # Split into words, remembering the character index of each word.
        words: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == " ":
                i += 1
                continue
            j = i
            while j < len(text) and text[j] != " ":
                j += 1
            words.append((i, j))
            i = j
        space_w = stringWidth(" ", font, size) + ws
        line: list[tuple[int, int]] = []
        line_w = 0.0
        lines: list[list[tuple[int, int]]] = []
        for a, b in words:
            w = stringWidth(text[a:b], font, size)
            add = w if not line else space_w + w
            if line and line_w + add > width:
                lines.append(line)
                line, line_w = [(a, b)], w
            else:
                line.append((a, b))
                line_w += add
        if line:
            lines.append(line)
        asc, desc = getAscentDescent(font, size)
        for ln in lines:
            self.ensure(self.line_h)
            self.y -= self.line_h
            base = self.y
            # Characters of this line, with their keys, joined by single spaces.
            chars: list[tuple[str, str | None]] = []
            for n, (a, b) in enumerate(ln):
                if n:
                    # The joining space keeps the key of the original space, so a
                    # multi-word value stays one box per line.
                    prev_end = ln[n - 1][1]
                    chars.append((" ", keys[prev_end] if prev_end < len(keys) else None))
                chars.extend((text[c], keys[c]) for c in range(a, b))
            line_str = "".join(c for c, _ in chars)

            def x_at(idx: int) -> float:
                pre = line_str[:idx]
                return x + stringWidth(pre, font, size) + ws * pre.count(" ")

            # Spans of equal key on this line.
            spans: list[tuple[int, int, str | None]] = []
            for idx, (_, k) in enumerate(chars):
                if spans and spans[-1][2] == k:
                    spans[-1] = (spans[-1][0], idx + 1, k)
                else:
                    spans.append((idx, idx + 1, k))
            # Draw text, leaving out redacted spans (drawn as black boxes instead).
            seg_start = 0
            for a, b, k in spans:
                if k is not None and k in self.redacted:
                    if seg_start < a:
                        self._ops().append(TextOp(x_at(seg_start), base, line_str[seg_start:a], font, size, ws))
                    x0, x1 = x_at(a), x_at(b)
                    self._ops().append(RectOp(x0 - 1, base + desc - 1, x1 - x0 + 2, asc - desc + 2))
                    seg_start = b
            if seg_start < len(line_str):
                self._ops().append(TextOp(x_at(seg_start), base, line_str[seg_start:], font, size, ws))
            for a, b, k in spans:
                if k is None:
                    continue
                # Trim spaces at span edges so boxes cover visible characters only.
                while a < b and line_str[a] == " ":
                    a += 1
                while b > a and line_str[b - 1] == " ":
                    b -= 1
                if a == b:
                    continue
                self.layout.add_box(k, Box(self.page, x_at(a), PAGE_H - (base + asc),
                                           x_at(b), PAGE_H - (base + desc)))

    def row(self, label: str, runs: list[Run], label_w: float | None = None) -> None:
        # Courier is monospaced and wider, so its label column is wider too; otherwise long
        # labels such as "Date & time of occurrence:" run into the value column.
        if label_w is None:
            label_w = 232.0 if self.s.font == "Courier" else 190.0
        x_val = self.s.margin + label_w
        width = PAGE_W - self.s.margin - x_val
        self.ensure(self.line_h)
        if label:
            f = BOLD[self.s.font]
            self._ops().append(TextOp(self.s.margin, self.y - self.line_h, label, f, self.s.font_size))
        if runs:
            self.flow(runs, x_val, width)
        else:
            self.y -= self.line_h

    def paragraph(self, runs: list[Run]) -> None:
        self.flow(runs, self.s.margin, PAGE_W - 2 * self.s.margin)


# ---------------------------------------------------------------------------
# Field runs
# ---------------------------------------------------------------------------

def _v(doc: Doc, key: str, i: int | None = None) -> Run:
    spec = FIELD_SPECS[key]
    val = doc.fields[key] if i is None else doc.fields[key][i]
    box_key = key if i is None else f"{key}[{i}]"
    if spec.ftype == "section":
        return (fmt_sections(val, doc.style), box_key)
    return (fmt_value(spec.ftype, key, val, doc.style), box_key)


def _list(doc: Doc, key: str, sep: str = ", ") -> list[Run]:
    runs: list[Run] = []
    for i in range(len(doc.fields[key])):
        if i:
            runs.append((sep, None))
        runs.append(_v(doc, key, i))
    return runs


def _person_rows(b: Builder, doc: Doc, label: str) -> None:
    for i in range(len(doc.fields["accused_names"])):
        runs: list[Run] = [(f"{i + 1}. ", None), _v(doc, "accused_names", i)]
        if "accused_relative_names" in doc.fields:
            rel = doc.relations["accused"][i]
            runs += [(f", {rel} ", None), _v(doc, "accused_relative_names", i)]
        if "accused_ages" in doc.fields:
            runs += [(", Age: ", None), _v(doc, "accused_ages", i)]
        b.row(label if i == 0 else "", runs)


def _item_rows(b: Builder, doc: Doc, label: str, with_ids: bool) -> None:
    """Property items, one per row; charge sheets print the exhibit ID before each item."""
    if "property_items" not in doc.fields:
        return
    for i in range(len(doc.fields["property_items"])):
        runs: list[Run] = [(f"{i + 1}. ", None)]
        if with_ids:
            runs += [_v(doc, "exhibit_ids", i), (": ", None)]
        runs.append(_v(doc, "property_items", i))
        b.row(label if i == 0 else "", runs)


def _officer_block(b: Builder, doc: Doc, heading: str) -> None:
    b.gap(1.0)
    b.ensure(b.line_h * 4 + 150)
    b.row(heading, [])
    b.row("Name:", [_v(doc, "officer_name")])
    b.row("Rank:", [_v(doc, "officer_rank")])
    b.row("ID No.:", [_v(doc, "officer_id")])
    _signature_zone(b, doc)


def _signature_zone(b: Builder, doc: Doc) -> None:
    """Signatures and the police station seal at the end of the document."""
    s = doc.style
    zone_top = b.y - 10
    sig_h, sig_w = 46.0, 130.0
    left_label = {"complainant": "Signature / thumb impression of informant",
                  "witness": "Signature of witness"}
    for sig in doc.signatures:
        if sig.who == "officer":
            x = PAGE_W - s.margin - sig_w
            label = "Signature of officer"
        else:
            x = s.margin
            label = left_label[sig.who]
        y = zone_top - sig_h
        b._ops().append(SigOp(sig.seed, x, y, sig_w, sig_h))
        b.layout.add_box(f"sig:{sig.who}", Box(b.page, x, PAGE_H - zone_top, x + sig_w, PAGE_H - y))
        b._ops().append(TextOp(x, y - 12, label, s.font, s.font_size - 2))
    for st in doc.stamps:
        if st.kind == "ps":
            cx, cy = PAGE_W / 2, zone_top - 50
            b._ops().append(StampOp(st, cx, cy))
            b.layout.add_box("stamp:ps", Box(b.page, cx - 46, PAGE_H - (cy + 46), cx + 46, PAGE_H - (cy - 46)))
    b.y = zone_top - 120


# ---------------------------------------------------------------------------
# Document layouts
# ---------------------------------------------------------------------------

def _narrative(b: Builder, sentences: tuple[Sentence, ...], style: Style, prefix: str = "narr") -> None:
    runs: list[Run] = []
    for i, sen in enumerate(sentences):
        if i:
            runs.append((" ", None))
        runs.append((render_sentence(sen, style), f"{prefix}:{i}"))
    b.paragraph(runs)


def _layout_fir(b: Builder, doc: Doc) -> None:
    b.title("FIRST INFORMATION REPORT", "Recorded at the police station")
    b.row("1. District:", [_v(doc, "district")])
    b.row("2. Police Station:", [_v(doc, "police_station")])
    b.row("3. FIR No.:", [_v(doc, "fir_number")])
    b.row("4. Acts and Sections:", [_v(doc, "law_sections")])
    b.row("5. Date & time of occurrence:", [_v(doc, "date_of_incident"), (" at ", None), _v(doc, "time_of_incident")])
    b.row("6. Information received at PS:", [_v(doc, "date_of_report"), (" at ", None), _v(doc, "time_of_report")])
    b.row("7. Place of occurrence:", [_v(doc, "place_of_incident")])
    b.gap()
    b.row("8. Complainant / Informant", [])
    b.row("   Name:", [_v(doc, "complainant_name")])
    b.row("   Father's/Husband's name:", [(doc.relations["complainant"] + " ", None), _v(doc, "complainant_relative_name")])
    b.row("   Address:", [_v(doc, "complainant_address")])
    b.row("   Phone:", _list(doc, "phone_numbers"))
    b.gap()
    _person_rows(b, doc, "9. Known suspects / accused:")
    b.row("10. Victim(s):", _list(doc, "victim_names"))
    b.row("11. Vehicle No(s).:", _list(doc, "vehicle_numbers"))
    b.row("12. Total value of property:", [_v(doc, "property_value")])
    _item_rows(b, doc, "13. Property involved:", with_ids=False)
    b.new_page()
    b.row("14. First information contents:", [])
    b.gap(0.3)
    _narrative(b, doc.narrative, doc.style)
    b.gap()
    b.row("15. Action taken:", [("Registered the case and took up investigation.", None)])
    b.paragraph([("FIR read over to the complainant / informant and admitted to be correctly recorded.", None)])
    _officer_block(b, doc, "16. Officer in charge")


def _layout_statement(b: Builder, doc: Doc) -> None:
    b.title("STATEMENT OF WITNESS", "Recorded during investigation")
    b.row("FIR No.:", [_v(doc, "fir_number")])
    b.row("Police Station:", [_v(doc, "police_station")])
    b.row("District:", [_v(doc, "district")])
    b.row("Date of statement:", [_v(doc, "date_of_statement")])
    b.row("Name of witness:", _list(doc, "witness_names"))
    b.row("Phone:", _list(doc, "phone_numbers"))
    b.row("Accused named in FIR:", _list(doc, "accused_names"))
    b.row("Date & time of incident:", [_v(doc, "date_of_incident"), (" at ", None), _v(doc, "time_of_incident")])
    b.row("Place of incident:", [_v(doc, "place_of_incident")])
    b.row("Vehicle No(s).:", _list(doc, "vehicle_numbers"))
    b.new_page()
    b.row("Statement:", [])
    b.gap(0.3)
    _narrative(b, doc.narrative, doc.style)
    _officer_block(b, doc, "Statement recorded by")


def _layout_chargesheet(b: Builder, doc: Doc) -> None:
    b.title("FINAL REPORT (CHARGE SHEET)", "Police report on completion of investigation")
    b.row("1. District:", [_v(doc, "district")])
    b.row("2. Police Station:", [_v(doc, "police_station")])
    b.row("3. FIR No.:", [_v(doc, "fir_number")])
    b.row("4. FIR date:", [_v(doc, "date_of_report")])
    b.row("5. Charge sheet No.:", [_v(doc, "charge_sheet_number")])
    b.row("6. Charge sheet date:", [_v(doc, "charge_sheet_date")])
    b.row("7. In the court of:", [_v(doc, "court_name")])
    b.row("8. Acts and Sections:", [_v(doc, "law_sections")])
    b.row("9. Date of occurrence:", [_v(doc, "date_of_incident")])
    b.row("10. Place of occurrence:", [_v(doc, "place_of_incident")])
    b.row("11. Complainant:", [_v(doc, "complainant_name")])
    _person_rows(b, doc, "12. Accused charge-sheeted:")
    b.row("13. Victim(s):", _list(doc, "victim_names"))
    b.row("14. Value of property:", [_v(doc, "property_value")])
    b.row("15. Vehicle No(s).:", _list(doc, "vehicle_numbers"))
    _item_rows(b, doc, "16. Property seized:", with_ids=True)
    b.row("17. Date of seizure:", [_v(doc, "seizure_date")])
    for i in range(len(doc.fields["witness_names"])):
        b.row("18. List of witnesses:" if i == 0 else "", [(f"{i + 1}. ", None), _v(doc, "witness_names", i)])
    b.new_page()
    b.row("19. Brief facts of the case:", [])
    b.gap(0.3)
    _narrative(b, doc.narrative, doc.style)
    b.gap()
    b.row("20. Chain of custody of seized property:", [])
    for i in range(len(doc.fields["custody_holders"])):
        b.row("", [(f"{i + 1}. {doc.relations['custody'][i]} ", None), _v(doc, "custody_holders", i),
                   (" on ", None), _v(doc, "custody_dates", i)], label_w=24.0)
    _officer_block(b, doc, "21. Investigating officer")


LAYOUTS = {"FIR": _layout_fir, "STATEMENT": _layout_statement, "CHARGESHEET": _layout_chargesheet}


def _footers(pages: list[list[Op]], numbers: list[int], style: Style) -> None:
    for ops, n in zip(pages, numbers):
        text = f"{FOOTER}  Page {n}"
        size = style.font_size - 2.5
        w = stringWidth(text, style.font, size)
        ops.append(TextOp((PAGE_W - w) / 2, style.margin - 10, text, style.font, size))


def layout_doc(doc: Doc) -> Layout:
    """Layout of the document before any page-level edit."""
    b = Builder(doc.style, redacted=doc.redacted)
    LAYOUTS[doc.doc_type](b, doc)
    lay = b.layout
    _footers(lay.pages, list(range(1, len(lay.pages) + 1)), doc.style)
    # Annotations and extra stamps placed on fixed areas of page 1.
    for ann in doc.annotations:
        if ann.over:
            # Ink over a field (D46): a pen stroke through the value and a short word above it.
            fb = lay.boxes[ann.over][0]
            width = fb.x1 - fb.x0
            lay.pages[fb.page].append(NoteOp(ann.lines, fb.x0, PAGE_H - fb.y1 + 2, strike=width + 6, angle=3.0))
            lay.add_box("annotation", Box(fb.page, fb.x0 - 3, fb.y0 - 3, fb.x1 + 70, fb.y1 + 3))
        else:
            lay.pages[ann.page].append(NoteOp(ann.lines, PAGE_W - doc.style.margin - 170, 150))
            lay.add_box("annotation", Box(ann.page, PAGE_W - doc.style.margin - 175, PAGE_H - 175,
                                          PAGE_W - doc.style.margin, PAGE_H - 95))
    for st in doc.stamps:
        if st.kind == "court":
            cx, cy = doc.style.margin + 105, 130
            lay.pages[0].append(StampOp(st, cx, cy))
            lay.add_box("stamp:court", Box(0, cx - 100, PAGE_H - (cy + 38), cx + 100, PAGE_H - (cy - 38)))
    return lay


@dataclass
class Assembled:
    pages: list[list[Op]]
    order: list[str]  # page origin per output page: "o3" = original page 3 (1-based), "x" = added page
    layout: Layout  # layout of the original page set (before page edits)
    extra_boxes: dict[str, list[Box]]  # boxes on the added page (page = output index)


def assemble(doc: Doc) -> Assembled:
    """Apply page-level edits (remove, swap, insert) to the laid-out pages."""
    lay = layout_doc(doc)
    pages = list(lay.pages)
    order = [f"o{i + 1}" for i in range(len(pages))]
    if doc.swapped_pages is not None:
        i, j = doc.swapped_pages
        pages[i], pages[j] = pages[j], pages[i]
        order[i], order[j] = order[j], order[i]
    extra_boxes: dict[str, list[Box]] = {}
    if doc.extra_page and doc.extra_page_after is not None:
        pos = doc.extra_page_after + 1
        eb = Builder(doc.style, page_offset=pos)
        _narrative(eb, doc.extra_page, doc.style, prefix="extra")
        extra = eb.layout.pages[0]
        _footers([extra], [pos + 1], doc.style)
        pages.insert(pos, extra)
        order.insert(pos, "x")
        extra_boxes = eb.layout.boxes
    if doc.removed_page is not None:
        idx = order.index(f"o{doc.removed_page + 1}")
        del pages[idx]
        del order[idx]
    return Assembled(pages, order, lay, extra_boxes)


# ---------------------------------------------------------------------------
# PDF drawing
# ---------------------------------------------------------------------------

def _draw_stamp(c: canvas.Canvas, st: Stamp, cx: float, cy: float) -> None:
    c.saveState()
    c.translate(cx, cy)
    c.rotate(st.angle)
    c.setStrokeColorRGB(*st.color)
    c.setFillColorRGB(*st.color)
    if st.kind == "ps":
        r = 44.0
        c.setLineWidth(1.8)
        c.circle(0, 0, r)
        c.setLineWidth(0.9)
        c.circle(0, 0, r - 13)
        text = st.ring_text
        c.setFont("Helvetica-Bold", 7.0)
        step = 340.0 / max(1, len(text))
        for k, ch in enumerate(text):
            ang = math.radians(90 + 170 - k * step)
            c.saveState()
            c.translate((r - 9) * math.cos(ang), (r - 9) * math.sin(ang))
            c.rotate(math.degrees(ang) - 90)
            c.drawCentredString(0, 0, ch)
            c.restoreState()
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(0, -4, st.center_text)
    else:
        w, h = 196.0, 70.0
        c.setLineWidth(1.6)
        c.rect(-w / 2, -h / 2, w, h)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(0, h / 2 - 18, "RECEIVED")
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(0, -2, st.ring_text)
        c.setFont("Helvetica", 9)
        c.drawCentredString(0, -h / 2 + 10, st.center_text)
    c.restoreState()


def _draw_signature(c: canvas.Canvas, op: SigOp) -> None:
    rng = random.Random(op.seed)
    c.saveState()
    c.setStrokeColorRGB(0.08, 0.12, 0.45)
    c.setLineWidth(1.1)
    p = c.beginPath()
    x, y = op.x + 4, op.y + op.h * rng.uniform(0.35, 0.65)
    p.moveTo(x, y)
    n = rng.randint(5, 8)
    for k in range(n):
        nx = op.x + 4 + (op.w - 8) * (k + 1) / n
        ny = op.y + op.h * rng.uniform(0.15, 0.9)
        p.curveTo(x + rng.uniform(0, 18), op.y + op.h * rng.uniform(0, 1),
                  nx - rng.uniform(0, 18), op.y + op.h * rng.uniform(0, 1), nx, ny)
        x, y = nx, ny
    c.drawPath(p, stroke=1, fill=0)
    yy = op.y + op.h * rng.uniform(0.05, 0.2)
    c.line(op.x + op.w * rng.uniform(0.1, 0.3), yy, op.x + op.w * rng.uniform(0.7, 0.95), yy + rng.uniform(-3, 3))
    c.restoreState()


def _draw_note(c: canvas.Canvas, op: NoteOp) -> None:
    c.saveState()
    c.translate(op.x, op.y)
    c.rotate(op.angle)
    c.setFillColorRGB(0.1, 0.2, 0.65)
    c.setStrokeColorRGB(0.1, 0.2, 0.65)
    if op.strike:
        # Pen stroke through the field value, then the note just above the field.
        c.setLineWidth(1.3)
        c.line(-3, 2, op.strike, 5)
        c.setFont("Times-Italic", 9)
        for k, line in enumerate(op.lines):
            c.drawString(op.strike + 4, 1 - k * 10, line)  # after the stroke, never over another row
    else:
        c.setFont("Times-Italic", 11)
        for k, line in enumerate(op.lines):
            c.drawString(0, -k * 14, line)
    c.restoreState()


def write_pdf(pages: list[list[Op]], style: Style, path: Path) -> None:
    """Write pages to a PDF. invariant=1 makes the output byte-identical across runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1, pageCompression=1)
    c.setTitle(style.pdf_title)
    c.setAuthor(style.pdf_author)
    c.setSubject(style.pdf_subject)
    c.setCreator(style.pdf_creator)
    for ops in pages:
        for op in ops:
            if isinstance(op, TextOp):
                c.setFillColorRGB(*op.color)
                t = c.beginText(op.x, op.y)
                t.setFont(op.font, op.size)
                if op.word_space:
                    t.setWordSpace(op.word_space)
                t.textOut(op.text)
                c.drawText(t)
            elif isinstance(op, RectOp):
                c.setFillColorRGB(*op.color)
                c.rect(op.x, op.y, op.w, op.h, stroke=0, fill=1)
            elif isinstance(op, StampOp):
                _draw_stamp(c, op.stamp, op.cx, op.cy)
            elif isinstance(op, SigOp):
                _draw_signature(c, op)
            elif isinstance(op, NoteOp):
                _draw_note(c, op)
        c.showPage()
    c.save()


def render(doc: Doc, path: Path) -> Assembled:
    asm = assemble(doc)
    write_pdf(asm.pages, doc.style, path)
    return asm


def box_dict(boxes: dict[str, list[Box]]) -> dict[str, Any]:
    return {k: [[b.page + 1] + b.as_list() for b in v] for k, v in boxes.items()}
