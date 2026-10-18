# Dataset card: FIR-Tamper

The full description is in `dataset/README.md`. This card holds the summary and the hashes that results must cite (`BUILD_PLAN.md`, extra rules for ML phases).

## Versions

| Version | Date | Content | Status |
|---|---|---|---|
| v0 | 15 Oct 2026 | English only. 60 base documents (24 FIR, 21 charge sheet, 15 witness statement), 900 versions, 2,700 samples (digital, simulated scan, simulated photo). 40 classes. | Built, automated QA passed, human 10% re-check not done |
| v3 (Stage 2) | 18 Oct 2026 | English only. 230 base documents (92 FIR, 69 charge sheet, 69 witness statement), 6,560 versions, 19,680 samples (digital, simulated scan, simulated photo). E0 to E19 in `labels_eclass.csv`; held-out test_unseen split (template family B). Folder `dataset_v3/`, card `dataset_v3/README.md`, plan `docs/DATASET_V3_PLAN.md` | Built (D92 to D96). Validator PASS, QA PASS, audit 18 of 18. Human 10% re-check not done |
| v3 (Stage 1) | 18 Oct 2026 | English only. 200 base documents (80 FIR, 60 charge sheet, 60 witness statement), 3,000 versions, 9,000 samples (digital, simulated scan, simulated photo). 46 generator classes under the locked rules, mapped to E0 to E19 in `labels_eclass.csv`. Folder `dataset_v3/`, card `dataset_v3/README.md`, plan `docs/DATASET_V3_PLAN.md` | Replaced by Stage 2 (D96). Validator PASS, QA PASS, audit 13 of 13. Human 10% re-check not done |
| v1 | replaced | Phase 4 target: at least 1,000 originals and 5,000 labelled pairs, English and Hindi, plus the equivalence traps and adversarial edits that v0 does not cover | Replaced by v3 (D92). Hindi is out of scope (D39) |

## v3 Stage 2 hashes (seed 20261018, current)

| Split | Base documents | Samples | SHA-256 |
|---|---|---|---|
| train | 140 | 11,994 | `be1ed76ccdc6fc4571521a1d3cd2070f2682bc709be39b34fac9915610d0e664` |
| val | 30 | 2,565 | `76e669ab54bbb203e8ed99cc393c567aca8a1d48bbbe73ca48cb7e56cf35b863` |
| test | 30 | 2,571 | `a1e2806e2488c7e100b1521abf98dd7cf90cdf4df85f767de50e2d63b37fd9be` |
| test_unseen | 30 | 2,550 | `8a0997f4e2b10a64546fd12f36ff9ef67f84bdb0361eeaac5eed14216c4d7332` |
| all | 230 | 19,680 | `62e59a668b8333ded9e8583d20ae8ce36e7c792b8c8787694a2efcc850f45016` |

How to regenerate: see `dataset_v3/README.md`. Results that use v3 must cite these hashes.

## v3 Stage 1 hashes (replaced by Stage 2; the files are no longer on disk)

| Split | Base documents | Samples | SHA-256 |
|---|---|---|---|
| train | 140 | 6,300 | `0d43be9408faab62b2c256ff9eb5dbf036d7782f229a4d4478803e35720aa25f` |
| val | 30 | 1,350 | `72e5bdc0cf943e42eea294679be68c5096bb5a81297b021cd958999f10617587` |
| test | 30 | 1,350 | `5a2ea661148282faffc969be9c1f6914f8405ac1dced0655e8fe486b662ba91f` |
| all | 200 | 9,000 | `916440f06ccf3ad08f2845e60f23b36bb795256383d22258e83d21cb00a3a710` |

Stage 1 cannot be rebuilt: the generator changed in D96, and with git paused (D28) the earlier code is not stored anywhere.

## v0 hashes (seed 20261015)

| Split | Base documents | Samples | SHA-256 |
|---|---|---|---|
| train | 42 | 1,890 | `d2b04b520190d5988bcf5a13ce9f40a7955cf5a2bfcf40800016912c9baa04ee` |
| val | 9 | 405 | `d651b1723b63f743603b3aec8b40fb0ece250e79407c2ca163f5d77b99c75d30` |
| test | 9 | 405 | `6a5647a96b009c8eb8ffac5053e0faef5bd34f3c53f585ba22acabb78de99695` |
| all | 60 | 2,700 | `fc5b29558214876d4990bb576dc5e83e709e98097bf6348028fc89b0d489819d` |

How to regenerate: `.venv/Scripts/python -m ml.data.generator.build --out dataset` (pinned libraries in `ml/requirements-data.txt`). **Note (18 Oct 2026):** after the D96 generator changes this command no longer reproduces the v0 hashes above. The v0 files in `dataset/` are still on disk; to rebuild v0 exactly, the pre-D96 generator code would be needed, and it is not stored (git paused, D28).

## Phase 4 exit criteria against v0

| Exit criterion (`BUILD_PLAN.md` Phase 4) | v0 |
|---|---|
| Same seed gives byte-identical dataset | Met. Built twice, same hash. Also a unit test |
| At least 1,000 originals and 5,000 labelled pairs | Not met. 60 originals, 900 pairs (2,700 samples with captures) |
| Every tamper type and trap type present in every split | Met for the 40 v0 classes. Hindi traps (Devanagari digits, Hindi dates), homoglyphs and zero-width characters are not in v0 |
| Split hashes recorded in DATASET.md | Met (above) |
| Label checker on a random sample of 50 (test) | Automated checks cover all 900 versions. The human re-check of 270 samples is not done |

Phase 4 therefore stays open.
