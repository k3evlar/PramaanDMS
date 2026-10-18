# dataset_v2 audit: how to rerun

These scripts audit `dataset_v2/` (the FIR-Tamper E0 to E15 build). They only read the dataset. Everything they write goes to this folder.

## Setup (once)

```powershell
cd analysis\dataset_audit
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-audit.txt
```

RapidOCR downloads its ONNX model files into the venv the first time it runs.

## Run

```powershell
.venv\Scripts\python run_all.py              # full audit, about 25 minutes
.venv\Scripts\python run_all.py --skip-ocr   # reuse the last OCR run
```

## Files

| File | What it does |
|---|---|
| `audit_lib.py` | Paths, loaders and the spec the dataset is checked against (classes, allowed values, 3-level verdict mapping) |
| `step1_inventory.py` | Folder tree, file counts and sizes, orphans, missing files, corrupt files |
| `step2_schema.py` | Every label row against the schema, the verdict and severity rules, the JSON diff, change log and split map |
| `step3_coverage.py` | Count tables and the PNG charts in `charts/` |
| `step4_splits.py` | Leakage by base document, near-duplicate bases across splits, split ratios, coverage in validation and test |
| `step5_tamper.py` | Every original/variant pair checked against its class definition, plus 5 random examples per class |
| `step6_quality.py` | Realism markers, personal data patterns, language, templating, image quality of every capture |
| `step6_ocr.py` | OCR on a stratified sample; CER, field match rate, tampered value survival, label readable in image |
| `build_issues.py` | Builds `issues.csv` from the outputs (issues that are fixed drop out on rerun) |
| `run_all.py` | Runs everything and writes `stats.json` |
| `outputs/` | Raw JSON per step, plus the teammate's and the project's validator output |
| `compare_v0_narratives.py` | Narrative diversity and template overlap of `dataset/` (v0) vs `dataset_v2/` |
| `REPORT.md` | The written report (by hand, from the numbers in `stats.json`) |
| `IMPROVEMENT_PLAN.md` | How to turn the dataset into one the Legal Hash can train and be tested on |

## Licences of audit-only tools

numpy (BSD-3-Clause), Pillow (MIT-CMU), opencv-python-headless (Apache-2.0), pypdfium2 (Apache-2.0 or BSD-3-Clause), matplotlib (Matplotlib licence, PSF-based), RapidFuzz (MIT), RapidOCR (Apache-2.0), onnxruntime (MIT). PP-OCR model weights: Apache-2.0 per PaddleOCR, TODO: verify for the exact PP-OCRv6 files RapidOCR downloads. None is non-commercial. These are audit tools only. If any of them moves into the product, add it to `docs/LICENCES.md`.
