# FIR-Tamper v0 (English)

A dataset of synthetic legal documents and changed copies, with exact labels for what was changed. It is used to test whether Pramaan DMS tells a harmless copy from a real edit.

- **Everything is invented.** No real FIR, person, address, phone, vehicle or case is used. Every page footer says "Synthetic document (FIR-Tamper v0). Not a real record."
- **English only.** Hindi is planned for a later version.
- **Version 0.** This is a first slice of Phase 4 in `BUILD_PLAN.md`. It is smaller than the Phase 4 target (1,000 originals, Hindi included). See "Limitations".

Built on 15 October 2026 with seed `20261015`.

## At a glance

| Item | Count |
|---|---|
| Base documents | 60 (24 FIR, 21 charge sheet, 15 witness statement) |
| Versions per base document | 15 (1 unchanged copy, 4 format-only, 10 content changes) |
| Versions in total | 900 |
| Capture types per version | 3 (digital, scan_sim, photo_sim) |
| Samples (rows in `labels.csv`) | 2,700 |
| Untouched or format-only samples | 900 (33.3%) |
| Tamper and format classes | 40 (all present in train, val and test) |
| Size on disk | about 1.6 GB (captures 1.56 GB) |

Expected verdicts over all samples: Altered 1,680, Equivalent 840, Identical 60, Inconclusive 120.

## Folder layout

```
dataset/
  README.md            this file
  labels.csv           one row per sample (2,700 rows)
  labels.json          full detail per version: every change with page and box, the changed values, file paths
  manifest.json        SHA-256 of every generated file, split hashes, dataset hash
  templates/
    SOURCES.md         where each official form came from, and what could not be obtained
    official/          the official form we used as a model (Meghalaya Police FIR format, 2024)
  base_docs/
    FIR-0001.pdf       the original (sealed) document
    FIR-0001.json      its fields, narrative, style and the box of every field on the page
  tampered/
    FIR-0001/
      FIR-0001-V00_NONE.pdf            byte-identical copy of the original
      FIR-0001-V01_F_FONT.pdf          format-only versions (V01 to V04)
      FIR-0001-V05_T_DATE.pdf          content-changed versions (V05 to V14)
  captures/
    scan_sim/FIR-0001/FIR-0001-V05.pdf        simulated flatbed scan of that version
    photo_sim/FIR-0001/FIR-0001-V05_p1.jpg    simulated phone photo, one JPEG per page
  splits/
    train.txt, val.txt, test.txt               base document IDs in each split
    train_samples.txt, ...                     sample IDs in each split
  qa/
    report.md          automated quality checks (all passed)
    recheck_10pct.csv  270 random samples for a second person to check by hand
```

Note: the `tampered/` folder holds every version of a base document, including the unchanged copy (`V00_NONE`) and the format-only versions. Their labels say they are not tampered.

The large generated folders (`base_docs/`, `tampered/`, `captures/`) are not kept in git. Rebuild them from the seed (see "How to rebuild").

## Document types and fields

There are three document types (`SCOPE.md`). Each document carries the fields its type uses, as listed in the "Found in" column of `docs/CRITICAL_FIELDS.md`. All 27 rows of that table are covered across the dataset. Row 24 is split into `charge_sheet_number` and `charge_sheet_date`, and row 27 (narrative) is the narrative text.

| Type | ID prefix | Fields on the document |
|---|---|---|
| FIR | `FIR-` | FIR number, police station, district, date and time of report, date and time of incident, place, complainant name, father's or husband's name, address, phone, accused names with father's names and ages, victims, law sections, property value, vehicle numbers, officer name, rank and ID, narrative |
| Witness statement | `STM-` | FIR number, police station, district, date of statement, witness name, phone, accused named, date and time of incident, place, vehicle numbers, officer name, rank and ID, narrative |
| Charge sheet | `CS-` | district, police station, FIR number, FIR date, charge sheet number and date, court, law sections, date of incident, place, complainant, accused with father's names and ages, victims, property value, vehicle numbers, list of witnesses, officer name, rank and ID, brief facts (narrative) |

The FIR layout follows the order of fields in the FIR format of Meghalaya Police Circular No. 03/2024, Annexure-1. Our pages are our own drawings, not copies of any form. No official charge sheet or statement form could be downloaded (see `templates/SOURCES.md`).

Variety in the base documents:

- 31 long narratives (16 to 21 sentences) and 29 short ones (5 to 7 sentences)
- 121 of 475 printed names carry "Shri" or "Smt"
- 20 documents cite one law section, 16 cite two, 9 cite three (FIR and charge sheet)
- 1, 2 or 3 accused (30, 20 and 10 documents), in varied order
- 4 case types: house theft, vehicle theft, assault, cheating
- 3 fonts, several date, time, amount, vehicle, phone, FIR-number and section formats, and some documents with names in capitals
- incident dates from 9 July 2024 to 9 June 2026; amounts from Rs 11,000 to Rs 8,00,000; ages 19 to 60

## Label columns (`labels.csv`)

The first nine columns are the ones the task asked for. The rest add detail.

| Column | Meaning | Values |
|---|---|---|
| `sample_id` | Version ID plus capture type | for example `FIR-0007-V05-photo_sim` |
| `doc_type` | Document type | `FIR`, `STATEMENT`, `CHARGESHEET` |
| `original_id` | The base document it came from | for example `FIR-0007` |
| `tamper_class` | What was done (see class table) | for example `T_DATE`, `F_FONT`, `NONE` |
| `field_changed` | What changed, separated by `;` | field keys from `CRITICAL_FIELDS.md` (for example `date_of_incident`), `narrative`, `stamp:ps`, `stamp:court`, `sig:officer`, `annotation`, `page_added`, `page_removed`, `page_reordered`, and `blurred:<field>` for an unreadable field. Empty when nothing changed |
| `page_affected` | Page numbers, separated by `;` | Page numbers of the original document. For an added page, the page number in the changed copy |
| `severity` | Severity of an Altered verdict | `Critical`, `Minor`, or `None` (for Identical, Equivalent, Inconclusive) |
| `expected_verdict` | The correct verdict | `Identical`, `Equivalent`, `Altered`, `Inconclusive` |
| `capture_type` | How the sample was captured | `digital`, `scan_sim`, `photo_sim` |
| `task_verdict` | The same verdict in three words | `Valid` (Identical or Equivalent), `Tampered` (Altered), `Inconclusive` |
| `content_changed` | Whether the content truly differs from the original | `yes`, `no`. Useful for blur samples, where the verdict is Inconclusive even though a field was edited |
| `edge_case` | Open questions from the Phase 1 docs that this label depends on | for example `E1`, `E5;Q4`. Empty if none |
| `version_id` | The version (shared by its three capture types) | for example `FIR-0007-V05` |
| `split` | Data split | `train`, `val`, `test` |
| `files` | Path(s) of the sample, relative to `dataset/`, separated by `;` | one PDF, or one JPEG per page for photos |

Notes on the labels:

- **Verdicts follow `docs/TAMPERING_DEFINITION.md`** (decision rules R1 to R7). Severity names are Critical and Minor. The task's "Major" and "Format" are not used: Critical replaces Major, and format-only samples have the verdict Equivalent with severity `None` and a `tamper_class` starting with `F_`.
- **Identical** applies only to the digital capture of the unchanged copy (`NONE`), which is byte-identical to the original. A scan or photo of the same copy is Equivalent.
- **Inconclusive** means one critical field was blurred until unreadable (rule R3). By the current spec, R3 is checked before changes, so a blurred field plus a clear edit elsewhere is also Inconclusive. That is open question E1, tagged in `edge_case`.

### More detail in `labels.json`

For each version, `labels.json` has:

- every change, with its kind, the field, the old and new value, whether it is critical, and its boxes `[page, x0, y0, x1, y1]`
- the full field values and style of the changed copy, and its narrative text
- the blurred fields and their boxes
- the page order of the changed copy (`o1`, `o2` are original pages, `x` is an added page)
- for photos, one 3x3 matrix per page

Box coordinates are in PDF points (1/72 inch), with the origin at the top-left of an A4 page (595 x 842 points). To find a box on a scan, multiply by 200/72 (scans are 200 dpi). To find a box on a photo, multiply by 200/72 and then apply that page's matrix (a perspective transform from page pixels to photo pixels).

## Classes

Each class comes from a worked example in `docs/TAMPERING_DEFINITION.md` (section 5). The QA report (`qa/report.md`) lists the count of each class in each split.

| Class | What was done | Expected label |
|---|---|---|
| `NONE` | Unchanged copy | Identical (digital), Equivalent (scan, photo) |
| `F_FONT` | Reprinted in another font | Equivalent |
| `F_REFLOW` | Font size and margins changed, so text reflows | Equivalent (E3) |
| `F_SPACING` | Line and word spacing changed only | Equivalent (E3) |
| `F_DATETIME_FORMAT` | Same dates and times in another format (for example `12/03/2026` and `12 March 2026`) | Equivalent |
| `F_NUMBER_FORMAT` | Same amount, vehicle, phone and FIR number written another way (for example `Rs 5,00,000/-` and `Rs. 500000`) | Equivalent |
| `F_SECTION_FORMAT` | Same law sections written another way and listed in another order | Equivalent (Q3) |
| `F_NAME_CASE` | Names in the field rows in capitals, or not | Equivalent |
| `F_METADATA` | PDF metadata changed only | Equivalent (E11) |
| `T_DATE` | A date field changed by one day | Altered, Critical |
| `T_TIME` | A time field changed | Altered, Critical |
| `T_AMOUNT` | Property value changed by one digit | Altered, Critical |
| `T_AGE` | Age of an accused changed by one digit | Altered, Critical |
| `T_NAME` | A person's first name changed | Altered, Critical |
| `T_NAME_ADDED` | An extra accused added | Altered, Critical |
| `T_SECTION` | One law section replaced by another | Altered, Critical |
| `T_VEHICLE` | One character of a vehicle number changed | Altered, Critical |
| `T_ID` | One digit of an FIR, charge sheet, officer ID or phone number changed | Altered, Critical |
| `T_PLACE` | Police station, place of incident or court changed | Altered, Critical |
| `T_RANK` | Officer rank changed | Altered, Critical |
| `T_ADDRESS` | Complainant address changed (a non-critical field) | Altered, Minor (Q5) |
| `N_WORD_SWAP` | One word swapped in the narrative (for example "red" to "blue") | Altered, Minor |
| `N_NEGATION` | Negation added ("did" to "did not") | Altered, Minor (E5) |
| `N_SENTENCE_ADD` | A sentence added | Altered, Minor |
| `N_SENTENCE_REMOVE` | A sentence removed | Altered, Minor |
| `N_REWORD` | A sentence reworded with the same meaning | Altered, Minor |
| `N_PUNCT` | One comma removed | Altered, Minor (E4) |
| `N_ENTITY` | A date, time, name, amount or vehicle changed inside the narrative only | Altered, Minor (E5, Q4) |
| `V_STAMP_REMOVED` | Police station seal removed | Altered, Critical |
| `V_STAMP_SWAPPED` | Seal of another police station | Altered, Critical |
| `V_SIGNATURE_SWAPPED` | A signature replaced by a different one | Altered, Critical |
| `P_PAGE_ADDED` | A page of extra narrative inserted | Altered, Minor (E6) |
| `P_PAGE_REMOVED` | A page removed | Altered, Critical if the page held a critical field, seal or signature, else Minor (E6) |
| `P_PAGE_REORDER` | Two pages swapped | Altered, Minor (E7) |
| `A_MARGIN_NOTE` | A handwritten-style note added in the margin | Altered, Minor (E8) |
| `A_COURT_STAMP` | A court receipt stamp added | Altered, Critical, because it adds a stamp region (E8) |
| `R_REDACTED` | A victim or witness name blacked out | Altered, Critical (E15, expected to fail in v1) |
| `B_BLUR_ONLY` | One critical field blurred until unreadable, nothing edited | Inconclusive |
| `B_BLUR_PLUS_EDIT` | One critical field blurred while another field has a clear edit | Inconclusive (E1) |

The E and Q codes point to open questions in `docs/TAMPERING_DEFINITION.md` section 6 and `docs/CRITICAL_FIELDS.md` section 4. If the team decides one of them differently, change the rule in `ml/data/generator/labels.py` and rebuild. Only the tagged samples change.

## How samples were generated

1. **Base documents.** For each document, the generator invents a case: names from fixed lists of common given names and surnames, an invented district and police station, dates after 1 July 2024, BNS sections, amounts, vehicles and phones. The narrative is built from sentence templates (about 70 templates in `narrative.py`), with long and short versions. Everything is stored as canonical values (ISO dates, integers, rank codes), separate from how it is printed.
2. **Drawing.** ReportLab draws each page and records a box for every field value, sentence, seal and signature. Seals and signatures are drawn shapes, not images of real ones.
3. **Versions.** Each base document gets the unchanged copy, 4 format classes and 10 content classes. Classes are spread evenly within each split.
4. **Labels.** A label is computed by comparing the canonical values of the original and the changed copy, using the comparison rules in `CRITICAL_FIELDS.md` (for example, law sections compare as a set, accused names compare in order). Each class also declares its expected verdict, and the build stops if the two do not agree.
5. **Captures.** Each version is rendered at 200 dpi:
   - **scan_sim:** grey, slightly rotated, a little blur, noise, contrast change and dust specks. Saved as an image PDF.
   - **photo_sim:** the page on a desk background, with perspective, a small rotation, uneven light, blur, noise and a colour cast. Saved as one JPEG per page.

   Blur samples are blurred before capture. Their digital file is an image PDF.
6. **Split.** By base document, stratified by type: 42 train, 9 validation, 9 test documents. All versions and captures of one document stay in one split.

All randomness is seeded. Building twice with the same seed gives byte-identical files. This was checked by building twice and comparing the dataset hash, and it is also a unit test.

## Quality checks

Run `.venv/Scripts/python -m ml.data.generator.check --data dataset`. Result on this build: **all automated checks passed** (`qa/report.md`):

- Labels agree with class declarations: 0 mismatches out of 900 versions
- Text-layer check: the text of all 860 vector digital PDFs was read back. Every value the label says is present is printed, and changed or redacted old values are gone. 0 failures. (The 40 blurred versions are image-only and are not text-checked.)
- No real personal data:
  - no 10-digit number starting with 6 to 9
  - every vehicle number uses "ZZ"
  - no e-mail addresses or URLs
  - every name token comes from the invented lists

  0 problems
- No base document is in more than one split
- Every class is present in train, validation and test

**Not done yet:** the 10% human re-check. `qa/recheck_10pct.csv` lists 270 random samples. A second person must open each file, compare it with its base document in `base_docs/`, and fill in the reviewer columns.

## How to rebuild

From the repository root, with the Python environment from `ml/requirements-data.txt`:

```
python -m venv .venv
.venv/Scripts/python -m pip install -r ml/requirements-data.txt
.venv/Scripts/python -m ml.data.generator.build --out dataset
.venv/Scripts/python -m ml.data.generator.check --data dataset
.venv/Scripts/python -m pytest tests/ml
```

The full build with captures took about 20 minutes on our laptop with 7 worker processes. Add `--no-captures` for the digital files only (seconds).

Hashes for this build (seed 20261015), from `manifest.json`:

| Split | SHA-256 |
|---|---|
| train | `d2b04b520190d5988bcf5a13ce9f40a7955cf5a2bfcf40800016912c9baa04ee` |
| val | `d651b1723b63f743603b3aec8b40fb0ece250e79407c2ca163f5d77b99c75d30` |
| test | `6a5647a96b009c8eb8ffac5053e0faef5bd34f3c53f585ba22acabb78de99695` |
| whole dataset | `fc5b29558214876d4990bb576dc5e83e709e98097bf6348028fc89b0d489819d` |

A split hash covers the base documents of that split and every sample file in it. Hashes depend on library versions, so rebuild with the pinned versions.

## Limitations

- **Captures are simulated.** `scan_sim` and `photo_sim` are image processing, not real prints or photos. Real captures are Phase 10 and must be used for testing only.
- **All base documents are 2 pages.** Page 1 holds the header fields; page 2 holds the narrative, officer details, seal and signatures. So `P_PAGE_REMOVED` is always Critical here, and the Minor case (a narrative-only page removed) is not covered. `P_PAGE_REORDER` always swaps pages 1 and 2.
- **Small and template-based.** 60 base documents and about 70 sentence templates. A model can learn the templates. Results on this set will be optimistic compared with real documents.
- **Expected labels assume readable captures.** Captures are kept mild so a person can read them. Whether a real OCR engine reads every field above the confidence threshold is for Phase 6 and 8 to measure. If it cannot, the system's output may be Inconclusive where the label says Equivalent or Altered.
- **Blur strength.** Blur is strong enough to make the field unreadable to a person. That is why its label is Inconclusive.
- **Law sections.** BNS section numbers are example values. Their mapping to offences was not checked against the BNS text (TODO: verify, D38).
- **Not covered in v0:**
  - Hindi
  - Devanagari digits
  - homoglyphs
  - zero-width characters
  - pen edits on paper
  - partially captured pages (E2)
  - transliterated names
  - QR copied onto another document
  - accused statements (only witness statements)
  - court orders (out of scope)
- **Templates.** No official charge sheet or statement form could be downloaded. Those layouts are our own (see `templates/SOURCES.md`).
