# FIR-Tamper v3: build plan

Status: approved 18 October 2026 (D92 to D95). Built in stages:

| Stage | When | Content | Status |
|---|---|---|---|
| 1 | Now | Existing generator classes, 200 base documents (80 FIR, 60 charge sheet, 60 statement), seed 20261018, digital + scan_sim + photo_sim; `labels_eclass.csv` adds E0 to E19 and `verdict_3level` (`ml/data/e_class.py`) | Done, replaced by Stage 2 |
| 2 | Before Phase 12 | WP1 leak fixes in names and footer, WP4 held-out template families and new scenarios, 30 held-out bases, missing classes E7, E9, E12, E13, E14 (WP3), evidence and custody fields, E-class plan | **Done 18 Oct 2026** (D96): 230 bases, 19,680 samples, validator PASS, QA PASS, audit 18 of 18 |
| 3 | Phase 10 | WP5 hard captures (with the Phase 10 augmentation pipeline) and real captures | Planned |

Decisions taken: this session builds v3 (D92), three document types (D93), E0 to E19 with the four evidence and custody fields deferred to Stage 2 (D94), 200 + 30 bases (D95). The sections below describe the full target; each work package names its stage in the table above.

This plan builds the dataset the Legal Hash needs (`LEGAL_HASH_SPEC.md` sections 5 to 12) and closes the Phase 4 exit criteria in `BUILD_PLAN.md`. It is based on the audit in `analysis/dataset_audit/REPORT.md` and the recommendations in `analysis/dataset_audit/IMPROVEMENT_PLAN.md`.

## 1. Goal

One reproducible, English-only, synthetic dataset that:

- trains the narrative hash N (triplet loss) without template or label leakage;
- tests F, N and V per class and per capture condition, with enough samples for useful confidence intervals;
- covers every locked rule (D40 to D48) with a tampered case and a clean negative;
- uses the E0 to E15 names for the paper, with the locked verdict names in the labels;
- passes both validators and the audit acceptance targets (section 8).

## 2. Approach

Extend the project generator (`ml/data/generator`). Do not patch the v2 script. Reasons are measured in `analysis/dataset_audit/IMPROVEMENT_PLAN.md` section 2: the generator already has 46 classes tied to the locked rules, labels computed from a model diff, boxes for every field and sentence, Indian names, BNS sections, per-type layouts, byte-identical rebuilds and 111 passing tests.

Output goes to a **new folder `dataset_v3/`**. `dataset/` (v0) and `dataset_v2/` are not touched. Generated folders are git-ignored; the generator code, tests, labels schema and manifest are committed.

## 3. What changes, by work package

### WP1. Remove every label leak

| Leak | Where | Change |
|---|---|---|
| Class code in file names (`FIR-0001-V03_T_DATE.pdf`) | `build.py` | Name files by an opaque sample ID: first 12 hex characters of SHA-256(seed, version ID). Folder per base document only |
| Version in footer ("FIR-Tamper v0") | `render.py` `FOOTER` | Same footer on every sample: "Synthetic document. Not a real record." |
| PDF title holds the doc ID | `generate.py` style | Neutral title (doc type only). F_METADATA still changes metadata as a format variant |
| Folder names in training code | loaders (Phase 12) | Pairs come from `labels.csv` only |

Test: no sample path, PDF text layer or PDF metadata contains a class code, subtype or version number.

### WP2. Taxonomy and labels

Labels keep the locked verdict names (D49) and add the paper's names.

| E-class | Name | Generator subtypes |
|---|---|---|
| E0 | Format only (Equivalent) or exact copy (Identical) | NONE, F_FONT, F_REFLOW, F_SPACING, F_DATETIME_FORMAT, F_NUMBER_FORMAT, F_SECTION_FORMAT, F_NAME_CASE, F_METADATA, F_HONORIFIC |
| E1 | Name substitution | T_NAME, T_NAME_ADDED, N_ENTITY (name) |
| E2 | Date alteration | T_DATE, N_ENTITY (date) |
| E3 | Time alteration | T_TIME, N_ENTITY (time) |
| E4 | Amount or number change | T_AMOUNT, T_AGE, T_ID, T_VEHICLE, T_ID_SPACE, N_ENTITY (amount, vehicle) |
| E5 | Legal provision change | T_SECTION, T_SECTION_ADDED |
| E6 | Negation flip | N_NEGATION |
| E7 | Role reversal | **new** E_ROLE_SWAP |
| E8 | Location change | T_PLACE |
| E9 | Evidence ID or description edit | **new** E_EXHIBIT_ID, E_EXHIBIT_DESC |
| E10 | Clause insertion | N_SENTENCE_ADD, N_SENTENCE_ADD_ENTITY |
| E11 | Clause deletion | N_SENTENCE_REMOVE, N_SENTENCE_REMOVE_ENTITY |
| E12 | Modal or quantifier shift | **new** N_MODAL |
| E13 | Custody chain edit | **new** C_CUSTODY_HOLDER, C_CUSTODY_DATE, C_CUSTODY_ENTRY_REMOVED |
| E14 | Backdating | **new** T_BACKDATE (document date moved before the BNS commencement date while BNS is cited) |
| E15 | Seal or signature tampering | V_STAMP_REMOVED, V_STAMP_SWAPPED, V_SIGNATURE_SWAPPED, A_COURT_STAMP |
| E16 | Wording change (Minor) | N_WORD_SWAP, N_REWORD, N_PUNCT, T_NAME_ORDER, T_ADDRESS, T_RANK |
| E17 | Page change | P_PAGE_ADDED, P_PAGE_REMOVED, P_PAGE_REORDER |
| E18 | Annotation | A_MARGIN_NOTE, A_NOTE_OVER_FIELD |
| E19 | Unreadable or redacted | B_BLUR_ONLY, B_BLUR_PLUS_EDIT, R_REDACTED |

E16 to E19 keep the locked-rule cases. **(decision)**

E7, E9 and E13 need new content:

- **Seizure list** (FIR property section, charge sheet): exhibit ID (`EX-<n>/<year>`), description, quantity, seizure date.
- **Custody block** (charge sheet): seized by (officer), deposited with (malkhana in-charge), register entry number, deposit date, and 1 to 3 transfer entries (for example to a forensic lab and back).
- These add four fields to `docs/CRITICAL_FIELDS.md` (rows 28 to 31: exhibit ID, exhibit description, seizure date, custody holder or entry). **(decision)**

### WP3. New classes

| Class | Edit | Severity (locked rules) | Applies to |
|---|---|---|---|
| E_ROLE_SWAP | Complainant and first accused swapped in the fields and in every narrative slot | Major (critical fields changed) | FIR, charge sheet |
| E_EXHIBIT_ID | One character of an exhibit ID changed | Major | Docs with a seizure list |
| E_EXHIBIT_DESC | One word of an exhibit description changed (colour, item, quantity word) | Major (critical field) | Same |
| N_MODAL | One modal or quantifier swapped in place, using new template slots ("saw" to "think I saw", "all" to "some", "must" to "may") | Minor (wording, no entity) | Narratives with a modal slot |
| C_CUSTODY_HOLDER | Name or rank of a custody holder changed | Major | Charge sheet |
| C_CUSTODY_DATE | One custody date shifted | Major | Charge sheet |
| C_CUSTODY_ENTRY_REMOVED | One transfer entry removed | Major | Charge sheet with 2 or more entries |
| T_BACKDATE | Document date (report, statement or charge sheet date) moved to a date before 1 July 2024; sections still BNS. Change log records the anachronism | Major | All |

Each class gets the same tests as the existing ones: a clean negative, a positive, the declared verdict equals the computed verdict on all three document types, and the text-layer check.

### WP4. Narrative diversity and held-out templates

- Add **8 scenarios** to the existing 4: chain snatching, mobile phone theft, criminal trespass, cyber fraud (UPI), road accident (rash driving), cheque cheating, house-breaking at night, intimidation over a land dispute. Each gets FIR core templates (5 to 7, two phrasings), a statement event, a charge sheet event, an amount range and example BNS sections (D38: section numbers are example values, not verified).
- Add modal or quantifier slots to about 20 templates (for N_MODAL).
- Split the generic extra-sentence pools into two disjoint halves and add sentences so each half has at least 15.
- **Template families:** each scenario and each extras half is a family. Families are assigned to splits:
  - seen families (9 scenarios, extras half A): train, val, test_seen;
  - held-out families (3 scenarios, extras half B): test_unseen only.
- Store `scenario` and the list of template IDs per base, so the audit can measure overlap.

### WP5. Capture levels

| Capture | Level | Change |
|---|---|---|
| scan_sim | moderate | existing scan |
| photo_sim | moderate | existing photo |
| photo_sim | hard | new: tilt up to 8 degrees, perspective jitter 6%, low light (0.55 to 0.75), glare spot, fold line shadow, JPEG 45 to 65, blur 1.2 to 2.0 px |

Column `capture_level`. Hard photos inherit the version label, except where the label rules make a critical field unreadable (not modelled at capture time; Inconclusive comes from E19 B_BLUR_ONLY). Real captures stay Phase 10.

### WP6. Splits

- Unit: base document. Stratified by type.
- 230 base documents **(decision)**: 200 from seen families split 140 / 30 / 30 (train / val / test_seen), plus 30 from held-out families (test_unseen).
- Frozen after build; SHA-256 per split in `manifest.json` and in the dataset card.

### WP7. Versions per base

Each base gets: NONE (exact copy), 8 of the 9 format subtypes, one subtype for each of E1 to E15 that applies, and 4 of the E16 to E19 subtypes, picked with the existing balanced `assign()` per split. About 28 versions per base, about 32% harmless.

### WP8. Label schema

`labels.csv` (plain UTF-8, no BOM), one row per sample:

`sample_id, version_id, original_id, original_path, original_sha256, sha256, doc_type, scenario, template_families, tamper_class (E0 to E19), subtype, field_changed, page_affected, severity, verdict (Identical / Equivalent / Tampered / Inconclusive / Not supported), verdict_3level (Identical / Equivalent / Materially Altered / Inconclusive / Not supported), could_not_verify, flagged, rule_ref, capture_type, capture_level, split, files`

`labels.json` keeps the full change list per version (kind, field, old, new, page, box, sentence index).

`ml/data/validate_labels.py` and `check.py` are updated to this schema and must pass. The audit scripts in `analysis/dataset_audit/` get a v3 mode.

### WP9. Build and QA

1. Unit tests for every new class and for leak removal (`pytest tests/ml`).
2. Trial build: 12 bases, no captures. Validator, `check.py` and audit.
3. Trial build with captures (12 bases). Look at sample images by eye.
4. Full build into `dataset_v3/`.
5. Rerun the audit; meet section 8.
6. Record split hashes, update docs, commit code (not data).
7. Human 10% re-check: a sample file is written; the review itself is a human task.

## 4. Size, time and disk (estimates)

| Item | Estimate |
|---|---|
| Bases | 230 |
| Versions | about 6,400 |
| Samples | digital + scan + photo + photo hard = about 25,600 |
| Disk | about 15 GB (v0: 1.5 GB for 900 versions with 2 capture types). 62 GB free |
| Build time | 3 to 5 hours on 12 cores (v0: about 20 minutes for 900 versions) |

These are estimates from v0; the trial build measures the real numbers.

## 5. Decisions

Taken on 18 October 2026: D92 (this session builds v3; the dataset teammate does the human review), D93 (three document types), D94 (E0 to E19; evidence and custody fields in Stage 2), D95 (200 bases in Stage 1, 30 held-out bases in Stage 2).

Paper taxonomy: E0 to E19 (D96).

## 6. Out of scope

Hindi (D39), real case data, real captures (Phase 10), training the model (Phase 12).

## 7. Risks

| Risk | Mitigation |
|---|---|
| New scenario templates sound alike | Two phrasings each, held-out families, audit overlap check |
| BNS section numbers wrong for an offence | Marked as example values (D38), TODO: verify before the paper |
| Build too slow or too large | Trial build first; reduce hard captures to val and test if needed |
| Label bug in a new class | Declared vs computed label check stops the build; text-layer check; tests |

## 8. Audit acceptance targets

| Check | Target |
|---|---|
| Class code, subtype or version in any path, text layer or metadata | 0 |
| Distinct narratives | equal to bases |
| Cross-split narrative pairs above 0.9 similarity | 0 |
| test_unseen sentences whose template appears in train | 0% |
| Classes failing their definition check | 0 |
| Validation share of bases | 13% to 17% |
| Harmless share | 30% to 40% |
| Identical, Equivalent, Tampered (Major and Minor), Inconclusive, Not supported | all present in every split |
| Both validators | PASS |
