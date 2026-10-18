"""Shared helpers for the FIR-Tamper dataset_v2 audit.

Read only: nothing in this package writes inside the dataset folder.
All outputs go to analysis/dataset_audit/outputs and analysis/dataset_audit/charts.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

AUDIT_DIR = Path(__file__).resolve().parent
ROOT = AUDIT_DIR.parents[1]
DATASET = ROOT / "dataset_v2"
OUT = AUDIT_DIR / "outputs"
CHARTS = AUDIT_DIR / "charts"
OUT.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)

SEED = 20261018  # audit sampling seed (not the dataset seed)

# ---------------------------------------------------------------------------
# What the dataset is SUPPOSED to look like (from schemas/*.md, README_DATASET.md,
# docs/TAMPERING_DEFINITION.md and DECISIONS.md D39 to D49).
# ---------------------------------------------------------------------------
CLASSES = [f"E{i}" for i in range(16)]
HARMLESS_CLASSES = {"E0"}  # schemas/TAMPERING_DEFINITION.md: only E0 is benign
MATERIAL_CLASSES = set(CLASSES) - HARMLESS_CLASSES

CLASS_NAMES = {
    "E0": "Benign control", "E1": "Name substitution", "E2": "Date alteration",
    "E3": "Time alteration", "E4": "Amount change", "E5": "Legal provision change",
    "E6": "Negation flip", "E7": "Role reversal", "E8": "Location change",
    "E9": "Evidence ID/description edit", "E10": "Clause insertion",
    "E11": "Clause deletion", "E12": "Modal/quantifier shift", "E13": "Custody chain edit",
    "E14": "Backdating", "E15": "Signature/seal tampering",
}

# Fields each class may touch (schemas/TAMPERING_DEFINITION.md section 2).
CLASS_ALLOWED_FIELDS = {
    "E1": {"complainant_name", "accused_name", "victim_name", "witness_name",
           "investigating_officer", "advocate_name"},
    "E2": {"filing_date", "document_date", "incident_date", "seizure_date", "next_hearing_date"},
    "E3": {"incident_time"},
    "E4": {"monetary_amount"},
    "E5": {"act_name", "section_number"},
    "E6": {"offence_description", "evidence_description"},
    "E7": {"complainant_name", "accused_name"},
    "E8": {"incident_location", "police_station", "jurisdiction"},
    "E9": {"evidence_item_id", "evidence_description"},
    "E10": {"offence_description", "evidence_description"},
    "E11": {"offence_description", "evidence_description"},
    "E12": {"offence_description"},
    "E13": {"custody_holder", "seizure_date"},
    "E14": {"filing_date", "document_date"},
    "E15": set(),  # visual region only, structured fields must not change
}

FIELDS_27 = [
    "document_type", "case_number", "fir_number", "court_name", "police_station",
    "jurisdiction", "filing_date", "document_date", "incident_date", "incident_time",
    "incident_location", "complainant_name", "accused_name", "victim_name",
    "witness_name", "investigating_officer", "advocate_name", "act_name",
    "section_number", "offence_description", "monetary_amount", "evidence_item_id",
    "evidence_description", "seizure_date", "custody_holder", "case_status",
    "next_hearing_date",
]
NARRATIVE_FIELDS = {"offence_description", "evidence_description"}

# Label schema (schemas/SCOPE.md section 8 plus the split column from section 9).
REQUIRED_COLUMNS = ["sample_id", "doc_type", "original_id", "tamper_class", "field_changed",
                    "page_affected", "severity", "expected_verdict", "capture_type",
                    "file_path", "split"]
ALLOWED = {
    "doc_type": {"FIR", "statement", "charge_sheet", "court_order"},
    "tamper_class": set(CLASSES),
    "severity": {"Minor", "Major", "Format", "None"},
    "expected_verdict": {"Tampered", "Inconclusive", "Valid"},
    "capture_type": {"digital", "scan", "photo"},  # SCOPE.md section 7 exact values
    "split": {"train", "validation", "test"},
}
# Capture spellings used on disk, mapped to the spec spelling, so the rest of the
# audit can still group them.
CAPTURE_ALIASES = {"print_scan": "scan", "phone_photo": "photo", "digital": "digital",
                   "scan": "scan", "photo": "photo"}

# The 3-level verdict the Legal Hash is trained on (user brief) and its mapping
# from the dataset's labels. Identical is SHA-256 equality with the original file.
def target_verdict(row: dict[str, str], is_byte_identical: bool) -> str:
    if row["tamper_class"] in HARMLESS_CLASSES:
        return "Identical" if is_byte_identical else "Equivalent"
    return "Materially Altered"


SPLIT_TARGET = {"train": 0.70, "validation": 0.15, "test": 0.15}
SCOPE_TYPE_TARGET = {"FIR": 20, "charge_sheet": 15, "statement": 8, "court_order": 7}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


@lru_cache(maxsize=1)
def labels() -> tuple[list[str], list[dict[str, str]]]:
    return read_csv(DATASET / "labels.csv")


def label_rows() -> list[dict[str, str]]:
    return labels()[1]


def abs_path(rel: str) -> Path:
    return ROOT / rel


def source_sample_id(sample_id: str) -> str:
    for suffix in ("-PRINT_SCAN", "-PHONE_PHOTO"):
        if sample_id.endswith(suffix):
            return sample_id[: -len(suffix)]
    return sample_id


def base_pdf(original_id: str) -> Path:
    return DATASET / "base_docs" / f"{original_id}.pdf"


def base_json(original_id: str) -> Path:
    return DATASET / "base_docs" / f"{original_id}.json"


def sidecar_json(row: dict[str, str]) -> Path:
    """JSON sidecar of the digital source of a row (captures share their source's)."""
    sid = source_sample_id(row["sample_id"])
    if sid == row["original_id"]:
        return base_json(sid)
    return DATASET / "tampered" / row["tamper_class"] / f"{sid}.json"


def source_pdf(row: dict[str, str]) -> Path:
    sid = source_sample_id(row["sample_id"])
    if sid == row["original_id"]:
        return base_pdf(sid)
    return DATASET / "tampered" / row["tamper_class"] / f"{sid}.pdf"


@lru_cache(maxsize=4096)
def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=4096)
def pdf_text(path: Path) -> str:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(path))
    try:
        return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
    finally:
        doc.close()


def pdf_meta(path: Path) -> dict[str, str]:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(path))
    try:
        return dict(doc.get_metadata_dict())
    finally:
        doc.close()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def norm_text(s: str) -> str:
    """Whitespace collapse and dash folding, used for ground truth vs OCR."""
    s = s.replace("�", "-").replace("—", "-").replace("–", "-")
    s = s.replace("\r", "\n")
    return re.sub(r"\s+", " ", s).strip()


HEADER_PATTERNS = [
    re.compile(r"Sample ID:\s*\S+"),
    re.compile(r"Controlled synthetic variant:\s*E\d+\.?"),
    re.compile(r"Original synthetic base record\.?"),
]


def strip_header(text: str) -> str:
    for p in HEADER_PATTERNS:
        text = p.sub("", text)
    return text


def write_json(name: str, obj: Any) -> Path:
    path = OUT / name
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n",
                    encoding="utf-8")
    return path


def read_out(name: str) -> Any:
    path = OUT / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0
