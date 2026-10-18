"""Compute ground-truth labels by comparing an original Doc with a variant Doc.

Rules: docs/TAMPERING_DEFINITION.md section 4 (R1 to R8) and the decisions locked before
Phase 2 (D39 to D56). In order:

1. Redacted copy: not supported in v1, no verdict ("Not supported", D47).
2. Identical: same bytes (only the unchanged copy in digital form).
3. Any clear change: Tampered. Unreadable (blurred) fields are listed as
   "could not verify" beside it, never instead of it (D41).
4. No clear change but some critical field unreadable: Inconclusive.
5. Otherwise: Equivalent (only format or capture differs).

Severity of Tampered is Major if any change is Major:
- a critical field value changed, added or removed (law sections compared as a set, D44)
- a narrative entity (date, time, name, number, amount, vehicle number) changed, added or
  removed (D45)
- a negation flip in the narrative (D42)
- a page added, removed or reordered (D43)
- a stamp, seal or signature removed, added or swapped
- an unsealed annotation over a critical field (D46)
Otherwise Minor: narrative wording or punctuation, sentences without entities, name order
(D44), the non-critical address field, or an annotation outside critical fields (flagged).
"""

from __future__ import annotations

import difflib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .model import FIELD_SPECS, Doc, canonical, fields_for
from .narrative import sentence_entities, sentence_negations
from .render import Assembled

NOT_SUPPORTED = "Not supported"
TASK_VERDICT = {"Identical": "Valid", "Equivalent": "Valid", "Tampered": "Tampered",
                "Inconclusive": "Inconclusive", NOT_SUPPORTED: NOT_SUPPORTED}


@dataclass
class Change:
    kind: str
    key: str
    major: bool
    old: Any = None
    new: Any = None
    pages: list[int] = field(default_factory=list)  # 1-based
    boxes: list[list[float]] = field(default_factory=list)  # [page, x0, y0, x1, y1]

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "key": self.key, "major": self.major,
                "old": _jsonable(self.old), "new": _jsonable(self.new),
                "pages": self.pages, "boxes": self.boxes}


def _jsonable(v: Any) -> Any:
    if isinstance(v, tuple):
        return [_jsonable(x) for x in v]
    return v


def _boxes(asm: Assembled, keys: list[str]) -> tuple[list[int], list[list[float]]]:
    out: list[list[float]] = []
    for k in keys:
        for b in asm.layout.boxes.get(k, []):
            out.append([b.page + 1] + b.as_list())
    pages = sorted({int(b[0]) for b in out})
    return pages, out


@dataclass
class LabelResult:
    changes: list[Change]
    could_not_verify: list[str]  # blurred box keys of critical fields
    verdict_digital: str  # verdict for the digital capture of this version
    verdict_capture: str  # verdict for scan and photo captures
    severity: str  # Major, Minor or None
    content_changed: bool
    flagged: bool  # an unsealed annotation outside critical fields needs a person's look

    @property
    def blurred(self) -> list[str]:  # kept for callers that use the old name
        return self.could_not_verify


def _field_changes(orig: Doc, var: Doc, orig_asm: Assembled, var_asm: Assembled) -> list[Change]:
    changes: list[Change] = []
    for key in fields_for(orig.doc_type):
        spec = FIELD_SPECS[key]
        o, v = orig.fields[key], var.fields[key]
        co, cv = canonical(key, o), canonical(key, v)
        if co == cv:
            continue
        if spec.is_list and spec.ftype != "section" and Counter(co) == Counter(cv):
            # Same values, different order: Minor (D44). Paired lists (father's names,
            # ages) move with their accused and are also order-only changes.
            pages, boxes = _boxes(orig_asm, [f"{key}[{i}]" for i in range(len(o))])
            changes.append(Change("order_changed", key, False, o, v, pages, boxes))
            continue
        if spec.is_list and spec.ftype != "section":
            n = max(len(o), len(v))
            keys = [f"{key}[{i}]" for i in range(n)
                    if i >= len(o) or i >= len(v) or canonical(key, (o[i],)) != canonical(key, (v[i],))]
        else:
            keys = [key]
        kind = "field_added" if spec.is_list and len(v) > len(o) else "field_changed"
        asm = var_asm if kind == "field_added" else orig_asm  # an added value exists only on the variant
        pages, boxes = _boxes(asm, keys)
        changes.append(Change(kind, key, spec.critical, o, v, pages, boxes))
    return changes


def _sentence_change(kind_base: str, sentence, asm: Assembled, box_key: str, old: Any, new: Any) -> Change:
    """An added or removed sentence is Major when it carries a narrative entity (D45)."""
    has_entity = bool(sentence_entities(sentence))
    pages, boxes = _boxes(asm, [box_key])
    kind = f"narrative_entity_{kind_base}" if has_entity else f"narrative_{kind_base}"
    return Change(kind, "narrative", has_entity, old, new, pages, boxes)


def _narrative_changes(orig: Doc, var: Doc, orig_asm: Assembled, var_asm: Assembled) -> list[Change]:
    changes: list[Change] = []
    a = [s.identity() for s in orig.narrative]
    b = [s.identity() for s in var.narrative]
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        pairs = list(zip(range(i1, i2), range(j1, j2))) if op == "replace" else []
        paired_i = {i for i, _ in pairs}
        paired_j = {j for _, j in pairs}
        for i, j in pairs:
            so, sv = orig.narrative[i], var.narrative[j]
            pages, boxes = _boxes(orig_asm, [f"narr:{i}"])
            if so.template_id != sv.template_id:
                # Different sentence altogether: one removed, one added.
                changes.append(_sentence_change("removed", so, orig_asm, f"narr:{i}", f"sentence {i + 1}", None))
                changes.append(_sentence_change("added", sv, var_asm, f"narr:{j}", None, f"sentence {j + 1}"))
            elif sentence_entities(so) != sentence_entities(sv):
                changes.append(Change("narrative_entity_changed", "narrative", True,
                                      dict(sentence_entities(so)), dict(sentence_entities(sv)), pages, boxes))
            elif sentence_negations(so) != sentence_negations(sv):
                changes.append(Change("negation_flipped", "narrative", True,
                                      dict(sentence_negations(so)), dict(sentence_negations(sv)), pages, boxes))
            else:
                # Same facts and polarity; wording, phrasing or punctuation changed.
                changes.append(Change("narrative_changed", "narrative", False, f"sentence {i + 1}",
                                      f"sentence {j + 1}", pages, boxes))
        for i in range(i1, i2):
            if i not in paired_i:
                changes.append(_sentence_change("removed", orig.narrative[i], orig_asm, f"narr:{i}",
                                                f"sentence {i + 1}", None))
        for j in range(j1, j2):
            if j not in paired_j:
                changes.append(_sentence_change("added", var.narrative[j], var_asm, f"narr:{j}",
                                                None, f"sentence {j + 1}"))
    return changes


def _visual_changes(orig: Doc, var: Doc, orig_asm: Assembled, var_asm: Assembled) -> list[Change]:
    changes: list[Change] = []
    o_st = {s.kind: s for s in orig.stamps}
    v_st = {s.kind: s for s in var.stamps}
    for kind in sorted(set(o_st) | set(v_st)):
        key = f"stamp:{kind}"
        if kind in o_st and kind not in v_st:
            pages, boxes = _boxes(orig_asm, [key])
            changes.append(Change("visual_removed", key, True, o_st[kind].ring_text, None, pages, boxes))
        elif kind not in o_st:
            pages, boxes = _boxes(var_asm, [key])
            changes.append(Change("visual_added", key, True, None, v_st[kind].ring_text, pages, boxes))
        elif o_st[kind] != v_st[kind]:
            pages, boxes = _boxes(orig_asm, [key])
            changes.append(Change("visual_changed", key, True, o_st[kind].ring_text, v_st[kind].ring_text, pages, boxes))
    o_sig = {s.who: s for s in orig.signatures}
    v_sig = {s.who: s for s in var.signatures}
    for who in sorted(o_sig):
        if o_sig[who] != v_sig.get(who):
            key = f"sig:{who}"
            pages, boxes = _boxes(orig_asm, [key])
            changes.append(Change("visual_changed", key, True, o_sig[who].seed, v_sig[who].seed, pages, boxes))
    return changes


def _annotation_changes(orig: Doc, var: Doc, var_asm: Assembled) -> tuple[list[Change], bool]:
    changes: list[Change] = []
    flagged = False
    for ann in var.annotations[len(orig.annotations):]:
        pages, boxes = _boxes(var_asm, ["annotation"])
        over_critical = bool(ann.over) and FIELD_SPECS[ann.over.split("[")[0]].critical
        if over_critical:
            changes.append(Change("annotation_over_field", ann.over, True, None, " / ".join(ann.lines), pages, boxes))
        else:
            flagged = True  # Minor, but shown to a person (D46)
            changes.append(Change("annotation_added", "annotation", False, None, " / ".join(ann.lines), pages, boxes))
    return changes, flagged


def _page_changes(orig: Doc, var: Doc, orig_asm: Assembled, var_asm: Assembled) -> list[Change]:
    """Pages added, removed or reordered are Major (D43). Their contents are listed too."""
    changes: list[Change] = []
    if var.swapped_pages is not None:
        i, j = var.swapped_pages
        changes.append(Change("page_reordered", "page", True, [i + 1, j + 1], [j + 1, i + 1], [i + 1, j + 1]))
    if var.extra_page:
        pos = var_asm.order.index("x") + 1
        changes.append(Change("page_added", "page", True, None, pos, [pos]))
        for k, sen in enumerate(var.extra_page):
            boxes = [[b.page + 1] + b.as_list() for b in var_asm.extra_boxes.get(f"extra:{k}", [])]
            kind = "narrative_entity_added" if sentence_entities(sen) else "narrative_added"
            changes.append(Change(kind, "narrative", bool(sentence_entities(sen)), None,
                                  f"added page sentence {k + 1}", [pos], boxes))
    if var.removed_page is not None:
        p = var.removed_page
        changes.append(Change("page_removed", "page", True, p + 1, None, [p + 1]))
        for bk in sorted(orig_asm.layout.keys_on_page(p)):
            boxes = [[b.page + 1] + b.as_list() for b in orig_asm.layout.boxes[bk] if b.page == p]
            if bk.startswith("narr:"):
                sen = orig.narrative[int(bk.split(":")[1])]
                kind = "narrative_entity_removed" if sentence_entities(sen) else "narrative_removed"
                changes.append(Change(kind, "narrative", bool(sentence_entities(sen)), bk, None, [p + 1], boxes))
            elif bk.startswith(("stamp:", "sig:")):
                changes.append(Change("visual_removed", bk, True, bk, None, [p + 1], boxes))
            elif bk == "annotation":
                continue
            else:
                key = bk.split("[")[0]
                old = orig.fields[key] if "[" not in bk else orig.fields[key][int(bk.split("[")[1].rstrip("]"))]
                changes.append(Change("field_removed", key, FIELD_SPECS[key].critical, old, None, [p + 1], boxes))
    return changes


def diff(orig: Doc, var: Doc, orig_asm: Assembled, var_asm: Assembled, is_byte_copy: bool) -> LabelResult:
    changes = _field_changes(orig, var, orig_asm, var_asm)
    for bk in sorted(var.redacted):
        key = bk.split("[")[0]
        pages, boxes = _boxes(orig_asm, [bk])
        idx = int(bk.split("[")[1].rstrip("]"))
        changes.append(Change("field_redacted", key, FIELD_SPECS[key].critical, orig.fields[key][idx], None, pages, boxes))
    changes += _narrative_changes(orig, var, orig_asm, var_asm)
    changes += _visual_changes(orig, var, orig_asm, var_asm)
    ann_changes, flagged = _annotation_changes(orig, var, var_asm)
    changes += ann_changes
    changes += _page_changes(orig, var, orig_asm, var_asm)

    could_not_verify = sorted(k for k in var.blurred if FIELD_SPECS[k.split("[")[0]].critical)
    content_changed = bool(changes)
    if var.redacted:
        verdict, severity = NOT_SUPPORTED, "None"
    elif changes:
        verdict = "Tampered"
        severity = "Major" if any(c.major for c in changes) else "Minor"
    elif could_not_verify:
        verdict, severity = "Inconclusive", "None"
    else:
        verdict, severity = "Equivalent", "None"
    verdict_digital = "Identical" if is_byte_copy and verdict == "Equivalent" else verdict
    return LabelResult(changes, could_not_verify, verdict_digital, verdict, severity, content_changed, flagged)


def field_changed_text(res: LabelResult) -> str:
    parts: list[str] = []
    for c in res.changes:
        tag = c.kind if c.kind.startswith("page") else c.key
        if tag not in parts:
            parts.append(tag)
    return ";".join(parts)


def pages_text(res: LabelResult, blur_pages: list[int]) -> str:
    pages: set[int] = set()
    for c in res.changes:
        pages.update(c.pages)
    pages.update(blur_pages)
    return ";".join(str(p) for p in sorted(pages))
