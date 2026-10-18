from __future__ import annotations

import argparse
import csv
import json
import random
import re
from copy import deepcopy
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "base_docs"
TAMPER_DIR = ROOT / "tampered"
ANNOTATIONS_DIR = ROOT / "annotations"
SCHEMA_DIR = ROOT / "schemas"

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
PLACES = ["Northbridge Sample District", "Westmere Fictional Ward", "Lakewood Test Quarter",
          "Eastvale Sample Sector", "Redstone Fictional Block"]
STATIONS = ["Northbridge Sample Station", "Westmere Test Station", "Lakewood Fictional Station"]
COURTS = ["Northbridge Sample Court", "Westmere Fictional Court", "Lakewood Test Court"]
ACTS = ["Synthetic Property Safety Act", "Fictional Public Order Act", "Sample Evidence Protection Act"]
SECTIONS = ["Section 12", "Section 18", "Section 24", "Section 31"]
AMOUNTS = ["Rs 5,00,000", "Rs 75,000", "Rs 1,20,000", "Rs 50,000", "Not applicable in this synthetic record"]

def make_record(i: int, rng: random.Random) -> dict:
    incident_day = 3 + (i % 20)
    month = 1 + (i % 9)
    incident_date = date(2026, month, incident_day).isoformat()
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
        "incident_date": incident_date,
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
        "evidence_description": f"A sealed sample parcel recorded as exhibit {evidence_id}; no real evidence is represented.",
        "seizure_date": incident_date,
        "custody_holder": f"Fictional Evidence Unit {i:02d}",
        "case_status": rng.choice(["Under investigation", "Filed", "Pending review"]),
        "next_hearing_date": date(2026, 11, min(incident_day + 1, 28)).isoformat(),
    }
    assert set(record) == set(FIELDS), "Record schema mismatch"
    return record

def render_pdf(record: dict, out_path: Path, sample_id: str, note: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=15, leading=18, textColor=colors.HexColor("#20334A")))
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#555555")))
    story = [
        Paragraph("SYNTHETIC TEST DOCUMENT — NOT AN OFFICIAL RECORD", styles["DocTitle"]),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Sample ID:</b> {escape(sample_id)} &nbsp;&nbsp; <b>Document type:</b> {escape(record['document_type'])}", styles["Normal"]),
        Paragraph(escape(note), styles["SmallNote"]),
        Spacer(1, 4 * mm),
    ]
    rows = [["Field", "Value"]]
    for field in FIELDS:
        value = str(record[field])
        rows.append([Paragraph(f"<b>{escape(field)}</b>", styles["BodyText"]),
                     Paragraph(escape(value), styles["BodyText"])])
    table = Table(rows, colWidths=[48 * mm, 118 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7F0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#152536")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB5BF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("All names, locations, case identifiers, institutions and events in this artifact are invented.", styles["SmallNote"]))
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=16*mm, bottomMargin=16*mm, title=f"Synthetic {sample_id}")
    doc.build(story)

def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def variant_specs(record: dict) -> list[tuple[str, str, dict, str, str, str, str]]:
    # tuple: suffix, class, edited record, changed field, severity, verdict, explanation
    variants = []
    def add(suffix, cls, field, new_value, severity, verdict, explanation):
        edited = deepcopy(record)
        old = edited[field]
        edited[field] = new_value
        variants.append((suffix, cls, edited, field, severity, verdict,
                         f"{explanation}; original={old!r}; modified={new_value!r}"))
    # E0 cosmetic/unchanged control: identical structured content, separate PDF.
    variants.append(("E0", "E0", deepcopy(record), "none", "None", "Valid",
                     "Untouched benign control; structured content unchanged."))
    # Only use applicable variants when not colliding with original value.
    add("E1", "E1", "accused_name", "Quinn Sampleton", "Major", "Tampered", "Synthetic name substitution")
    old_date = record["incident_date"]
    add("E2", "E2", "incident_date", "2026-10-27" if old_date != "2026-10-27" else "2026-10-26", "Major", "Tampered", "Synthetic incident-date alteration")
    old_time = record["incident_time"]
    add("E3", "E3", "incident_time", "11:40 AM" if old_time != "11:40 AM" else "11:40 PM", "Major", "Tampered", "Synthetic incident-time alteration")
    old_amount = record["monetary_amount"]
    add("E4", "E4", "monetary_amount", "Rs 9,99,999" if old_amount != "Rs 9,99,999" else "Rs 8,88,888", "Major", "Tampered", "Synthetic amount alteration")
    # E6 negation flip in description
    old_desc = record["offence_description"]
    new_desc = old_desc.replace("was removed", "was not removed", 1) if "was removed" in old_desc else old_desc + " The parcel was not removed."
    add("E6", "E6", "offence_description", new_desc, "Major", "Tampered", "Negation/meaning change in offence description")
    add("E8", "E8", "incident_location", "Southport Fictional Yard", "Major", "Tampered", "Synthetic incident-location alteration")
    add("E9", "E9", "evidence_item_id", "EXHIBIT-SYN-Z999", "Major", "Tampered", "Synthetic evidence identifier alteration")
    add("E10", "E10", "evidence_description", record["evidence_description"] + " A second fictional witness stated that the parcel was missing.", "Major", "Tampered", "Insertion of a material synthetic clause")
    add("E11", "E11", "evidence_description", "A sealed sample parcel was recorded. Details are intentionally abbreviated in this altered sample.", "Major", "Tampered", "Deletion of a key evidence-description clause")
    old_modal = record["offence_description"]
    add("E12", "E12", "offence_description", old_modal + " The record states that the parcel shall be treated as accounted for.", "Major", "Tampered", "Insertion of a modal statement changing obligation")
    return variants

def main():
    parser = argparse.ArgumentParser(description="Generate a small synthetic PramaanDMS dataset pilot.")
    parser.add_argument("--bases", type=int, default=5, help="Number of base documents to generate (pilot: 5)")
    parser.add_argument("--seed", type=int, default=20261017, help="Random seed")
    args = parser.parse_args()
    if args.bases < 1 or args.bases > 100:
        raise SystemExit("--bases must be between 1 and 100")
    rng = random.Random(args.seed)
    BASE_DIR.mkdir(exist_ok=True)
    TAMPER_DIR.mkdir(exist_ok=True)
    ANNOTATIONS_DIR.mkdir(exist_ok=True)
    labels = []
    changes = []
    for i in range(1, args.bases + 1):
        record = make_record(i, rng)
        base_id = f"BASE-{i:04d}"
        base_json = BASE_DIR / f"{base_id}.json"
        base_pdf = BASE_DIR / f"{base_id}.pdf"
        write_json(base_json, record)
        render_pdf(record, base_pdf, base_id, "Original synthetic base record.")
        labels.append({
            "sample_id": base_id, "doc_type": record["document_type"], "original_id": base_id,
            "tamper_class": "E0", "field_changed": "none", "page_affected": "all",
            "severity": "None", "expected_verdict": "Valid", "capture_type": "digital",
            "file_path": str(base_pdf.relative_to(ROOT)).replace("\\", "/")
        })
        changes.append({"sample_id": base_id, "original_id": base_id, "operation": "base_record",
                        "tamper_class": "E0", "field_changed": "none", "original_value": "",
                        "modified_value": "", "severity": "None", "expected_verdict": "Valid",
                        "review_status": "needs_review", "notes": "Original synthetic base record."})
        for suffix, cls, edited, field, severity, verdict, explanation in variant_specs(record):
            sample_id = f"{base_id}-{suffix}"
            out_path = TAMPER_DIR / cls / f"{sample_id}.pdf"
            json_path = TAMPER_DIR / cls / f"{sample_id}.json"
            write_json(json_path, edited)
            render_pdf(edited, out_path, sample_id, f"Controlled synthetic variant: {cls}.")
            labels.append({
                "sample_id": sample_id, "doc_type": record["document_type"], "original_id": base_id,
                "tamper_class": cls, "field_changed": field, "page_affected": "see PDF; verify page",
                "severity": severity, "expected_verdict": verdict, "capture_type": "digital",
                "file_path": str(out_path.relative_to(ROOT)).replace("\\", "/")
            })
            changes.append({"sample_id": sample_id, "original_id": base_id, "operation": explanation,
                            "tamper_class": cls, "field_changed": field,
                            "original_value": explanation.split("original=", 1)[1].split("; modified=", 1)[0] if "original=" in explanation else "",
                            "modified_value": explanation.split("; modified=", 1)[1] if "; modified=" in explanation else "",
                            "severity": severity, "expected_verdict": verdict,
                            "review_status": "needs_review", "notes": "Verify label and affected page against rendered PDF."})
    label_path = ROOT / "labels.csv"
    with label_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "doc_type", "original_id", "tamper_class", "field_changed",
                                                "page_affected", "severity", "expected_verdict", "capture_type", "file_path"])
        writer.writeheader()
        writer.writerows(labels)
    change_path = ANNOTATIONS_DIR / "change_log.csv"
    with change_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "original_id", "operation", "tamper_class", "field_changed",
                                                "original_value", "modified_value", "severity", "expected_verdict",
                                                "review_status", "notes"])
        writer.writeheader()
        writer.writerows(changes)
    manifest = {"dataset_name": "PramaanDMS synthetic English pilot", "version": "0.1-pilot",
                "seed": args.seed, "base_document_count": args.bases, "sample_count": len(labels),
                "implemented_classes": ["E0", "E1", "E2", "E3", "E4", "E6", "E8", "E9", "E10", "E11", "E12"],
                "not_yet_implemented": ["E5", "E7", "E13", "E14", "E15", "scan variants", "photo variants"],
                "review_required": True}
    write_json(ROOT / "dataset_manifest.json", manifest)
    print(f"Generated {args.bases} base records and {len(labels)} labeled digital PDF samples.")
    print(f"Labels: {label_path}")
    print(f"Change log: {change_path}")
    print("IMPORTANT: all labels are provisional; review PDFs and correct labels before research use.")

if __name__ == "__main__":
    main()
