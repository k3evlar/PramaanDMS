# TAMPERING_DEFINITION.md — Tampering Classes E0–E15

## 1. Purpose and labeling principle

This file defines the dataset's tampering classes. A sample must be assigned one primary class only. Record every affected field or region in `field_changed` and the detailed change log.

- `E0` is the benign/no-tamper control class. It is not one of the 15 tampering classes.
- `E1`–`E15` are the primary tampering classes.
- Do not assign multiple primary classes to one sample. If multiple independent edits are present, regenerate the sample with one controlled edit or treat it as a separately designed multi-edit evaluation outside the single-class benchmark.
- The class is based on the operation performed, not only on the observed text difference.
- `expected_verdict` is the expected system decision, not a claim about legal guilt or legal validity.

## 2. Class definitions

| ID | Class | Fields / regions hit | Example | Default expected verdict |
|---|---|---|---|---|
| E0 | Benign control | No semantic field change; cosmetic/layout regions | Spacing, reformatting, or meaning-preserving synonym substitution | `Valid` |
| E1 | Name substitution | `complainant_name`, `accused_name`, `victim_name`, `witness_name`, `investigating_officer`, `advocate_name` | “Ravi Kumar” becomes “Ravi Sharma” | `Tampered` |
| E2 | Date alteration | `filing_date`, `document_date`, `incident_date`, `seizure_date`, `next_hearing_date` | Incident date changes from 12 March to 21 March | `Tampered` |
| E3 | Time alteration | `incident_time` | 11:40 PM becomes 11:40 AM | `Tampered` |
| E4 | Amount or number change | `monetary_amount` | Rs 5,00,000 becomes Rs 50,000 | `Tampered` |
| E5 | Legal provision change | `act_name`, `section_number` | Section 302 becomes Section 304 | `Tampered` |
| E6 | Negation flip | `offence_description`, `evidence_description` | “was present” becomes “was not present” | `Tampered` |
| E7 | Role reversal | `complainant_name`, `accused_name` and their role assignments | Complainant and accused are swapped | `Tampered` |
| E8 | Location change | `incident_location`, `police_station`, `jurisdiction` | Incident location changes to another area | `Tampered` |
| E9 | Evidence ID or description edit | `evidence_item_id`, `evidence_description` | Exhibit A-14 becomes A-41 | `Tampered` |
| E10 | Clause insertion | `offence_description`, `evidence_description` | A new incriminating or exculpatory sentence is added | `Tampered` |
| E11 | Clause deletion | `offence_description`, `evidence_description` | A key sentence is silently removed | `Tampered` |
| E12 | Modal or quantifier shift | `offence_description` | “may” becomes “shall”; “some” becomes “all” | `Tampered` |
| E13 | Custody chain edit | `custody_holder`, `seizure_date` and related custody annotation | Custodian changes or a transfer entry is removed | `Tampered` |
| E14 | Backdating | `filing_date`, `document_date`, plus file metadata | Printed date and file timestamps disagree in a way that indicates backdating | `Tampered` when evidence is clear |
| E15 | Signature or seal tampering | `signature_region`, `seal_region`, signatory annotation | Signature is removed or replaced, or seal is altered | `Tampered` when alteration is clear |

## 3. Verdict and severity rules

### Expected verdict
- `Valid`: E0 samples whose meaning is unchanged and whose content remains sufficiently readable.
- `Tampered`: E1–E13, E14, or E15 when the intended material alteration is clearly observable and labelable.
- `Inconclusive`: the relevant evidence cannot be reliably adjudicated, for example because the only potentially affected content is obscured or unreadable and the protocol requires abstention.

Do not make every blurred or redacted sample automatically `Inconclusive`. Apply the actual test condition: a blurred sample with a clear, independently readable edit can remain `Tampered`; a blurred sample with no discernible edit may be `Inconclusive` if the system cannot reliably verify it. Record the reason.

### Severity
Use the four severity values specified by the dataset task:
- `Minor`: a meaningful but comparatively limited alteration under the project's documented impact rubric.
- `Major`: a change with material implications for identity, date/time, legal provision, roles, location, amount, evidence, custody, or operative meaning.
- `Format`: a cosmetic change that preserves meaning, normally used for E0 formatting controls.
- `None`: untouched reference copy.

Severity must not be inferred solely from visual size or OCR confidence. Document subjective decisions in the change log and review them.

## 4. Class-specific implementation notes

### E0 — Benign control
Include both untouched copies and controlled cosmetic changes. Examples: whitespace, font, line wrapping, page layout, or meaning-preserving synonym changes. A synonym is benign only after a reviewer confirms that the legal/evidentiary meaning is unchanged. Keep the untouched/benign samples at approximately one-third of the total dataset.

### E1 — Name substitution
Change one identity-bearing name and keep all other fields unchanged. Record the exact original and replacement strings. Avoid accidentally changing unrelated names in the same document.

### E2 — Date alteration
Change one date field per sample. Do not confuse E2 with E14: E2 changes a date value; E14 specifically tests a backdating pattern involving date text and metadata.

### E3 — Time alteration
Change `incident_time` only, unless the official schema is versioned. Ensure AM/PM flips are unambiguous.

### E4 — Amount or number change
Change `monetary_amount`. If a future scope expands this class to non-monetary numbers, update the definition and field mapping before labeling.

### E5 — Legal provision change
Change `act_name` or `section_number`. Keep the sample synthetic and do not imply that the changed provision is legally correct for a real case.

### E6 — Negation flip
Change the presence/absence of negation in a sentence within `offence_description` or `evidence_description`. Verify that the meaning changes materially.

### E7 — Role reversal
Swap complainant and accused roles, not merely the order in which names are printed. Ensure the label records both affected fields and the role assignment.

### E8 — Location change
Change one location/jurisdiction-related value. If multiple linked fields must change for the example to remain internally coherent, record all affected fields but keep the operation focused on location change.

### E9 — Evidence ID or description edit
Change an evidence identifier or its description. Keep the edit focused on the evidence reference.

### E10 — Clause insertion
Insert one meaningful sentence into `offence_description` or `evidence_description`. Record the inserted text and its location.

### E11 — Clause deletion
Remove one meaningful sentence from `offence_description` or `evidence_description`. Preserve the original text in the change log.

### E12 — Modal or quantifier shift
Change one modal or quantifier that alters certainty, obligation, scope, or quantity. A reviewer must confirm that the change is meaning-relevant rather than stylistic.

### E13 — Custody chain edit
Alter `custody_holder`, `seizure_date`, or a clearly annotated custody-transfer entry. If the transfer history is not represented in the canonical 27 fields, retain it in the document text and change log.

### E14 — Backdating
Construct a controlled inconsistency between the date printed in the document and associated file metadata. Preserve the pre-edit and post-edit metadata in the change log. Do not rely on filesystem timestamps alone as proof; record the exact metadata field changed and the test assumption.

### E15 — Signature or seal tampering
Alter a signature or seal region in a controlled synthetic artifact. Annotate `signature_region` or `seal_region` and the affected page. Never use or imitate a real person's signature, a real official seal, or a real institution's authentication mark. Use clearly fictional marks.

## 5. Annotation requirements

For every sample, record:
- `sample_id`
- `original_id`
- `tamper_class`
- `field_changed` (canonical field names; for E15, include region annotation)
- `page_affected`
- `severity`
- `expected_verdict`
- `capture_type`

In the detailed change log, also record:
- operation description
- original value/text
- modified value/text
- reason for label
- metadata change for E14, where applicable
- reviewer status and any adjudication notes

## 6. Reviewer decision rule

If the class, affected field, or expected verdict is ambiguous, do not guess. Mark the sample as needing review, resolve the ambiguity using this definition, and only then include it in the final labeled dataset. A missing sample is preferable to a confidently incorrect label.
