# Improving FIR-Tamper for the Legal Hash

For: the project owner and the dataset owner. Based on the audit in `REPORT.md` (18 October 2026) and on what the Legal Hash needs (`LEGAL_HASH_SPEC.md` sections 5 to 12, `BUILD_PLAN.md` Phases 4, 10 to 15). Every number here comes from the audit scripts in this folder. Size targets in section 5 are proposals, with the arithmetic shown.

## 1. The short answer

dataset_v2 has a sound folder layout and clean bookkeeping, but its content cannot train or test the Legal Hash. The fastest way to a usable dataset is **not** to patch the v2 script. It is to build **v3 from the project generator** (`ml/data/generator`), keep the E0 to E15 names as the reporting taxonomy, and add the four classes the project generator lacks. Then fix one leak that both generators share: train and test use the same sentence templates.

What v2 is still good for: a plumbing test set for Phases 5 to 9 (upload, OCR, field extraction, verify UI). It must not be used to train N, to set thresholds or to report any metric.

## 2. Why build on the project generator

Measured with the same scripts on both datasets (`outputs/compare_v0_v2_narratives.json`, `outputs/step*_*.json`):

| Property | dataset_v2 (teammate script) | dataset/ v0 (`ml/data/generator`) |
|---|---|---|
| Distinct narratives | 5 of 50 (after masking IDs) | 60 of 60 |
| Narrative length, mean | 46 words | 155 words |
| Cross-split narrative similarity, mean | 0.955 | 0.441 |
| Cross-split pairs above 0.9 | 592 of 592 | 0 of 837 |
| Distinct sentences (entities masked) | 4 | 299 |
| Layout | one 27-row table for all types | per type (FIR follows a published FIR annexure field order, see `dataset/templates/SOURCES.md`) |
| Names | 15 invented non-Indian names | Indian first names x surnames, random |
| Law sections | invented acts | BNS sections (example values, D38) |
| Label printed on page | yes (sample ID and class) | no |
| Classes | 16 (4 fail their definition) | 46, tied to the locked rules D40 to D48 |
| Format-only Equivalent variants | none | 9 (font, reflow, spacing, date format, number format, section format, name case, metadata, honorific) |
| Minor-severity edits | none | word swap, reword, punctuation, sentence add/remove without entity, name order, address |
| Stamps, signatures, pages | text box only, 1 page | stamp removed/swapped, signature swapped, page add/remove/reorder |
| Inconclusive cases | none | blur only (Inconclusive), blur plus edit (Tampered) |
| Field and sentence boxes | none | recorded per field, sentence, stamp and signature (`render.py`) |
| Reproducible | seed only | byte-identical rebuild tested |
| Tests | none | label validator plus generator tests in `tests/ml/` |

The v0 dataset on disk predates the locked rules and must be rebuilt (PROGRESS.md: 1,860 old-label errors). The generator itself was already updated to the locked rules (D77, D78).

## 3. What each part of the Legal Hash needs from the data

| Component | Needs | v2 today | Action |
|---|---|---|---|
| **N** narrative hash (triplet loss) | Many different narratives; anchor = clean chunk; positive = same chunk after real OCR noise; hard negatives = word swap, negation, reword, sentence add/remove; templates not shared between train and test | 5 narratives; captures nearly noise-free; no word swap or reword | Unique narratives, held-out template families, harder captures, all narrative edit types (sections 4.1, 4.2, 4.5) |
| **F** field fingerprint and normalization | Every field type, equivalence traps that must never fire, one-character edits | No traps; one fixed value per class | Format variants and value pools (4.3, 4.4) |
| Field extraction (Phases 7, 13) | Realistic labelled forms and a box per field | Table with snake_case labels, no boxes | Per-type layouts with boxes (4.6) |
| **V** stamp and signature | Real seal and signature regions, removed or swapped | One text box that says "E15 TEST" | Visual E15 (4.4) |
| Verdict logic and thresholds | A validation split large enough to choose t_N, t_V, c_min; Identical, Equivalent, Tampered, Inconclusive all present | 4 validation bases; no Identical or Inconclusive | Split and size (5) |
| Evaluation (spec section 12) | Recall per class and per capture condition, false alarm rate on Equivalent, localization | 36 test samples per class; about 60 Equivalent test samples | Size (5) |

Why the size matters (95% confidence, recall around 0.9):

| Test samples per class | Margin on recall |
|---|---|
| 36 (v2 today) | about plus or minus 10 points |
| 90 | about plus or minus 6 points |
| 150 | about plus or minus 5 points |

For the false alarm rate on Equivalent copies: with zero false alarms in n samples, the 95% upper bound is about 3/n. With the roughly 60 Equivalent test samples in v2, the best claim possible is "false alarm rate below 5%". With 1,000 it is "below 0.3%". Samples from the same base document are correlated, so the number of test **base documents** matters too. Aim for at least 30.

## 4. The improvements, in order

### 4.1 Remove every label leak (Blocker, do first)

- Print nothing on the page that names the sample, the class or the version. The original, the E0 copies and every variant print the same header.
- Keep IDs out of the PDF metadata Title and file creation dates. They can carry the class too.
- Use neutral file names in the training loader. The paths `tampered/E6/...` give the class away. The loader should read pairs from `labels.csv`, never from folder names.
- Check: rerun `step5_tamper.py` and `step6_ocr.py`. Target: 0 pairs with a header difference, 0% "label readable in image".

### 4.2 Make narratives diverse and keep templates apart (Blocker)

- One narrative per base, 100 to 250 words, 6 to 12 sentences, with narrative entities inside (dates, times, names, amounts, vehicle numbers), as D45 needs.
- Add scenarios. v0 has 4 (house theft, vehicle theft, cheating, assault). Aim for 10 or more (for example chain snatching, cyber fraud, criminal trespass, missing person, dowry harassment complaint, road accident, mobile phone theft). Give each scenario several sentence templates with two phrasings each, as `narrative.py` already does.
- **Shared-template leak.** Even in v0, about 70% of a test document's sentences (entities masked) also appear in training documents (69 of 96 distinct test sentences). A narrative hash can memorise templates. Fix it with template families:
  - give every template a `template_family` ID;
  - assign families to splits so test uses families never seen in training;
  - keep a second, "seen-template" test set to show the gap. This gap is a useful result for the paper (generalisation to unseen wording).
- Check: cross-split narrative similarity above 0.9 = 0 pairs (`step4_splits.py`). Share of test sentences whose template text appears in train: below 20% for the unseen-template test set.

### 4.3 Draw replacement values from pools (Blocker)

- Names: a random name from the pool that differs from every party in the document; sometimes a one-letter change (Suresh to Mahesh), sometimes a full change.
- Dates: plus or minus 1 to 30 days, sometimes day and month swapped (12/03 to 03/12).
- Times: hour change and AM/PM flip.
- Amounts: one-digit edit, extra zero, lakh vs thousand.
- IDs and vehicle numbers: one character changed.
- Sections: replace, add or remove one section.
- Rotate the field: E1 over all name fields, E2 over all date fields, E8 over station, place and district.
- Use separate value pools for train and for validation/test.
- Check: distinct new values per class at least 80% of the class count (`step4_splits.py`, `replacement_values_per_class`).

### 4.4 Map E0 to E15 onto the generator, and add what is missing

Keep E0 to E15 as the names in the paper and the labels. Store the generator class as `subtype`, so the locked-rule cases are kept without inventing new top-level classes.

| E-class | Generator class(es) to use | Status | Notes |
|---|---|---|---|
| E0 Equivalent | NONE (byte-identical copy = Identical), F_FONT, F_REFLOW, F_SPACING, F_DATETIME_FORMAT, F_NUMBER_FORMAT, F_SECTION_FORMAT, F_NAME_CASE, F_METADATA, F_HONORIFIC | exists | `subtype` = the F_ class. Gives the equivalence traps the spec requires |
| E1 Name | T_NAME, T_NAME_ADDED | exists | |
| E2 Date | T_DATE | exists | |
| E3 Time | T_TIME | exists | |
| E4 Amount / number | T_AMOUNT, T_AGE, T_ID, T_VEHICLE, T_ID_SPACE | exists | Only on documents that have the value (avoids the v2 E4 problem) |
| E5 Legal provision | T_SECTION, T_SECTION_ADDED | exists | Section order stays E0 (F_SECTION_FORMAT) |
| E6 Negation | N_NEGATION | exists | |
| E7 Role reversal | none | **add** | Swap complainant and accused in fields and in the narrative together |
| E8 Location | T_PLACE | exists | |
| E9 Evidence | none | **add** | Needs a seizure or property-list section (exhibit ID, description, quantity) in charge sheets and FIRs |
| E10 Clause insertion | N_SENTENCE_ADD, N_SENTENCE_ADD_ENTITY | exists | Severity Minor or Major by entity (D45) |
| E11 Clause deletion | N_SENTENCE_REMOVE, N_SENTENCE_REMOVE_ENTITY | exists | Same |
| E12 Modal / quantifier | none (N_WORD_SWAP is close) | **add** | Swap one modal or quantifier in place: "may" to "shall", "some" to "all", "saw" to "think I saw" |
| E13 Custody chain | none | **add** | Needs a custody block (seized by, deposited with, malkhana entry number, date); edit one entry |
| E14 Backdating | none | **add** | Printed date moved before 1 July 2024 while the document still cites BNS (the Phase 25 anachronism rule; use the effective date as verified in `docs/REQUIREMENTS.md`). Do not rely on PDF metadata: verify reads page content, and photos have none |
| E15 Seal / signature | V_STAMP_REMOVED, V_STAMP_SWAPPED, V_SIGNATURE_SWAPPED, A_COURT_STAMP | exists | Real synthetic seal and signature images; printed text unchanged |
| Locked-rule cases outside E1 to E15 | N_WORD_SWAP, N_REWORD, N_PUNCT, T_NAME_ORDER, T_ADDRESS, T_RANK, P_PAGE_*, A_MARGIN_NOTE, A_NOTE_OVER_FIELD, B_BLUR_ONLY, B_BLUR_PLUS_EDIT, R_REDACTED | exists | Keep them as an extra group, for example E16 (wording, Minor), E17 (page change), E18 (annotation), E19 (blur and redaction). Needs a decision |

### 4.5 Make the captures realistic (Major)

v2 captures are almost as clean as the PDF: OCR field match 0.963 digital, 0.964 scan, 0.950 photo; scan rotation at most 1.1 degrees. N learns OCR robustness only if the positives carry real OCR noise.

| Level | Scan | Photo |
|---|---|---|
| mild (today) | rotation up to 1 degree, light noise | perspective about 3%, soft shadow |
| moderate | 200 to 300 dpi, JPEG 60 to 80, blur 0.5 px, rotation up to 3 degrees, slight bleed-through | tilt 10 to 20 degrees, uneven light, JPEG 70, motion blur 1 px |
| hard | 150 dpi, JPEG 40 to 60, rotation up to 5 degrees, fold line, toner streak | dim light, glare spot, fold, partial crop of a margin, 1.5 px blur |

- Add a `capture_level` column. Report results per level (spec section 12: "per capture condition").
- Make a small set where a critical field becomes unreadable and nothing else changed, labelled **Inconclusive**, and the same with a clear edit elsewhere, labelled **Tampered** (D41).
- Use pypdfium2, not PyMuPDF, to render (D61).
- Cache OCR text per capture as a derived file (with OCR engine and version), so N's positives are real OCR output.
- Real print-and-photo captures stay Phase 10 and are the final test. Report simulated and real results separately.

### 4.6 Make the documents look real (Major)

- One layout per type, in the field order of the published forms. The FIR follows the source in `dataset/templates/SOURCES.md`. For the charge sheet and statement, find blank public forms and record them in `SOURCES.md`. Never copy a filled real document.
- Statement: first person, "Statement of ... recorded under Section 180 BNSS" style heading, signature line. TODO: verify the section number before using it in a template.
- Charge sheet: accused table (name, relation, age, address), witness list, sections, property list, IO details.
- Follow D34: phones start with 10, vehicles use ZZ, invented districts and stations, dates after 1 July 2024 (except E14), footer "Synthetic document. Not a real record." on every page of every sample (the same on all samples, so it is not a shortcut).
- Use 1 to 3 pages so page classes exist.
- Record a box for every field, narrative sentence, stamp and signature (the generator already does this). These boxes are the ground truth for localization accuracy and for the Phase 13 tagger.

### 4.7 Fix the labels (Major)

One schema, accepted by both `ml/data/validate_labels.py` and this audit. Suggested columns:

| Column | Example | Why |
|---|---|---|
| `sample_id`, `version_id`, `original_id` | FIR-0007-V03-photo_sim | Pairing |
| `original_path`, `original_sha256`, `sha256` | | Identical check, dataset hashes |
| `doc_type` | FIR / STATEMENT / CHARGESHEET | |
| `tamper_class`, `subtype` | E2, T_DATE | Paper taxonomy plus locked-rule detail |
| `verdict` | Identical / Equivalent / Tampered / Inconclusive | Locked names (D49) |
| `verdict_3level` | Identical / Equivalent / Materially Altered | What the model trains on |
| `severity` | Major / Minor / None | Locked rules (D42 to D46) |
| `changes` (JSON) | field, old, new, page, bbox, sentence index, char span | Localization metric, review |
| `could_not_verify` | date_of_report | Inconclusive cases |
| `capture_type`, `capture_level` | photo_sim, hard | Per-condition results |
| `template_family`, `scenario` | HT_2, house_theft | Split checks |
| `split` | train / val / test_seen / test_unseen | |

Write CSV as plain UTF-8 without BOM. Integer page numbers.

### 4.8 Split, freeze and review (Major)

- Split by base document **and** by template family (4.2). Then freeze and record SHA-256 per split in `docs/DATASET.md` (Phase 4 exit).
- Allocation with `round()` per type, so validation is about 15%.
- Independent review: 10% of rows, stratified by class, type and capture level, by a second person, into `annotations/independent_review.csv`.

## 5. Proposed size for v3

Assumes D32 stands (FIR, statement, charge sheet; no court orders) and 4 captures per version (digital, scan moderate, photo moderate, photo hard). These are targets to agree, not results.

| Item | Proposal |
|---|---|
| Base documents | 230: 200 from seen template families (FIR 80, charge sheet 60, statement 60) + 30 from held-out families |
| Split by base | train 140, val 30, test_seen 30, test_unseen 30 |
| Versions per base | about 28: 1 Identical copy, 8 format-only (E0), 15 tamper classes E1 to E15, about 4 extra locked-rule cases |
| Samples | about 230 x 28 x 4 = 25,800 |
| Harmless share | 9 of 28 versions, about 32% (target about one-third) |
| Per class in each test set | 30 bases x 4 captures = 120 (margin about plus or minus 5.5 points at recall 0.9) |
| Equivalent samples per test set | 30 x 9 x 4 = 1,080 (zero false alarms would bound the rate below 0.3%) |
| Build time | v0 took about 20 minutes for 900 versions with 3 captures; v3 is about 6,400 versions with 4 captures, so expect a few hours. Measure on a 10-base trial first |

`BUILD_PLAN.md` Phase 4 asks for 1,000 originals and 5,000 pairs ("adjust after first run"). 230 bases with about 6,400 labelled pairs meets the pairs target but not the originals target. Agree the number and update `BUILD_PLAN.md`.

## 6. Work order

| Step | Work | Who | Done when |
|---|---|---|---|
| 1 | Decide: build v3 on `ml/data/generator`, keep E0 to E15 names, scope (court orders or not), extra classes E16 to E19 | Project owner and dataset owner | Decisions in `DECISIONS.md` |
| 2 | Add E7, E9, E12, E13, E14 to `tamper.py` with tests (one clean negative and one positive each, like the existing tests) | Dataset owner | `pytest tests/ml` passes |
| 3 | Add scenarios and template families to `narrative.py`; add custody and seizure blocks to the charge sheet layout | Dataset owner | 10+ scenarios, `template_family` on every sentence |
| 4 | Replacement value pools, split-specific | Dataset owner | Audit check 4.3 passes |
| 5 | Capture levels and Inconclusive set; pypdfium2 rendering | Dataset owner | Audit OCR shows clear drop at hard level |
| 6 | Label schema (4.7); update `validate_labels.py` and this audit to the same schema | Dataset owner with ML owner | Both validators pass |
| 7 | 10-base trial build, rerun this audit, fix, then the full build | Dataset owner | Section 7 targets met |
| 8 | Freeze splits, record hashes, 10% independent review | Dataset owner + second teammate | Review file complete, `docs/DATASET.md` updated |

## 7. Acceptance targets for the rerun audit

Run `.venv/Scripts/python run_all.py` from this folder after each build (the audit needs small updates for the new schema in step 6).

| Check | v2 today | Target |
|---|---|---|
| Pairs differing in printed header | 800 of 800 | 0 |
| Label readable in images (OCR) | 94% to 97% | 0% |
| Distinct narratives / bases | 5 / 50 | equal |
| Cross-split narrative pairs above 0.9 | 592 of 592 | 0 |
| Test-unseen sentences whose template appears in train | not measured (v0: 72%) | below 20% |
| Distinct replacement values per class | 1 to 2 of 50 | at least 80% of class count |
| Classes passing the definition check | 11 of 15 (E4 partial) | 15 of 15, every pair |
| Validation share of bases | 8% | 13% to 17% |
| Harmless share | 11.8% | 30% to 40% |
| Identical pairs | 0 | at least 1 per base |
| Minor, Inconclusive samples | 0, 0 | present in every split |
| OCR field match, hard captures | n/a (all mild) | clearly below digital, reported per level |
| Realism markers (BNS cite, PS label, complainant particulars, signature line) | 0 of 50 | every base |
| Independent review rows | 0 | 10% |

## 8. Decisions needed before the build

1. Build v3 on `ml/data/generator`, or keep patching the v2 script? Recommended: the generator (section 2).
2. Court orders: follow D32 (out of scope) or replace D32? Recommended: follow D32 for v1.
3. Keep E0 to E15 as the paper taxonomy with `subtype`, and add E16 to E19 for the locked-rule cases? Recommended: yes.
4. Size: 230 bases (section 5) or the `BUILD_PLAN.md` 1,000 originals? Recommended: 230 now, grow if training shows N needs more.
5. E14 as the BNS-before-effective-date pattern rather than file metadata? Recommended: yes.
