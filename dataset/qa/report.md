# FIR-Tamper v0: QA report

Seed: 20261015. Versions: 900. Samples: 2700.
Overall automated result: PASS


## 1. Labels agree with class declarations

Mismatches: 0

## 2. Text-layer check of digital PDFs

Versions checked: 860 (blurred versions are image-only and are skipped). Failures: 0.

## 3. No real personal data

Checked: no 10-digit numbers starting 6 to 9, every vehicle number uses the invented ZZ code, no e-mail addresses or URLs, every name token comes from the invented lists, every phone number starts with 10.

Problems: 0

## 4. Split leakage

Base documents in more than one split: 0

## 5. Coverage per class and split

Counts are versions (samples = versions x 3 capture types).

| Class | Group | Worked example | Open question | Expected verdict | train | val | test |
|---|---|---|---|---|---|---|---|
| NONE | none | 1 | - | Identical (digital) / Equivalent (scan, photo) | 42 | 9 | 9 |
| F_FONT | format | 4 | - | Equivalent | 21 | 5 | 5 |
| F_REFLOW | format | 12 | E3 | Equivalent | 21 | 5 | 5 |
| F_SPACING | format | 12 | E3 | Equivalent | 21 | 4 | 5 |
| F_DATETIME_FORMAT | format | 8 | - | Equivalent | 21 | 4 | 4 |
| F_NUMBER_FORMAT | format | 7 | - | Equivalent | 22 | 4 | 4 |
| F_SECTION_FORMAT | format | 10 | Q3 | Equivalent | 21 | 5 | 4 |
| F_NAME_CASE | format | 11 | - | Equivalent | 21 | 5 | 5 |
| F_METADATA | format | 5 | E11 | Equivalent | 20 | 4 | 4 |
| T_DATE | field | 14 | - | Altered, Critical | 14 | 3 | 3 |
| T_TIME | field | 15 | - | Altered, Critical | 14 | 3 | 3 |
| T_AMOUNT | field | 16 | - | Altered, Critical | 14 | 3 | 3 |
| T_AGE | field | 14-20 (same rule) | - | Altered, Critical | 14 | 3 | 3 |
| T_NAME | field | 17 | - | Altered, Critical | 14 | 3 | 3 |
| T_NAME_ADDED | field | 18 | - | Altered, Critical | 14 | 3 | 3 |
| T_SECTION | field | 19 | - | Altered, Critical | 14 | 3 | 2 |
| T_VEHICLE | field | 20 | - | Altered, Critical | 14 | 3 | 3 |
| T_ID | field | 14-20 (same rule) | - | Altered, Critical | 15 | 3 | 3 |
| T_PLACE | field | 14-20 (same rule) | - | Altered, Critical | 14 | 3 | 4 |
| T_RANK | field | 14-20 (same rule) | - | Altered, Critical | 14 | 3 | 3 |
| T_ADDRESS | field | 14-20 (same rule) | Q5 | Altered, Minor | 13 | 3 | 2 |
| N_WORD_SWAP | narrative | 21 | - | Altered, Minor | 14 | 3 | 3 |
| N_NEGATION | narrative | 22 | E5 | Altered, Minor | 14 | 3 | 3 |
| N_SENTENCE_ADD | narrative | 23 | - | Altered, Minor | 14 | 3 | 3 |
| N_SENTENCE_REMOVE | narrative | 24 | - | Altered, Minor | 14 | 3 | 3 |
| N_REWORD | narrative | 25 | - | Altered, Minor | 14 | 3 | 3 |
| N_PUNCT | narrative | 26 | E4 | Altered, Minor | 14 | 3 | 3 |
| N_ENTITY | narrative | 22 (E5 option b) | E5;Q4 | Altered, Minor | 14 | 3 | 3 |
| V_STAMP_REMOVED | visual | 27 | - | Altered, Critical | 14 | 3 | 3 |
| V_STAMP_SWAPPED | visual | 28 | - | Altered, Critical | 14 | 3 | 3 |
| V_SIGNATURE_SWAPPED | visual | 29 | - | Altered, Critical | 14 | 3 | 3 |
| P_PAGE_ADDED | page | 31 | E6 | Altered, Minor | 14 | 3 | 3 |
| P_PAGE_REMOVED | page | 32 | E6 | Altered, Critical or Minor by page content | 14 | 3 | 3 |
| P_PAGE_REORDER | page | 33 | E7 | Altered, Minor | 14 | 3 | 3 |
| A_MARGIN_NOTE | annotation | 38 | E8 | Altered, Minor | 14 | 3 | 4 |
| A_COURT_STAMP | annotation | 38 (E8) | E8 | Altered, Critical | 14 | 3 | 3 |
| R_REDACTED | redaction | E15 | E15 | Altered, Critical | 14 | 3 | 3 |
| B_BLUR_ONLY | blur | 36 | - | Inconclusive | 14 | 3 | 3 |
| B_BLUR_PLUS_EDIT | blur | 36 (E1) | E1 | Inconclusive | 14 | 3 | 3 |

Classes missing from a split: none

Untouched or format-only samples: 900 of 2700 (33.3%). Target: about one third.

Expected verdicts over all samples: Altered 1680, Equivalent 840, Identical 60, Inconclusive 120

## 6. Second-person re-check

270 samples (10%) picked at random (seed 7) into `qa/recheck_10pct.csv`. Status: NOT DONE. A second person must open each file, compare it with the base document, and fill in the reviewer columns.
