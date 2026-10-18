# FIR-Tamper v3 (Stage 2)

Synthetic, English-only dataset for training and testing the Legal Hash. All names, places, numbers and events are invented. Every page says "Synthetic document. Not a real record." Nothing here is a real case record.

Built on 18 October 2026 with the project generator (`ml/data/generator`), decisions D92 to D96. Plan: `docs/DATASET_V3_PLAN.md`. Stage 2 replaced the Stage 1 build in this folder.

## Rebuild

```powershell
.venv\Scripts\python -m ml.data.generator.build --out dataset_v3 --seed 20261018 --n-fir 80 --n-chargesheet 60 --n-statement 60 --n-fir-unseen 12 --n-chargesheet-unseen 9 --n-statement-unseen 9 --format-per-doc 8 --eclass-plan
.venv\Scripts\python -m ml.data.e_class --data dataset_v3
```

The same seed gives byte-identical files. Build time on 12 cores: 55 minutes. Size: 12 GB. Generated folders are git-ignored.

## Contents

| Item | Count |
|---|---|
| Base documents | 230: 92 FIR, 69 charge sheet, 69 witness statement |
| Versions | 6,560 (about 28.5 per base: 1 exact copy, 8 format-only, one per applicable E-class) |
| Samples | 19,680 (each version as digital PDF, simulated scan PDF, simulated phone photo JPG) |
| Narratives | 230 distinct, 154 words on average; 12 incident scenarios |
| Splits by base document | train 140, val 30, test 30 (70 / 15 / 15 of the seen bases), plus test_unseen 30 |

**test_unseen** holds 30 extra bases written only from template family B: 3 scenarios (road accident, breach of trust, land dispute intimidation) and their own generic sentences. None of their sentence templates appears in train. Use it to measure how the narrative hash handles wording it never saw. The other splits use family A (9 scenarios). Seen-family test documents do share templates with train, by design.

## Files

| Path | What it is |
|---|---|
| `labels_eclass.csv` | **Use this one.** One row per sample: all `labels.csv` columns plus `e_class`, `e_class_name`, `verdict_3level`, `original_path` |
| `labels.csv` | Generator labels (locked verdict names, D49); `tamper_class` is the generator subtype |
| `labels.json` | Full change list per version: field, old and new value, page, box, sentence |
| `base_docs/` | Originals: PDF and a JSON with fields, narrative, template IDs, family, style and boxes |
| `tampered/<base>/` | Digital versions, named by an opaque version ID |
| `captures/scan_sim/`, `captures/photo_sim/` | Simulated captures (not real scans or photos, D33) |
| `splits/` | Base and sample IDs per split |
| `manifest.json` | SHA-256 of every file, per split and overall |
| `qa/` | Generator QA report |

File names and version IDs do not show the class. Read pairs from `labels_eclass.csv`.

## Labels

- `expected_verdict`: Identical (exact copy, digital only), Equivalent, Tampered, Inconclusive, Not supported (redacted, D47).
- `verdict_3level`: the same with Tampered named "Materially Altered".
- `severity`: Major, Minor or None, by the locked rules (D42 to D46).
- `e_class` (mapping in `ml/data/e_class.py`):

| E-class | Meaning | Generator subtypes |
|---|---|---|
| E0 | Format only or exact copy | NONE, F_* (font, reflow, spacing, date and number format, section format, name case, metadata, honorific) |
| E1 | Name substitution | T_NAME, T_NAME_ADDED, N_ENTITY_NAME |
| E2 | Date alteration | T_DATE, N_ENTITY_DATE |
| E3 | Time alteration | T_TIME, N_ENTITY_TIME |
| E4 | Amount or number change | T_AMOUNT, T_AGE, T_ID, T_VEHICLE, T_ID_SPACE, N_ENTITY_NUMBER |
| E5 | Legal provision change | T_SECTION, T_SECTION_ADDED |
| E6 | Negation flip | N_NEGATION |
| E7 | Role reversal | E_ROLE_SWAP |
| E8 | Location change | T_PLACE |
| E9 | Evidence ID or description edit | E_EXHIBIT_ID, E_EXHIBIT_DESC |
| E10 | Clause insertion | N_SENTENCE_ADD, N_SENTENCE_ADD_ENTITY |
| E11 | Clause deletion | N_SENTENCE_REMOVE, N_SENTENCE_REMOVE_ENTITY |
| E12 | Modal or quantifier shift (Minor) | N_MODAL |
| E13 | Custody chain edit | C_CUSTODY_HOLDER, C_CUSTODY_DATE, C_CUSTODY_ENTRY_REMOVED |
| E14 | Backdating (all dates before the BNS commencement date while BNS is cited) | T_BACKDATE |
| E15 | Seal or signature | V_STAMP_REMOVED, V_STAMP_SWAPPED, V_SIGNATURE_SWAPPED, A_COURT_STAMP |
| E16 | Other content edit (wording, order, minor field) | N_WORD_SWAP, N_REWORD, N_PUNCT, T_NAME_ORDER, T_ADDRESS, T_RANK |
| E17 | Page change | P_PAGE_ADDED, P_PAGE_REMOVED, P_PAGE_REORDER |
| E18 | Annotation | A_MARGIN_NOTE, A_NOTE_OVER_FIELD |
| E19 | Unreadable or redacted | B_BLUR_ONLY (Inconclusive), B_BLUR_PLUS_EDIT, R_REDACTED (Not supported) |

## Counts (samples, all captures)

| e_class | train | val | test | test_unseen |
|---|---|---|---|---|
| E0 | 3,780 | 810 | 810 | 810 |
| E1 | 420 | 90 | 90 | 90 |
| E2 | 420 | 90 | 90 | 90 |
| E3 | 351 | 63 | 75 | 78 |
| E4 | 420 | 90 | 90 | 90 |
| E5 | 588 | 126 | 126 | 126 |
| E6 | 357 | 78 | 75 | 72 |
| E7 | 378 | 90 | 78 | 60 |
| E8 | 420 | 90 | 90 | 90 |
| E9 | 588 | 126 | 126 | 126 |
| E10 | 420 | 90 | 90 | 90 |
| E11 | 420 | 90 | 90 | 90 |
| E12 | 366 | 75 | 84 | 81 |
| E13 | 378 | 81 | 81 | 81 |
| E14 | 588 | 126 | 126 | 126 |
| E15 | 420 | 90 | 90 | 90 |
| E16 | 420 | 90 | 90 | 90 |
| E17 | 420 | 90 | 90 | 90 |
| E18 | 420 | 90 | 90 | 90 |
| E19 | 420 | 90 | 90 | 90 |

| verdict_3level | train | val | test | test_unseen |
|---|---|---|---|---|
| Identical | 140 | 30 | 30 | 30 |
| Equivalent | 3,640 | 780 | 780 | 780 |
| Materially Altered | 7,932 | 1,695 | 1,701 | 1,680 |
| Inconclusive | 141 | 30 | 30 | 30 |
| Not supported | 141 | 30 | 30 | 30 |

Harmless (E0) share: 31.6%. Severity over all samples: Major 10,797, Minor 2,211, None 6,672.

## Checks run (18 October 2026)

| Check | Result |
|---|---|
| `ml.data.validate_labels` | PASS, 0 errors, 0 warnings, 4 of 4 split hashes match |
| `ml.data.generator.check` | PASS: 0 label/declaration mismatches, 0 text-layer failures, 0 personal-data hits, no class missing from a split |
| `analysis/dataset_audit/audit_v3.py` | 18 of 18 checks pass: no missing or corrupt files; no class code in printed text, PDF metadata or file paths; no version tag in the footer; no split leakage; val and test 15% of seen bases; 230 distinct narratives; 0 cross-split narrative pairs above 0.9 similarity (max 0.84); 31.6% harmless; every E-class present with at least 75 test samples; test_unseen shares 0% of templates with train; all five verdicts and both severities in every split |
| `pytest tests` | 644 passed, 9 skipped (Docker), 0 failed |
| `analysis/dataset_audit/ocr_v3.py` (RapidOCR, random sample, seed 20261018) | Changed value readable after capture: digital 15 of 15, scan 30 of 30, photo 30 of 30. Header fields of harmless copies read: 37 of 37 samples. Small sample: with 30 of 30 the true rate is very likely above about 90%. The comparison ignores spaces, so it does not confirm space-inside-ID edits (T_ID_SPACE) |

Label file hashes: `labels_eclass.csv` `d0bedf37a908b10a9bb7eecfd4a67894711368aeca56fe604fd11ad3afaa61b6`, `labels.csv` `925b53d1a4074f91a4107a507d426b17fcedcc479b2c88eec17452be3b79d758`. Split hashes are in `docs/DATASET.md` and `manifest.json`.

## Known limitations

1. **Captures are simulated** and one difficulty level only. Harder and real captures come in Phase 10 (Stage 3).
2. **BNS section numbers are example values** (D38), and the BNS commencement date used by E14 (1 July 2024) is the one recorded in D34. TODO: verify both against official sources before the paper describes them as correct.
3. **Seen-family test documents share sentence templates with train** (by design). Report narrative-hash results on test_unseen as the generalisation number.
4. **The 10% human re-check is not done.** The sample to review is `analysis/dataset_v3_build/recheck_10pct.csv` (1,968 rows).
5. The size is below the `BUILD_PLAN.md` Phase 4 figure of 1,000 originals; D95 sets 230.
