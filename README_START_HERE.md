# PramaanDMS dataset starter kit

## First run
1. Copy the contents of this kit into your existing `PramaanDMS-Dataset` folder.
2. Copy the three `.md` files from your existing `schemas` folder only if you want this kit's schema copies; your existing files may be retained.
3. Open VS Code Terminal at the project root.
4. Run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install reportlab pandas
   python scripts\generate_dataset.py --bases 5
   ```
5. Output will be created in `base_docs/`, `tampered/`, `annotations/`, and `labels.csv`.

The generator is a starter pipeline for **five fictional pilot records**, not the full dataset. Review every PDF and label before increasing the count. It generates a limited set of example classes (E0, E1, E2, E3, E4, E6, E8, E9, E10, E11, E12) and does not claim to cover E1–E15 yet. E5, E7, E13, E14, E15 and all capture variants need separate implementation and review.

## Important schema alignment issue
The user-provided canonical schema has 27 fields. The earlier task brief also mentioned additional fields such as age, complainant address and narrative, but these are not in the 27-field list. This starter kit keeps the 27 fields exactly as supplied and uses `offence_description` and `evidence_description` for narrative text. Confirm with your supervisor whether the extra fields must be added before expanding.

## Synthetic data only
All names, places, institutions, identifiers and case details are invented. These PDFs are test artifacts, not real legal documents.
