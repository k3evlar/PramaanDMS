# CRITICAL_FIELDS.md — Canonical 27-Field Schema

## 1. Purpose

This file defines the canonical structured fields required in every PramaanDMS base document. Field names are machine-readable identifiers and must be used exactly as written in generated JSON/CSV records.

All values must be synthetic and English-only. Use `null` only if a field is genuinely inapplicable to a document type and the project supervisor explicitly permits it. The current dataset requirement is that every base document contains all 27 fields; therefore, prefer a clearly marked fictional value such as `Not applicable in this synthetic record` only if the downstream schema accepts it. Do not silently omit keys.

## 2. Canonical field list

| # | Field | Group | Definition / validation guidance |
|---:|---|---|---|
| 1 | `document_type` | Document | One of `FIR`, `statement`, `charge_sheet`, `court_order`. |
| 2 | `case_number` | Document | Synthetic case identifier; use a consistent, unique-looking format. |
| 3 | `fir_number` | Document | Synthetic FIR identifier. For non-FIR documents, preserve a linked fictional FIR reference or use an explicitly approved not-applicable value. |
| 4 | `court_name` | Document | Invented court name; never use a real court name in a way that could imply a real case. |
| 5 | `police_station` | Document | Invented police-station name. |
| 6 | `jurisdiction` | Document | Fictional jurisdiction/area relevant to the document. |
| 7 | `filing_date` | Time | Date the document is recorded as filed; use a consistent date format. |
| 8 | `document_date` | Time | Date printed on or assigned to the document. |
| 9 | `incident_date` | Time | Date of the fictional incident. |
| 10 | `incident_time` | Time | Time of the fictional incident, with AM/PM or an explicitly documented 24-hour convention. |
| 11 | `incident_location` | Place | Fictional location of the incident. |
| 12 | `complainant_name` | Party | Invented complainant name. |
| 13 | `accused_name` | Party | Invented accused name. |
| 14 | `victim_name` | Party | Invented victim name. |
| 15 | `witness_name` | Party | Invented witness name. |
| 16 | `investigating_officer` | Party | Invented officer name/identifier. |
| 17 | `advocate_name` | Party | Invented advocate name; use an approved not-applicable convention if needed. |
| 18 | `act_name` | Legal | Name of the fictional or explicitly selected legal act. If using real statute names/sections for realistic examples, do not present the synthetic case as real; validate section examples and document the choice. |
| 19 | `section_number` | Legal | Section or set of sections referenced by the document. |
| 20 | `offence_description` | Legal | Neutral description of the alleged offence or legal issue. |
| 21 | `monetary_amount` | Quantity | Amount, including currency, or an approved not-applicable value if no amount is relevant. |
| 22 | `evidence_item_id` | Evidence | Synthetic exhibit/evidence identifier. |
| 23 | `evidence_description` | Evidence | Description of the fictional evidence item and relevant facts. |
| 24 | `seizure_date` | Evidence | Date of fictional seizure, using a consistent date format. |
| 25 | `custody_holder` | Evidence | Synthetic person/role or unit currently responsible for evidence custody. |
| 26 | `case_status` | Status | Controlled status value suitable to the document, such as `Under investigation`, `Filed`, `Pending`, `Disposed` (adapt as needed and document the allowed set). |
| 27 | `next_hearing_date` | Status | Date of the next fictional hearing, or an approved not-applicable convention where no hearing is scheduled. |

## 3. Required field groups

The canonical group assignments are:
- Document: fields 1–6
- Time: fields 7–10
- Place: field 11
- Party: fields 12–17
- Legal: fields 18–20
- Quantity: field 21
- Evidence: fields 22–25
- Status: fields 26–27

## 4. Representation and validation rules

1. Every base record must contain all 27 keys.
2. Use ISO `YYYY-MM-DD` for dates in structured JSON/CSV, unless the project implementation explicitly selects a different canonical format. Display formatting in PDFs may vary.
3. Store times in a consistent canonical format; if AM/PM is shown in the PDF, ensure the structured value is unambiguous.
4. Preserve the distinction between a field's structured value and its displayed text. This helps test formatting variation without changing the underlying value.
5. Use the same fictional identity consistently across linked records, except when a controlled tampering operation intentionally changes it.
6. Use stable IDs for base documents and variants; never reuse `sample_id`.
7. For each generated PDF, retain the source JSON record and a mapping from fields to page/region when possible.
8. If a field is not naturally relevant to a document type, still preserve the key and use a documented, consistent representation accepted by the pipeline. Do not invent a value that changes the document's meaning merely to fill a field.
9. Field-level labels must use these canonical names wherever applicable. For E15, use an explicit region annotation such as `signature_region` or `seal_region`; for E14, include metadata in the change log.

## 5. Synthetic-data examples

These are illustrative placeholders only:
- `case_number`: `CASE-SYN-2026-0001`
- `fir_number`: `FIR-SYN-2026-0001`
- `incident_date`: `2026-08-12`
- `incident_time`: `23:40`
- `evidence_item_id`: `EXHIBIT-SYN-A14`

Do not reuse the examples as if they were real identifiers. Generated records should vary across samples.

## 6. Alignment note

The canonical list above contains exactly 27 fields. Other details mentioned in earlier planning material (for example, age of accused, complainant address, report time, charge-sheet number/date, or a free-form narrative field) are not additional canonical fields in this version. If these are required by the supervisor, add them through a versioned schema change and update downstream generators and labels together.
