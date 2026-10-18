# PramaanDMS Synthetic Document Dataset — V2

## Status

This is a synthetic, English-language pilot dataset for developing and evaluating meaning-aware document comparison and tampering detection workflows. All documents are fictional test records, not official records. The dataset is **not yet research-final** until the independent review described below is completed and recorded.

## Current dataset snapshot

Based on the project's latest successful terminal audit:

- 50 base documents
- 850 digital PDF samples
- 850 simulated print-scan images
- 850 simulated phone-photo images
- 2,550 labelled sample rows in `labels.csv`
- 16 tampering/control classes: E0–E15
- Base-document splits currently recorded in `labels.csv`, `splits.csv`, and `split_manifest.json`
- Latest structural audit: 0 errors, 1 warning (E0 count expectation)

Do not regenerate or change the current split unless a genuine defect is found. Treat the current `dataset_v2` output as the working source of truth.

## Important limitations

1. Print-scan and phone-photo files are **synthetically simulated capture effects**. They are not actual scans or camera photographs.
2. E15 currently uses a clearly marked synthetic seal-region alteration. It is a visual test marker, not a realistic forensic signature/seal forgery simulation.
3. The automated validator checks file paths, sample identifiers, class coverage, selected structured-field change rules, capture labels, and split consistency. It does not prove every semantic change is meaningful or every image is legible.
4. `E0` appears 100 times in the digital class counts because each base document has both its original base PDF and a separate unchanged E0 control copy. This is expected under the current generation design; the audit warning reflects its current expectation of 50 E0 rows.
5. Splits are grouped by `original_id` so variants of the same base document should remain in one split. Check `split_manifest.json` for the actual current counts and methodology.
6. This dataset is synthetic and relatively small. Results from it should not be presented as proof of real-world forensic reliability.

## Directory guide

- `base_docs/`: original synthetic base records (`.json` structured data and `.pdf` renderings).
- `tampered/E0` … `tampered/E15/`: generated control and tampering variants.
- `captures/print_scan/`: simulated print-scan JPGs.
- `captures/phone_photo/`: simulated phone-photo JPGs.
- `annotations/change_log.csv`: annotations/change log for digital samples.
- `annotations/capture_variants.csv`: capture-variant log.
- `labels.csv`: one row per digital or capture sample, including labels, file paths, and split assignment.
- `splits.csv`: base-document split mapping.
- `split_manifest.json`: split counts and methodology.
- `dataset_manifest.json`: generator-produced dataset summary.
- `schemas/`: scope, critical-field, and tampering definitions.
- `scripts/`: generation, capture simulation, validation, split, and audit scripts.

## `labels.csv` fields

- `sample_id`: unique sample identifier.
- `doc_type`: document type.
- `original_id`: base document identifier used for grouping and leakage-safe splitting.
- `tamper_class`: E0–E15 label.
- `field_changed`: field or region declared as changed.
- `page_affected`: page information from the generator; verify during review.
- `severity`: declared severity label.
- `expected_verdict`: expected label such as `Valid` or `Tampered`.
- `capture_type`: `digital`, `print_scan`, or `phone_photo`.
- `file_path`: path relative to the project root.
- `split`: `train`, `validation`, or `test`.

## Tampering classes

Use `schemas/TAMPERING_DEFINITION.md` as the authoritative definition of E0–E15. Do not infer a class definition solely from a filename. The JSON sidecars, PDF/image content, `labels.csv`, and change log should agree.

## Recommended review protocol

Before research or model evaluation:

1. Use `annotations/independent_review.csv` to record a second-person review.
2. Review at least 10% of sample rows (255 of 2,550 rows) selected across all capture types and tampering classes. Include some samples from each document type.
3. For each reviewed row, confirm the file exists, the document is legible, the stated class is appropriate, the declared changed field matches the content, the expected verdict is appropriate, and the capture transformation has not obscured or changed the semantic content.
4. For E0, confirm that meaning and structured values remain unchanged.
5. For E15, record that it is a synthetic visual marker rather than a realistic forgery simulation.
6. Record `pass`, `fail`, or `needs_correction`, plus a short note and reviewer/date.
7. Fix failed rows and rerun `scripts/validate_dataset.py` and `scripts/final_dataset_audit.py`. Do not silently overwrite review records.

## Reproducibility

Record the Python version, installed package versions, generator command, random seed, and date for each dataset release. Preserve the scripts and manifests used to produce the release.

## Ethical and legal note

All records are synthetic. Do not add real case records, real personal names, addresses, signatures, seals, or other sensitive case data without appropriate authorization and a documented governance process.
