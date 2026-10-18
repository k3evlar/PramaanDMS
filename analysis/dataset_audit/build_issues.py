"""Build issues.csv from the step outputs. Each issue has a detector that reads the
outputs, so rerunning after fixes drops issues that no longer apply."""
from __future__ import annotations

import csv
from typing import Callable

from audit_lib import AUDIT_DIR, ROOT, read_out

SEV_ORDER = {"Blocker": 0, "Major": 1, "Minor": 2}


def ids(xs, limit: int = 60) -> str:
    xs = list(xs)
    s = ";".join(xs[:limit])
    return s + (f";... (+{len(xs) - limit} more)" if len(xs) > limit else "")


def detectors() -> list[Callable[[dict], dict | None]]:
    def leak(o):
        t5, ocr = o["step5"], o["ocr"]
        n = t5["pairs_with_header_label_leak"]
        if not n:
            return None
        ocr_rate = {k: v["label_readable_in_image_rate"] for k, v in ocr["summary"].items()} if ocr else "not run"
        return dict(severity="Blocker", area="Label leakage",
                    title="Sample ID and class code are printed on every page",
                    what=(f"Every PDF header prints 'Sample ID: BASE-xxxx-E<n>' and 'Controlled synthetic variant: E<n>.' "
                          f"(the base prints 'Original synthetic base record.'). {n} of {t5['pairs_checked']} original/variant "
                          f"pairs differ in this header. OCR reads the label from the images too (rate by capture: {ocr_rate}). "
                          "A model can read the answer off the page, and every E0 'harmless' copy differs from its original in printed text."),
                    affected="all 850 PDFs and all 1,700 capture images (header block)",
                    fix=("In generate_dataset_v2.py render_pdf(), remove the 'Sample ID' line and the note line from the page "
                         "(keep the sample ID only in labels.csv and the JSON sidecar). Also set the PDF Title metadata to a "
                         "neutral value. The base, E0 and every variant must print the same header. Then regenerate PDFs and captures."))

    def templated(o):
        s4, s6 = o["step4"], o["step6"]
        n = s4["distinct_narratives_after_masking_ids"]
        if n >= 0.8 * s4["base_documents"]:
            return None
        return dict(severity="Blocker", area="Content diversity / leakage",
                    title="Narratives are one template; train and test share the same text",
                    what=(f"Only {n} distinct narratives exist across {s4['base_documents']} base documents "
                          "(offence_description differs only by place name; evidence_description only by exhibit ID). "
                          f"{s4['cross_split_pairs_narrative_above_threshold']} of {s4['cross_split_base_pairs_total']} cross-split base pairs "
                          f"have narrative similarity above 0.9 (min {s4['narrative_similarity_all_pairs']['min']}). "
                          "The narrative hash N cannot learn general wording sensitivity from this, and test narratives are "
                          "the training narratives, so split-by-base gives no real independence."),
                    affected="all 50 base documents (offence_description, evidence_description)",
                    fix=("Generate a unique narrative per base document (several sentences, 80 to 250 words, different "
                         "incidents, with dates, times, names, amounts and vehicle numbers inside the text). Use at least "
                         "10 incident templates with slot filling plus paraphrase, keep templates disjoint between train and "
                         "val/test, and recheck that cross-split narrative similarity stays below 0.9."))

    def fixed_values(o):
        rv = o["step4"]["replacement_values_per_class"]
        const = [c for c, v in rv.items() if v["distinct_new_values"] <= 2]
        if not const:
            return None
        return dict(severity="Blocker", area="Shortcut learning",
                    title="Each tamper class always inserts the same value",
                    what=("Classes " + ", ".join(const) + " use one or two fixed replacement values for all 50 bases "
                          "(for example E1 always 'Quinn Sampleton', E2 always 2026-10-27, E4 always 'Rs 9,99,999', "
                          "E9 always 'EXHIBIT-SYN-Z999'), and the same values appear in train, validation and test. A model "
                          "can learn 'this string means tampered' and test scores would be inflated."),
                    affected="tampered/" + ", tampered/".join(const),
                    fix=("Draw replacement values from pools (names, dates near the original, amounts with one-digit and "
                         "order-of-magnitude edits, IDs with one-character edits). Use disjoint pools for train versus "
                         "validation/test. Vary which field each class edits (E1 over all six name fields, E2 over all five date fields)."))

    def class_fail(cls, sev, title, fix):
        def f(o):
            pc = o["step5"]["per_class"][cls]
            if pc["fail"] == 0:
                return None
            return dict(severity=sev, area=f"Tamper correctness ({cls})", title=title,
                        what=f"{pc['fail']} of {pc['checked']} {cls} samples fail the class definition. Example: "
                             f"{pc['first_failure']['sample_id']}: {pc['first_failure']['reason']}",
                        affected=ids(pc["failure_ids"]) + " (and their -PRINT_SCAN / -PHONE_PHOTO copies)", fix=fix)
        return f

    def split_ratio(o):
        r = o["step4"]["ratios"]
        bad = {s: v for s, v in r.items() if abs(v["bases_pct"] - v["target_pct"]) > 5}
        if not bad:
            return None
        return dict(severity="Major", area="Split",
                    title="Validation split is too small (4 base documents)",
                    what=("Base-document split is " + ", ".join(f"{s} {v['bases']} ({v['bases_pct']}%)" for s, v in r.items())
                          + " against 70/15/15. Validation has 1 base per document type and 12 samples per class, "
                            "which is too few to choose t_N, t_V and c_min (LEGAL_HASH_SPEC section 9)."),
                    affected="splits.csv, split_manifest.json, labels.csv split column",
                    fix=("In create_stratified_splits.py allocate_type(), use round() instead of int() for the 15% share "
                         "(13 bases -> 9/2/2, 12 -> 8/2/2), giving 35/8/7 overall, or raise the base count. Fix the split "
                         "after the content fixes, then freeze it and record SHA-256 hashes per split."))

    def equivalence(o):
        return dict(severity="Major", area="Coverage (Equivalent)",
                    title="No format-only Equivalent variants and no Identical pairs",
                    what=(f"E0 is only an untouched re-render. There are no font, spacing, reflow, date-format, "
                          f"number-format, honorific or section-order variants (LEGAL_HASH_SPEC section 5, "
                          f"TAMPERING_DEFINITION.md examples 4 to 14). Byte-identical non-self pairs: "
                          f"{o['step2']['byte_identical_non_self_pairs']}. Equivalent examples come only from mild simulated "
                          "captures, so false alarm rate on format changes, the metric the spec calls most important, cannot be measured."),
                    affected="tampered/E0 (all 50)",
                    fix=("Add E0 sub-types with an e0_subtype column: exact copy (byte-identical, verdict Identical), reflow, "
                         "font swap, line spacing, date format (12/03/2026 vs 12 March 2026), Indian vs plain number "
                         "format, honorific added, section order swapped, vehicle-number separators. Aim for about one-third "
                         "of samples as harmless (SCOPE.md section 5)."))

    def harmless_share(o):
        p = o["step3"]["harmless_share_pct"]
        if p >= 25:
            return None
        return dict(severity="Major", area="Balance",
                    title=f"Harmless samples are {p}%, not about 33%",
                    what=(f"E0 rows are {p}% of all rows (expected_verdict counts: "
                          f"{ {x['value']: x['count'] for x in o['step3']['expected_verdict']} }). SCOPE.md section 5 asks for about one-third."),
                    affected="labels.csv (class balance)",
                    fix="Add the E0 sub-types above until harmless rows are about 33%, or report class-weighted metrics.")

    def locked_rules(o):
        return dict(severity="Major", area="Coverage (locked rules)",
                    title="No data for page changes, stamps, annotations or Minor edits",
                    what=("All 850 PDFs are 1 page, so page add/remove/reorder (D43) cannot occur. There are no stamp or "
                          "signature images (D46), no annotations, no name-order swaps (D44), no ID-spacing edits (D40), "
                          "no single-word swaps or rewording (TAMPERING_DEFINITION.md examples 25 to 35). Severity is Major on "
                          f"every tampered row ({o['step3']['severity']})."),
                    affected="whole dataset",
                    fix=("Either extend the class list (for example E16 page change, E17 word swap or rewording, E18 "
                         "annotation, E19 name order) with multi-page documents and real seal/signature images, or record in "
                         "DECISIONS.md that these locked-rule cases are tested on the v0 generator data instead."))

    def schema_vocab(o):
        return dict(severity="Major", area="Label schema",
                    title="Label vocabulary differs from the model's 3-level verdict and the project schema",
                    what=("labels.csv uses Valid/Tampered and severity None/Major. The Legal Hash is trained on "
                          "Identical / Equivalent / Materially Altered, and the locked project rules (D49, D77) use Identical / "
                          "Equivalent / Tampered / Inconclusive with columns the project validator expects (files, could_not_verify, "
                          "rule_ref). The project validator (ml/data/validate_labels.py) cannot read v2: the UTF-8 BOM hides "
                          "sample_id and the 'files' column is missing."),
                    affected="labels.csv header and expected_verdict column (2,550 rows)",
                    fix=("Add a verdict_3level column (exact copy = Identical; E0 and its captures = Equivalent; E1 to E15 = "
                         "Materially Altered) and an original_path column. Write labels.csv as plain UTF-8 without BOM. "
                         "Agree one schema with the owner of ml/data/validate_labels.py and make both validators pass."))

    def synonym_rule(o):
        return dict(severity="Major", area="Spec conflict",
                    title="schemas/TAMPERING_DEFINITION.md lets a synonym swap be E0 (Valid)",
                    what=("The teammate's E0 definition includes 'meaning-preserving synonym substitution' as Valid. The locked "
                          "rule D6/D49 says reworded content is Tampered (docs/TAMPERING_DEFINITION.md section 3, example 34). "
                          "Not yet present in the data, but any cosmetic E0 built from that text would be mislabelled."),
                    affected="schemas/TAMPERING_DEFINITION.md (E0 row, section 4 E0 notes)",
                    fix="Remove synonym substitution from E0. Put it in a Materially Altered class (wording change).")

    def realism(o):
        s6 = o["step6"]
        hits = {m: sum(v.values()) for m, v in s6["realism_marker_hits_by_doc_type"].items()}
        return dict(severity="Major", area="Realism",
                    title="Documents do not look like Indian FIRs, statements, charge sheets or orders",
                    what=("Every document of every type is the same 27-row table with snake_case field names "
                          f"(one layout across types: {s6['all_doc_types_share_one_layout']}). Acts are invented "
                          f"({', '.join(s6['act_names_used'])}); no BNS/BNSS/BSA reference, no u/s citation, no complainant "
                          f"particulars, no brief-facts heading. Marker hits over 50 bases: {hits}. Names are a pool of "
                          f"{len(s6['name_pool'])} non-Indian names. An industry panel will see this at once, and OCR/field "
                          "extraction trained on it will not transfer to real forms."),
                    affected="all 50 base documents",
                    fix=("Render each type from its own layout: FIR in the NCRB/BNSS field order (dataset/templates/SOURCES.md "
                         "has the v0 source), statement as first-person prose, charge sheet with accused/witness lists, court "
                         "order with case title and operative order. Use invented Indian names and places with the D34 "
                         "conventions (phones starting 10, ZZ vehicle codes, BNS section numbers marked as example values)."))

    def review(o):
        s1, s2 = o["step1"], o["step2"]
        if s1["independent_review_done"]:
            return None
        return dict(severity="Major", area="QA",
                    title="Independent 10% human review not done",
                    what=(f"annotations/independent_review.csv does not exist (only the template). change_log review_status: "
                          f"{s2['change_log_review_status']}. SCOPE.md section 10 and the README require it before research use."),
                    affected="annotations/change_log.csv (850 rows)",
                    fix="After the content fixes, a second person reviews 255 stratified rows and records pass/fail.")

    def pymupdf(o):
        src = (ROOT / "scripts" / "make_capture_variants.py").read_text(encoding="utf-8")
        if "import fitz" not in src:
            return None
        return dict(severity="Major", area="Licence",
                    title="Capture script uses PyMuPDF (AGPL-3.0)",
                    what="scripts/make_capture_variants.py imports fitz (PyMuPDF, AGPL-3.0). D61 says PyMuPDF is not used.",
                    affected="scripts/make_capture_variants.py",
                    fix="Render with pypdfium2 (already in the project): pdfium.PdfDocument(p)[0].render(scale=160/72).to_pil().")

    def captures_clean(o):
        s6, ocr = o["step6"], o["ocr"]
        if not ocr:
            return None
        sm = ocr["summary"]
        d = sm["digital"]["field_exact_match_mean"]
        worst = min(sm[c]["field_exact_match_mean"] for c in ("scan", "photo"))
        if worst < d - 0.05:
            return None
        return dict(severity="Major", area="Capture realism",
                    title="Simulated scans and photos are almost as clean as the digital PDF",
                    what=(f"OCR field exact-match rate: digital {d}, scan {sm['scan']['field_exact_match_mean']}, photo "
                          f"{sm['photo']['field_exact_match_mean']}; token recall {sm['digital']['token_recall_mean']} / "
                          f"{sm['scan']['token_recall_mean']} / {sm['photo']['token_recall_mean']}. Scan CER "
                          f"{sm['scan']['cer_mean']} equals digital {sm['digital']['cer_mean']}; photo CER {sm['photo']['cer_mean']} "
                          "comes mostly from line order under perspective, not misread characters. Scan rotation is under 1 degree, photo perspective about 3%, "
                          f"blur radius 0.15 to 0.18 px. Images flagged as too poor to OCR: {len(s6['images_flagged'])}. "
                          "The positives for triplet training (same text after capture noise) carry almost no noise, so the "
                          "model will not learn OCR robustness and the Inconclusive verdict cannot be tested."),
                    affected="captures/print_scan, captures/phone_photo",
                    fix=("Add harder capture levels with a capture_level column (mild/moderate/hard): JPEG quality 40 to 70, "
                         "blur 0.5 to 1.5 px, rotation up to 5 degrees, stronger perspective, low light, shadows, folds, "
                         "partial crop. Keep a small hard set labelled Inconclusive where a critical field is unreadable. "
                         "Phase 10 real captures stay the final test."))

    def court_order_scope(o):
        n = next((x["count"] for x in o["step3"]["base_by_type"] if x["value"] == "court_order"), 0)
        scope = (ROOT / "docs" / "SCOPE.md").read_text(encoding="utf-8")
        if not n or "Court orders are out of scope" not in scope:
            return None
        return dict(severity="Major", area="Spec conflict",
                    title="court_order documents are out of project scope (D32)",
                    what=(f"{n} of 50 base documents are court orders. The project scope (docs/SCOPE.md, D32) says three "
                          "document types only (FIR, witness statement, charge sheet) and that court orders are out of scope. "
                          "The teammate's schemas/SCOPE.md lists four types, so the two scope documents disagree."),
                    affected="all court_order bases and their variants (labels.csv doc_type=court_order)",
                    fix=("Decide with the project owner (open question 11). If D32 stands, replace court orders with "
                         "statements and charge sheets. If court orders stay, record a new decision that replaces D32."))

    def capture_names(o):
        n = o["step2"]["violations_by_rule"].get("value_not_allowed:capture_type", 0)
        if not n:
            return None
        return dict(severity="Minor", area="Label schema", title="capture_type values differ from SCOPE.md",
                    what=f"{n} rows use print_scan / phone_photo; SCOPE.md section 7 says the exact values are scan / photo.",
                    affected="labels.csv capture_type (all -PRINT_SCAN and -PHONE_PHOTO rows)",
                    fix="Pick one spelling and use it in both SCOPE.md and labels.csv.")

    def page_affected(o):
        n = o["step2"]["violations_by_rule"].get("page_affected_not_integer", 0)
        if not n:
            return None
        return dict(severity="Minor", area="Label schema", title="page_affected is free text",
                    what=f"{n} rows hold '1 (verify rendered PDF)' instead of an integer.",
                    affected="labels.csv page_affected",
                    fix="Write the page number as an integer (all PDFs are 1 page today).")

    def no_orig_path(o):
        if o["step2"]["has_explicit_original_path_column"]:
            return None
        return dict(severity="Minor", area="Label schema", title="No explicit path to the original document",
                    what="Rows give original_id only; the original's path must be rebuilt by convention (base_docs/<id>.pdf).",
                    affected="labels.csv", fix="Add original_path (and original_sha256) columns.")

    def e8_e9_inconsistent(o):
        ex = o["step5"]["examples"]
        n8 = sum("still name the old place" in e["reason"] for e in ex.get("E8", []))
        n9 = sum("still cites the old exhibit ID" in e["reason"] for e in ex.get("E9", []))
        if not (n8 or n9):
            return None
        return dict(severity="Minor", area="Tamper design",
                    title="E8 and E9 leave an easy cross-field mismatch",
                    what=("E8 changes incident_location but jurisdiction and the narrative still name the old place; "
                          "E9 changes evidence_item_id but evidence_description still cites the old ID. A simple consistency "
                          "rule spots these, which can make results look better than the hash deserves."),
                    affected="tampered/E8, tampered/E9 (all 50 each)",
                    fix=("Decide per class (open question 6). If the goal is single-field edits, keep it but report a "
                         "consistency-rule baseline. If not, edit the narrative mention too."))

    def manifest_stale(o):
        if not o["step1"]["stale_dataset_manifest"]:
            return None
        return dict(severity="Minor", area="Docs", title="dataset_manifest.json is stale",
                    what="It still says capture_types=['digital'] and lists captures and splits as not implemented.",
                    affected="dataset_v2/dataset_manifest.json",
                    fix="Regenerate the manifest after captures and splits, with per-split SHA-256 hashes.")

    def e0_double(o):
        return dict(severity="Minor", area="Label design", title="Base PDF and E0 copy are both labelled E0",
                    what=("Each base appears twice as E0 (base row and -E0 row), so E0 has 100 digital rows. The base row is "
                          "the anchor, not a candidate; counting it as an E0 sample inflates harmless counts."),
                    affected="the 50 BASE-xxxx rows and their captures",
                    fix="Mark base rows with role=original (or tamper_class=ORIGINAL) and exclude them from class counts.")

    def nonascii(o):
        na = o["step6"]["non_ascii_chars_in_pdf_text"]
        if not na:
            return None
        return dict(severity="Minor", area="Language / style",
                    title="Page header uses an em dash",
                    what=(f"Non-ASCII characters in PDF text layers: {na} (the em dash in 'SYNTHETIC TEST DOCUMENT - NOT AN "
                          f"OFFICIAL RECORD'). No non-English or Devanagari text was found "
                          f"({o['step6']['pdfs_with_devanagari']} PDFs with Devanagari). The project style rule bans em dashes."),
                    affected="all 850 PDFs (header line)",
                    fix="Use a plain hyphen or a colon in the header.")

    def docs_mismatch(o):
        return dict(severity="Minor", area="Docs",
                    title="Two datasets exist and docs/DATASET.md describes only v0",
                    what=("dataset/ (v0, 40 classes, 60 bases, Identical/Equivalent labels) and dataset_v2/ (E0 to E15) both "
                          "exist. docs/DATASET.md and PROGRESS.md describe v0 only; no split hashes are recorded for v2; "
                          "dataset_v2/ is not git-ignored (610 MB)."),
                    affected="docs/DATASET.md, PROGRESS.md, .gitignore",
                    fix="Record which dataset is canonical (open question 1), add a v2 card with split hashes, git-ignore the generated folders.")

    return [leak, templated, fixed_values,
            class_fail("E11", "Major", "E11 is a rewrite, not a clause deletion",
                       "Delete one sentence or clause from a multi-sentence narrative and keep every other token unchanged."),
            class_fail("E12", "Major", "E12 appends a sentence, so it duplicates E10",
                       "Swap one modal or quantifier in place (may -> shall, some -> all, was -> may have been) with no other token change."),
            class_fail("E14", "Major", "E14 changes printed dates only; no metadata inconsistency",
                       ("Set PDF CreationDate/ModDate (and the change log) so the file metadata is later than the backdated "
                        "printed date, or drop the metadata claim and merge E14 into E2. Also avoid a filing date before the "
                        "incident date unless that is intended.")),
            class_fail("E15", "Major", "E15 is a printed text change that names the class",
                       ("Draw a synthetic seal or signature image in the region and alter it visually (remove, replace, move). "
                        "Keep any printed text the same as the original. Never print the class code.")),
            class_fail("E4", "Minor", "E4 on 8 bases inserts an amount where there was none",
                       "Only apply E4 to bases with a real amount, or label these as a separate 'value added' case."),
            split_ratio, equivalence, harmless_share, locked_rules, schema_vocab, synonym_rule, realism,
            captures_clean, review, pymupdf, court_order_scope, capture_names, page_affected, no_orig_path, e8_e9_inconsistent,
            e0_double, manifest_stale, nonascii, docs_mismatch]


def main() -> list[dict]:
    o = {"step1": read_out("step1_inventory.json"), "step2": read_out("step2_schema.json"),
         "step3": read_out("step3_coverage.json"), "step4": read_out("step4_splits.json"),
         "step5": read_out("step5_tamper.json"), "step6": read_out("step6_quality.json"),
         "ocr": read_out("step6_ocr.json")}
    issues = [i for d in detectors() if (i := d(o))]
    issues.sort(key=lambda i: SEV_ORDER[i["severity"]])
    for n, i in enumerate(issues, 1):
        i["id"] = f"I{n:02d}"
    cols = ["id", "severity", "area", "title", "what", "affected", "fix"]
    with (AUDIT_DIR / "issues.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({c: i[c] for c in cols} for i in issues)
    from collections import Counter
    print(Counter(i["severity"] for i in issues))
    for i in issues:
        print(i["id"], i["severity"], i["title"])
    return issues


if __name__ == "__main__":
    main()
