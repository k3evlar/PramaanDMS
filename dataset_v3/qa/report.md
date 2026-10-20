# FIR-Tamper v0: QA report

Seed: 20261018. Versions: 6560. Samples: 19680.
Overall automated result: PASS


## 1. Labels agree with class declarations

Mismatches: 0

## 2. Text-layer check of digital PDFs

Versions checked: 6407 (blurred versions are image-only and are skipped). Failures: 0.

## 3. No real personal data

Checked: no 10-digit numbers starting 6 to 9, every vehicle number uses the invented ZZ code, no e-mail addresses or URLs, every name token comes from the invented lists, every phone number starts with 10.

Problems: 0

## 4. Split leakage

Base documents in more than one split: 0

## 5. Coverage per class and split

Counts are versions (samples = versions x 3 capture types).

| Class | Group | Worked example | Decision | Expected verdict | train | val | test | test_unseen |
|---|---|---|---|---|---|---|---|---|
| NONE | none | 1 | - | Identical (digital) / Equivalent (scan, photo) | 140 | 30 | 30 | 30 |
| F_FONT | format | 4 | - | Equivalent | 128 | 29 | 28 | 27 |
| F_REFLOW | format | 12 | D40 | Equivalent | 128 | 27 | 28 | 26 |
| F_SPACING | format | 12 | D40 | Equivalent | 129 | 27 | 27 | 27 |
| F_DATETIME_FORMAT | format | 6, 8 | - | Equivalent | 128 | 27 | 27 | 27 |
| F_NUMBER_FORMAT | format | 7, 13 | D40 | Equivalent | 128 | 28 | 27 | 28 |
| F_SECTION_FORMAT | format | 10, 14 | D44 | Equivalent | 98 | 21 | 21 | 21 |
| F_NAME_CASE | format | 11 | - | Equivalent | 128 | 28 | 28 | 27 |
| F_METADATA | format | 5 | - | Equivalent | 126 | 26 | 28 | 29 |
| F_HONORIFIC | format | 9 | D48 | Equivalent | 127 | 27 | 26 | 28 |
| T_DATE | field | 16 | - | Tampered, Major | 70 | 15 | 15 | 15 |
| T_TIME | field | 17 | - | Tampered, Major | 58 | 10 | 13 | 13 |
| T_AMOUNT | field | 18 | - | Tampered, Major | 23 | 4 | 5 | 4 |
| T_AGE | field | 18 (same rule) | - | Tampered, Major | 24 | 5 | 4 | 5 |
| T_NAME | field | 19 | - | Tampered, Major | 47 | 10 | 10 | 10 |
| T_NAME_ADDED | field | 20 | - | Tampered, Major | 46 | 10 | 10 | 10 |
| T_SECTION | field | 21 | D44 | Tampered, Major | 98 | 21 | 21 | 21 |
| T_SECTION_ADDED | field | 22 | D44 | Tampered, Major | 98 | 21 | 21 | 21 |
| T_VEHICLE | field | 23 | - | Tampered, Major | 24 | 5 | 5 | 6 |
| T_ID | field | 23 (same rule) | - | Tampered, Major | 23 | 5 | 5 | 5 |
| T_ID_SPACE | field | 24 | D40 | Tampered, Major | 23 | 5 | 6 | 5 |
| T_PLACE | field | 16 (same rule) | - | Tampered, Major | 140 | 30 | 30 | 30 |
| T_RANK | field | 16 (same rule) | - | Tampered, Major | 23 | 5 | 6 | 5 |
| T_ADDRESS | field | 26 | - | Tampered, Minor | 23 | 5 | 3 | 5 |
| T_NAME_ORDER | field | 25 | D44 | Tampered, Minor | 23 | 5 | 5 | 5 |
| N_WORD_SWAP | narrative | 27 | - | Tampered, Minor | 24 | 5 | 6 | 5 |
| N_NEGATION | narrative | 28 | D42 | Tampered, Major | 119 | 26 | 25 | 24 |
| N_SENTENCE_ADD | narrative | 31 | - | Tampered, Minor | 70 | 15 | 15 | 15 |
| N_SENTENCE_ADD_ENTITY | narrative | 32 | D45 | Tampered, Major | 70 | 15 | 15 | 15 |
| N_SENTENCE_REMOVE | narrative | 33 | - | Tampered, Minor | 70 | 15 | 14 | 15 |
| N_SENTENCE_REMOVE_ENTITY | narrative | 32 (removal) | D45 | Tampered, Major | 70 | 15 | 16 | 15 |
| N_REWORD | narrative | 34 | - | Tampered, Minor | 24 | 5 | 5 | 5 |
| N_PUNCT | narrative | 35 | - | Tampered, Minor | 23 | 5 | 5 | 5 |
| V_STAMP_REMOVED | visual | 36 | - | Tampered, Major | 35 | 8 | 8 | 7 |
| V_STAMP_SWAPPED | visual | 37 | - | Tampered, Major | 35 | 7 | 7 | 8 |
| V_SIGNATURE_SWAPPED | visual | 38 | - | Tampered, Major | 35 | 7 | 7 | 8 |
| A_COURT_STAMP | annotation | 39 | D46 | Tampered, Major | 35 | 8 | 8 | 7 |
| P_PAGE_ADDED | page | 40 | D43 | Tampered, Major | 47 | 10 | 10 | 10 |
| P_PAGE_REMOVED | page | 41 | D43 | Tampered, Major | 46 | 10 | 10 | 10 |
| P_PAGE_REORDER | page | 42 | D43 | Tampered, Major | 47 | 10 | 10 | 10 |
| A_MARGIN_NOTE | annotation | 43 | D46 | Tampered, Minor | 70 | 15 | 15 | 15 |
| A_NOTE_OVER_FIELD | annotation | 44 | D46 | Tampered, Major | 70 | 15 | 15 | 15 |
| B_BLUR_ONLY | blur | 47 | D41 | Inconclusive | 47 | 10 | 10 | 10 |
| B_BLUR_PLUS_EDIT | blur | 48 | D41 | Tampered, Major | 46 | 10 | 10 | 10 |
| R_REDACTED | redaction | 51 | D47 | Not supported | 47 | 10 | 10 | 10 |
| N_ENTITY_NAME | narrative | 30 | D45 | Tampered, Major | 47 | 10 | 10 | 10 |
| N_ENTITY_DATE | narrative | 29 | D45 | Tampered, Major | 70 | 15 | 15 | 15 |
| N_ENTITY_TIME | narrative | 29 (same rule) | D45 | Tampered, Major | 59 | 11 | 12 | 13 |
| N_ENTITY_NUMBER | narrative | 29 (same rule) | D45 | Tampered, Major | 23 | 6 | 5 | 5 |
| E_ROLE_SWAP | field | 19 (same rule) | - | Tampered, Major | 126 | 30 | 26 | 20 |
| E_EXHIBIT_ID | field | 23 (same rule) | - | Tampered, Major | 42 | 9 | 9 | 9 |
| E_EXHIBIT_DESC | field | 16 (same rule) | - | Tampered, Major | 154 | 33 | 33 | 33 |
| N_MODAL | narrative | 27 (same rule) | - | Tampered, Minor | 122 | 25 | 28 | 27 |
| C_CUSTODY_HOLDER | field | 19 (same rule) | - | Tampered, Major | 42 | 9 | 9 | 9 |
| C_CUSTODY_DATE | field | 16 (same rule) | - | Tampered, Major | 42 | 9 | 9 | 9 |
| C_CUSTODY_ENTRY_REMOVED | field | 20 (same rule) | - | Tampered, Major | 42 | 9 | 9 | 9 |
| T_BACKDATE | field | 16 (same rule) | D52 | Tampered, Major | 196 | 42 | 42 | 42 |

Classes missing from a split: none
Classes not used in this build: ['N_ENTITY']

Untouched or format-only samples: 6210 of 19680 (31.6%). Target: about one third.

Expected verdicts over all samples: Equivalent 5980, Identical 230, Inconclusive 231, Not supported 231, Tampered 13008

## 6. Second-person re-check

1968 samples (10%) picked at random (seed 7) into `qa/recheck_10pct.csv`. Status: NOT DONE. A second person must open each file, compare it with the base document, and fill in the reviewer columns.
