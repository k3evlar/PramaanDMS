# SCOPE.md — PramaanDMS English Dataset

## 1. Purpose

Build a reproducible, English-only dataset for evaluating PramaanDMS, a meaning-aware document management system for legal and investigation documents. The dataset tests whether the system can distinguish material changes to a document's legal meaning or evidentiary content from benign formatting changes and capture noise.

The dataset is synthetic. It must not contain real FIRs, real personal data, real case details, or unredacted material copied from real cases.

## 2. In-scope document types

The dataset covers these four document types:

1. First Information Report (FIR)
2. Witness or accused statement
3. Charge sheet
4. Court order

Prioritize FIRs and charge sheets during initial development, followed by statements and court orders.

## 3. Language and data policy

- All document text and labels are in English.
- Use invented names, addresses, case numbers, institutions, places, evidence identifiers, dates, amounts, and narratives.
- Clearly mark synthetic records as fictional in dataset documentation. Do not add a prominent fictional watermark to only some samples, because it could become a shortcut feature for a model.
- Do not use real personal data or real case facts.
- Blank public forms may be used as layout references only if their source is recorded in `templates/sources.txt`. Do not treat real filled legal documents as synthetic data.

## 4. Field schema

Each base document must contain all 27 fields defined in `CRITICAL_FIELDS.md`. The field names in that file are the canonical schema for this dataset.

**Schema alignment note:** an earlier task brief mentioned additional example fields such as report time, age of accused, complainant address, and narrative. These are not among the 27 fields in the currently supplied canonical list. For this specification, the supplied 27-field list is authoritative. If the project supervisor requires those extra fields, revise `CRITICAL_FIELDS.md` and the dataset version together before data generation; do not silently add them or claim they are part of the current 27.

Some tampering operations also affect information not represented as one of the 27 structured fields:
- E14 may affect file metadata as well as date text.
- E15 affects a signature or seal region and may include a signatory identifier.
These must be recorded in the change log and field/region annotation even when they are not canonical structured fields.

## 5. Dataset size and composition

Initial target:
- 50 base documents for the first complete version.
- Expand to 100 if time and quality review permit.
- Every base document has all 27 canonical fields.
- Each base document should have multiple variants, with 5–15 variants as a planning target where feasible.
- Every class E1–E15 must be represented in the complete dataset.
- Include E0 benign controls. Approximately one-third of all samples should be untouched or benign/format-only controls, as required by the task brief.

A suggested initial allocation of 50 base documents is:
- 20 FIRs
- 15 charge sheets
- 8 statements
- 7 court orders

This allocation is a planning recommendation, not a legal or statistical requirement. Adjust it if a supervisor-approved sampling plan says otherwise.

Do not force every tampering class onto every base document. Use only plausible edits for the document and field, and ensure all classes are covered across the dataset.

## 6. Sample and variant principles

- Every sample has a unique `sample_id`.
- Every derivative references its base document through `original_id`.
- Keep the original structured record immutable.
- Define the intended edit in a change log before rendering the edited artifact.
- Each tampered sample has exactly one primary tampering class (E1–E15), plus a list of all affected fields/regions.
- If one operation accidentally introduces multiple independent tampering classes, either correct the sample or explicitly rebuild it as a separate, clearly designed sample. Do not label a multi-class edit as a single-class example.
- E0 is used for no-tamper/benign controls, not as a tampering class.
- Store clean digital PDFs, print-and-scan PDFs, and phone-photo images/PDFs where applicable.
- A capture variant inherits the underlying content label unless image quality makes the correct verdict genuinely uncertain under the evaluation protocol.

## 7. Capture types

Use these exact `capture_type` values:
- `digital`: clean digitally generated PDF
- `scan`: print-and-scan version
- `photo`: phone photograph with realistic perspective, lighting, or focus variation

Capture changes alone must not change document meaning. Record deliberate content edits separately from capture transformations.

## 8. Labels and expected verdicts

Use the exact label columns defined in the dataset task:
`sample_id`, `doc_type`, `original_id`, `tamper_class`, `field_changed`, `page_affected`, `severity`, `expected_verdict`, `capture_type`.

Allowed values:
- `tamper_class`: `E0` for benign/no-tamper controls; `E1`–`E15` for tampered samples.
- `severity`: `Minor`, `Major`, `Format`, `None`.
- `expected_verdict`: `Tampered`, `Inconclusive`, `Valid`.
- `capture_type`: `digital`, `scan`, `photo`.

Default verdict policy:
- E0 untouched or meaning-preserving controls: `Valid`.
- E1–E15 with a clearly observable material edit: `Tampered`.
- A sample whose relevant content cannot be reliably read or adjudicated due to blur, occlusion, redaction, or low image/OCR confidence: `Inconclusive` when the evaluation protocol calls for abstention.
- Do not label an E0 sample `Tampered` merely because spacing, layout, scan noise, or meaning-preserving wording differs.

Severity guidance:
- `Major`: a change that can materially affect identity, chronology, legal provision, role, location, amount, evidence, custody, or the operative meaning of a clause.
- `Minor`: a limited content change that is meaningful but has lower assessed impact under the project's review rubric.
- `Format`: a cosmetic or layout-only transformation that preserves meaning.
- `None`: no change from the reference content.

The severity assignment must be made from the change and the project's rubric, not from how visually obvious the change is. If severity is subjective for a case, document the rationale in the change log and review it.

## 9. Train, validation, and test split

Use an approximate 70% / 15% / 15% split by **base document**, not by individual sample. Every sample derived from one base document must remain in the same split. This prevents near-duplicate leakage between training and evaluation.

Create:
- `splits/train.csv`
- `splits/validation.csv`
- `splits/test.csv`

Use a fixed random seed and record it in `README.md`. Check that the splits contain useful coverage of all document types and tampering classes. With a small dataset, exact class balance may not be possible; report missing coverage honestly rather than moving derivatives across splits.

## 10. Quality assurance

Before release:
- Validate all 27 fields for every base record.
- Verify every label against the actual artifact and the planned edit.
- Check that every E-class has sufficient examples for the intended analysis.
- Confirm E0 controls are included and approximately one-third of samples are untouched or format-only.
- Have a second reviewer randomly inspect 10% of labels.
- Check that no real personal data appears anywhere.
- Confirm every sample opens and every ID/path resolves.
- Keep a record of corrections and reviewer disagreements.

## 11. Out of scope

Unless a later version explicitly adds them, this dataset does not claim to cover:
- Languages other than English
- Authentic real-world case files
- Legal advice or adjudication of whether a real person committed an offence
- Exhaustive coverage of every jurisdiction's document format
- Proof that a document is legally authentic based solely on semantic similarity
- Reliable interpretation of completely unreadable or fully redacted content

## 12. Dataset versioning

Version the schema, class definitions, generated records, and labels together. If the 27 fields or class definitions change, increment the dataset version and regenerate or revalidate affected records and labels.
