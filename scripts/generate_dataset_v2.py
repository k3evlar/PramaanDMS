from __future__ import annotations

import argparse
import csv
import json
import random
from copy import deepcopy
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)

# This V2 generator writes to dataset_v2/ so it does not overwrite the existing pilot.
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dataset_v2"
BASE_DIR = OUT_DIR / "base_docs"
TAMPER_DIR = OUT_DIR / "tampered"
ANNOTATIONS_DIR = OUT_DIR / "annotations"

FIELDS = [
    "document_type", "case_number", "fir_number", "court_name", "police_station",
    "jurisdiction", "filing_date", "document_date", "incident_date", "incident_time",
    "incident_location", "complainant_name", "accused_name", "victim_name",
    "witness_name", "investigating_officer", "advocate_name", "act_name",
    "section_number", "offence_description", "monetary_amount", "evidence_item_id",
    "evidence_description", "seizure_date", "custody_holder", "case_status",
    "next_hearing_date"
]

DOC_TYPES = ["FIR", "charge_sheet", "statement", "court_order"]
NAMES = [
    "Avery Rowan", "Morgan Ellis", "Jordan Vale", "Casey North", "Taylor Reed",
    "Riley Quinn", "Cameron Blake", "Drew Arden", "Skyler Hayes", "Parker Wren",
    "Robin Mercer", "Jamie Frost", "Emerson Lane", "Finley Hart", "Kendall Rivers"
]
PLACES = [
    "Northbridge Sample District", "Westmere Fictional Ward",
    "Lakewood Test Quarter", "Eastvale Sample Sector", "Redstone Fictional Block"
]
STATIONS = [
    "Northbridge Sample Station", "Westmere Test Station",
    "Lakewood Fictional Station"
]
COURTS = [
    "Northbridge Sample Court", "Westmere Fictional Court", "Lakewood Test Court"
]
ACTS = [
    "Synthetic Property Safety Act", "Fictional Public Order Act",
    "Sample Evidence Protection Act"
]
SECTIONS = ["Section 12", "Section 18", "Section 24", "Section 31"]
AMOUNTS = [
    "Rs 5,00,000", "Rs 75,000", "Rs 1,20,000", "Rs 50,000",
    "Not applicable in this synthetic record"
]


def make_record(i: int, rng: random.Random) -> dict:
    incident_day = 3 + (i % 20)
    month = 1 + (i % 9)
    incident = date(2026, month, incident_day).isoformat()
    doc_type = DOC_TYPES[(i - 1) % len(DOC_TYPES)]
    names = rng.sample(NAMES, 6)
    place = rng.choice(PLACES)
    evidence_id = f"EXHIBIT-SYN-{chr(65 + (i % 20))}{10 + i:02d}"
    record = {
        "document_type": doc_type,
        "case_number": f"CASE-SYN-2026-{i:04d}",
        "fir_number": f"FIR-SYN-2026-{i:04d}",
        "court_name": rng.choice(COURTS),
        "police_station": rng.choice(STATIONS),
        "jurisdiction": place,
        "filing_date": date(2026, min(month + 1, 12), min(incident_day + 1, 28)).isoformat(),
        "document_date": date(2026, month, min(incident_day + 1, 28)).isoformat(),
        "incident_date": incident,
        "incident_time": rng.choice(["09:15 AM", "11:40 PM", "02:25 PM", "07:10 AM"]),
        "incident_location": place,
        "complainant_name": names[0],
        "accused_name": names[1],
        "victim_name": names[2],
        "witness_name": names[3],
        "investigating_officer": names[4],
        "advocate_name": names[5],
        "act_name": rng.choice(ACTS),
        "section_number": rng.choice(SECTIONS),
        "offence_description": (
            f"In this fictional case, the complainant reported that an unidentified parcel "
            f"was removed from a storage room in {place}. The account is synthetic and created "
            f"only to test meaning-aware document comparison."
        ),
        "monetary_amount": rng.choice(AMOUNTS),
        "evidence_item_id": evidence_id,
        "evidence_description": (
            f"A sealed sample parcel recorded as exhibit {evidence_id}; "
            "no real evidence is represented."
        ),
        "seizure_date": incident,
        "custody_holder": f"Fictional Evidence Unit {i:02d}",
        "case_status": rng.choice(["Under investigation", "Filed", "Pending review"]),
        "next_hearing_date": date(2026, 11, min(incident_day + 1, 28)).isoformat(),
    }
    assert set(record) == set(FIELDS), "Record schema mismatch"
    return record


def render_pdf(record: dict, out_path: Path, sample_id: str, note: str,
               visual_tamper: bool = False) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle", parent=styles["Title"], alignment=TA_CENTER,
        fontSize=13, leading=15, textColor=colors.HexColor("#20334A")
    ))
    styles.add(ParagraphStyle(
        name="SmallNote", parent=styles["Normal"], fontSize=7, leading=8,
        textColor=colors.HexColor("#555555")
    ))
    story = [
        Paragraph("SYNTHETIC TEST DOCUMENT — NOT AN OFFICIAL RECORD", styles["DocTitle"]),
        Spacer(1, 2 * mm),
        Paragraph(
            f"<b>Sample ID:</b> {escape(sample_id)} &nbsp;&nbsp; "
            f"<b>Document type:</b> {escape(record['document_type'])}",
            styles["Normal"]
        ),
        Paragraph(escape(note), styles["SmallNote"]),
        Spacer(1, 2 * mm),
    ]
    rows = [["Field", "Value"]]
    for field in FIELDS:
        rows.append([
            Paragraph(f"<b>{escape(field)}</b>", styles["BodyText"]),
            Paragraph(escape(str(record[field])), styles["BodyText"])
        ])
    table = Table(rows, colWidths=[45 * mm, 121 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7F0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#152536")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB5BF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(table)
    story.append(Spacer(1, 2 * mm))

    # The seal/signature region is intentionally synthetic. E15 alters this region visually.
    seal_text = "SYNTHETIC SIGNATURE / SEAL PLACEHOLDER"
    if visual_tamper:
        seal_text = "ALTERED SYNTHETIC SEAL REGION — E15 TEST"
    seal_color = colors.HexColor("#A52A2A") if visual_tamper else colors.HexColor("#385D7A")
    seal = Table(
        [[Paragraph(f"<b>{escape(seal_text)}</b>", styles["SmallNote"])]],
        colWidths=[166 * mm], rowHeights=[9 * mm]
    )
    seal.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, seal_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), seal_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether([
        seal,
        Spacer(1, 1 * mm),
        Paragraph(
            "All names, locations, identifiers, institutions and events are invented.",
            styles["SmallNote"]
        )
    ]))
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm, title=f"Synthetic {sample_id}"
    )
    doc.build(story)


def build_variants(record: dict) -> list[dict]:
    """Each result contains explicit old/new values; one primary class per sample."""
    variants = []

    def single(cls, field, new_value, severity="Major", explanation=""):
        edited = deepcopy(record)
        old_value = edited[field]
        edited[field] = new_value
        variants.append({
            "class": cls, "record": edited, "field_changed": field,
            "fields_changed": [field], "old_values": {field: old_value},
            "new_values": {field: new_value}, "severity": severity,
            "expected_verdict": "Valid" if cls == "E0" else "Tampered",
            "operation": explanation
        })

    # E0: untouched control. Cosmetic E0 variants can be added as a separate future subtype.
    variants.append({
        "class": "E0", "record": deepcopy(record), "field_changed": "none",
        "fields_changed": [], "old_values": {}, "new_values": {},
        "severity": "None", "expected_verdict": "Valid",
        "operation": "Untouched benign control; structured content unchanged."
    })

    # E1: name substitution (accused name).
    single("E1", "accused_name", "Quinn Sampleton",
           explanation="Name substitution in accused_name.")

    # E2: incident date change.
    new_date = "2026-10-27" if record["incident_date"] != "2026-10-27" else "2026-10-26"
    single("E2", "incident_date", new_date,
           explanation="Incident date altered.")

    # E3: incident time change.
    new_time = "11:40 AM" if record["incident_time"] != "11:40 AM" else "10:40 AM"
    single("E3", "incident_time", new_time,
           explanation="Incident time altered.")

    # E4: monetary amount change.
    new_amount = "Rs 9,99,999" if record["monetary_amount"] != "Rs 9,99,999" else "Rs 8,88,888"
    single("E4", "monetary_amount", new_amount,
           explanation="Monetary amount altered.")

    # E5: legal provision change; edit both act and section as one class.
    edited = deepcopy(record)
    old = {"act_name": edited["act_name"], "section_number": edited["section_number"]}
    edited["act_name"] = "Fictional Restricted Materials Act"
    edited["section_number"] = "Section 99"
    variants.append({
        "class": "E5", "record": edited, "field_changed": "act_name;section_number",
        "fields_changed": ["act_name", "section_number"], "old_values": old,
        "new_values": {"act_name": edited["act_name"], "section_number": edited["section_number"]},
        "severity": "Major", "expected_verdict": "Tampered",
        "operation": "Legal act and section changed."
    })

    # E6: negation flip. The source narrative contains 'was removed'.
    field = "offence_description"
    old = record[field]
    new = old.replace("was removed", "was not removed", 1)
    if new == old:
        new = old + " The parcel was not removed."
    single("E6", field, new, explanation="Negation flip changes the meaning of the narrative.")

    # E7: role reversal: swap complainant and accused values.
    edited = deepcopy(record)
    old = {"complainant_name": edited["complainant_name"], "accused_name": edited["accused_name"]}
    edited["complainant_name"], edited["accused_name"] = (
        edited["accused_name"], edited["complainant_name"]
    )
    variants.append({
        "class": "E7", "record": edited, "field_changed": "complainant_name;accused_name",
        "fields_changed": ["complainant_name", "accused_name"], "old_values": old,
        "new_values": {"complainant_name": edited["complainant_name"],
                       "accused_name": edited["accused_name"]},
        "severity": "Major", "expected_verdict": "Tampered",
        "operation": "Complainant and accused roles reversed."
    })

    # E8: incident location change.
    single("E8", "incident_location", "Southport Fictional Yard",
           explanation="Incident location altered.")

    # E9: evidence identifier change.
    single("E9", "evidence_item_id", "EXHIBIT-SYN-Z999",
           explanation="Evidence item identifier altered.")

    # E10: insert a material clause.
    field = "evidence_description"
    single("E10", field, record[field] +
           " A second fictional witness stated that the parcel was missing.",
           explanation="Material clause inserted.")

    # E11: remove a clause from evidence description.
    field = "evidence_description"
    shortened = "A sealed sample parcel was recorded; no further description is provided."
    single("E11", field, shortened, explanation="Evidence-description clause deleted.")

    # E12: modal/quantifier shift.
    field = "offence_description"
    single("E12", field, record[field] +
           " The record states that the parcel must be treated as accounted for.",
           explanation="Modal wording inserted, changing the asserted obligation.")

    # E13: custody chain edit, changing custody holder.
    single("E13", "custody_holder", "Fictional Evidence Unit 99",
           explanation="Custody holder altered.")

    # E14: backdating: document and filing dates moved earlier.
    edited = deepcopy(record)
    old = {"filing_date": edited["filing_date"], "document_date": edited["document_date"]}
    edited["filing_date"] = "2025-12-01"
    edited["document_date"] = "2025-11-29"
    variants.append({
        "class": "E14", "record": edited, "field_changed": "filing_date;document_date",
        "fields_changed": ["filing_date", "document_date"], "old_values": old,
        "new_values": {"filing_date": edited["filing_date"], "document_date": edited["document_date"]},
        "severity": "Major", "expected_verdict": "Tampered",
        "operation": "Document and filing dates backdated; synthetic metadata note recorded."
    })

    # E15: visual signature/seal-region tampering; structured fields remain unchanged.
    variants.append({
        "class": "E15", "record": deepcopy(record), "field_changed": "signature_seal_region",
        "fields_changed": ["signature_seal_region"], "old_values": {"signature_seal_region": "synthetic placeholder"},
        "new_values": {"signature_seal_region": "visually altered synthetic placeholder"},
        "severity": "Major", "expected_verdict": "Tampered",
        "operation": "Synthetic signature/seal region visually altered."
    })
    return variants


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate PramaanDMS synthetic English dataset V2.")
    parser.add_argument("--bases", type=int, default=5, help="Number of base documents (pilot: 5)")
    parser.add_argument("--seed", type=int, default=20261017, help="Random seed")
    parser.add_argument("--force", action="store_true",
                        help="Allow replacing files in dataset_v2; do not use unless you intend to regenerate it.")
    args = parser.parse_args()

    if args.bases < 1 or args.bases > 100:
        raise SystemExit("--bases must be between 1 and 100")

    if OUT_DIR.exists() and any(OUT_DIR.iterdir()) and not args.force:
        raise SystemExit(
            f"{OUT_DIR} already contains files. Nothing was overwritten. "
            "Use --force only if you intentionally want to regenerate dataset_v2."
        )

    rng = random.Random(args.seed)
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    TAMPER_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    labels, changes = [], []

    for i in range(1, args.bases + 1):
        record = make_record(i, rng)
        base_id = f"BASE-{i:04d}"
        base_pdf = BASE_DIR / f"{base_id}.pdf"
        write_json(BASE_DIR / f"{base_id}.json", record)
        render_pdf(record, base_pdf, base_id, "Original synthetic base record.")
        labels.append({
            "sample_id": base_id, "doc_type": record["document_type"], "original_id": base_id,
            "tamper_class": "E0", "field_changed": "none", "page_affected": "1",
            "severity": "None", "expected_verdict": "Valid", "capture_type": "digital",
            "file_path": str(base_pdf.relative_to(ROOT)).replace("\\", "/")
        })
        changes.append({
            "sample_id": base_id, "original_id": base_id, "operation": "base_record",
            "tamper_class": "E0", "field_changed": "none", "fields_changed": "[]",
            "original_value": "", "modified_value": "", "severity": "None",
            "expected_verdict": "Valid", "review_status": "needs_review",
            "notes": "Original synthetic base record; verify rendered page count."
        })

        for item in build_variants(record):
            cls = item["class"]
            sample_id = f"{base_id}-{cls}"
            out_path = TAMPER_DIR / cls / f"{sample_id}.pdf"
            json_path = TAMPER_DIR / cls / f"{sample_id}.json"
            write_json(json_path, item["record"])
            render_pdf(
                item["record"], out_path, sample_id,
                f"Controlled synthetic variant: {cls}.",
                visual_tamper=(cls == "E15")
            )
            labels.append({
                "sample_id": sample_id, "doc_type": record["document_type"], "original_id": base_id,
                "tamper_class": cls, "field_changed": item["field_changed"],
                "page_affected": "1 (verify rendered PDF)", "severity": item["severity"],
                "expected_verdict": item["expected_verdict"], "capture_type": "digital",
                "file_path": str(out_path.relative_to(ROOT)).replace("\\", "/")
            })
            changes.append({
                "sample_id": sample_id, "original_id": base_id, "operation": item["operation"],
                "tamper_class": cls, "field_changed": item["field_changed"],
                "fields_changed": json.dumps(item["fields_changed"]),
                "original_value": json.dumps(item["old_values"], ensure_ascii=False),
                "modified_value": json.dumps(item["new_values"], ensure_ascii=False),
                "severity": item["severity"], "expected_verdict": item["expected_verdict"],
                "review_status": "needs_review",
                "notes": "Verify semantic effect, page number, and label against rendered PDF."
            })

    label_path = OUT_DIR / "labels.csv"
    with label_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sample_id", "doc_type", "original_id", "tamper_class", "field_changed",
            "page_affected", "severity", "expected_verdict", "capture_type", "file_path"
        ])
        writer.writeheader()
        writer.writerows(labels)

    change_path = ANNOTATIONS_DIR / "change_log.csv"
    with change_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sample_id", "original_id", "operation", "tamper_class", "field_changed",
            "fields_changed", "original_value", "modified_value", "severity",
            "expected_verdict", "review_status", "notes"
        ])
        writer.writeheader()
        writer.writerows(changes)

    manifest = {
        "dataset_name": "PramaanDMS synthetic English dataset V2",
        "version": "0.2-pilot",
        "seed": args.seed,
        "base_document_count": args.bases,
        "sample_count": len(labels),
        "implemented_classes": [f"E{i}" for i in range(16)],
        "capture_types": ["digital"],
        "not_yet_implemented": [
            "print-scan variants", "phone-photo variants", "train/validation/test split",
            "automatic OCR confidence checks", "independent second-review workflow"
        ],
        "review_required": True,
        "important_note": "Labels are provisional; verify every PDF, change, page number, and expected verdict before research use."
    }
    write_json(OUT_DIR / "dataset_manifest.json", manifest)
    print(f"Generated {args.bases} base records and {len(labels)} digital PDF samples.")
    print(f"Output folder: {OUT_DIR}")
    print(f"Labels: {label_path}")
    print(f"Change log: {change_path}")
    print("All labels are provisional. Review PDFs and annotations before research use.")


if __name__ == "__main__":
    main()
