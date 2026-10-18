# Tampering Definition

Phase 1 deliverable, updated on 16 October 2026 to the decisions locked before Phase 2 (D39 to D56 in `DECISIONS.md`).

This document defines what Pramaan DMS calls tampering. It is the reference for the field check (Phase 7), the verify API (Phase 8), the final verdict logic (Phase 15), the QR-sealed copy check (Phase 23) and the paper. English documents only.

## Terms used

| Term | Meaning |
|---|---|
| **Original** | The document version sealed at intake. It has a stored SHA-256 (S) and a signed fingerprint record (F, N, V). |
| **Candidate** | Any file checked against the original: a PDF, a scan, or a phone photo. |
| **Content** | What the document says and shows: the values of its fields, the words of its narrative, its stamps and signatures, and its pages. |
| **Format or capture** | How the content is stored or captured: file type, metadata, resolution, font, letter case, layout reflow, spacing between words and lines, the standard way a value is written (for example `12/03/2026` or `12 March 2026`), scan or photo noise, lighting, tilt, compression. |
| **Critical field** | A field marked "Critical: yes" in `CRITICAL_FIELDS.md` (for example FIR number, dates, names, law sections, amounts). |
| **Narrative entity** | A date, time, name, number, amount, vehicle number or law section number written inside the narrative. Each one gets an exact fingerprint, like a field. |
| **Narrative** | The free text of the document, apart from its narrative entities. It is compared by meaning with the learned narrative hash (N). |
| **Visual region** | A stamp, seal or signature area on a page. |
| **Unsealed annotation** | A handwritten note, mark or initials added to a copy with no stamp or seal. |
| **Clear change** | A change found where both the original value and the candidate value were read with confidence at or above the threshold. |
| **Could not verify** | A critical field or narrative entity in the candidate that was read with confidence below the threshold (for example blurred, folded or cut off). |
| **c_min, t_N, t_V** | Thresholds: minimum OCR confidence, maximum Hamming distance for a narrative chunk, maximum Hamming distance for a visual region. All are chosen on the validation set only. |

## 1. The four verdicts

| Verdict | Exact definition |
|---|---|
| **Identical** | The SHA-256 of the candidate file bytes equals the stored SHA-256 of the original version. |
| **Equivalent (Format)** | Not Identical, no clear change, and every critical field and narrative entity was read with confidence at or above c_min. Only format or capture differs. |
| **Tampered** | At least one clear change was found. Every Tampered verdict has a severity (Major or Minor) and a list of changes, each with its page and location. Any fields that could not be read are listed beside it as "could not verify". |
| **Inconclusive** | No clear change was found, and at least one critical field or narrative entity could not be read (below c_min). The verdict lists those fields as "could not verify" and the case goes to human review. |

A candidate that is a **redacted copy** (parts blacked out or masked) is not supported in v1. Verification stops with the message "Redacted copies are not supported in this version. Verify against an unredacted copy." No verdict is given.

A **change** is any one of these:

- **Field change:** a field's fingerprint differs from the original, a field in the original is missing from the candidate, or the candidate has an extra field value.
- **Narrative entity change:** a narrative entity's fingerprint differs, or an entity is missing or extra.
- **Narrative change:** an aligned narrative chunk has a Hamming distance above t_N, or a chunk is missing or extra after alignment.
- **Visual change:** a stamp, seal or signature region is missing, extra, or has a Hamming distance above t_V.
- **Page change:** a page was added, removed or moved to a different position.
- **Annotation:** an unsealed annotation was added.

## 2. Severity for Tampered

The rule is applied to the full list of clear changes:

> **Major** if at least one change is any of:
> - a change to a critical field, including a value added or removed (for example a law section added or removed, or an extra accused)
> - a change to a narrative entity (a date, time, name, number, amount, vehicle number or section number inside the narrative)
> - a negation flip in the narrative (for example "did" to "did not")
> - a page added, removed or reordered
> - a stamp, seal or signature removed, added or swapped
> - an unsealed annotation that overlaps a critical field
>
> **Minor** in every other case, which covers:
> - narrative wording or punctuation changes that touch no narrative entity and flip no negation
> - a sentence added or removed that contains no narrative entity
> - a change in the order of names in a list
> - a change to a non-critical field (complainant address)
> - an unsealed annotation outside any critical field. It is also flagged so a person sees it.

Notes:

- **Name order.** Changing only the order of names in a list (for example accused 1 and 2 swapped) is Minor. A name changed, added or removed is Major.
- **Law sections** are compared as a set. The order they are listed in is format. A section added, removed or replaced is Major.
- **Honorifics** (Shri, Smt and similar) are removed before matching, so adding or removing one is format. The raw text is still stored.
- **Spacing.** Spacing between words and lines, and the standard separators of a value type, are format. A space that splits or merges a value inside an ID, number or date is content (see `CRITICAL_FIELDS.md` section 3, spacing rule). For example `ZZ 01 AB 1234` and `ZZ01AB1234` are the same, but `142/2026` and `14 2/2026` are not.

## 3. The key principle: Equivalent means only capture or format differs

**Equivalent** means the content is the same and only the way it was stored or captured is different. **Any change to content is Tampered.** This includes a reworded sentence that seems to keep the same meaning.

Why this matters for legal documents:

1. **Exact words carry legal weight.** A witness statement records what a person said. "I saw him take the bag" and "I think he took the bag" may look close in meaning, but they say different things about what the witness saw and how sure they are. A system that calls a reworded statement "the same" would hide exactly the change that matters.
2. **"Same meaning" is a judgement, not a measurement.** Deciding whether two wordings mean the same needs a person who knows the case. A model that decides this would make legal judgements silently.
3. **A meaning test is easy to attack.** If small "same meaning" edits were accepted, an insider could make edits that slip under a threshold. A strict content rule removes that room.
4. **Format changes are not a risk.** A rescan, a photo or a reprint in another font does not change what the document says. Flagging these as tampered, as SHA-256 does, creates false alarms and teaches users to ignore alerts.

So the system is lenient on format and strict on content. Severity says how much attention a change needs. It never decides whether the change "matters" legally; that stays with the officer or the court.

## 4. Decision rules, in order

These match `LEGAL_HASH_SPEC.md` section 9.

```
R1. If SHA-256(candidate) == S:                               return Identical
R2. If the candidate is a redacted copy:                      stop with the "not supported" message
R3. Run the Legal Hash pipeline on the candidate
    (preprocess, OCR, fields, narrative entities, normalization, F, N, V, pages)
R4. unreadable = critical fields and narrative entities below c_min
R5. changes    = clear field, entity, narrative, visual, page and annotation changes
R6. If changes is not empty:  return Tampered(severity(changes), changes, could_not_verify = unreadable)
R7. If unreadable is not empty: return Inconclusive(could_not_verify = unreadable)
R8.                                                           return Equivalent
```

A clear edit always wins over unreadable fields (R6 before R7). An unreadable field never hides a clear edit somewhere else.

Every verdict record stores: the verdict, the change list, the "could not verify" list, the confidences, the thresholds, the model version, the OCR engine and version, the normalization rules version, the code version (git commit) and the time. A stored verdict can be re-run and must give the same answer.

## 5. Who sees what

| Viewer | Sees |
|---|---|
| Authenticated staff with access to the case | Verdict, severity, every change with field name, page, location, and old and new values, plus the "could not verify" list |
| Public verifier (QR verify page, no login) | One fixed message only. No field names, no values, no locations. See `REQUIREMENTS.md` FR-PUB rows for the exact messages |

## 6. Worked examples

"Critical field" refers to the list in `CRITICAL_FIELDS.md`. Dates are DD/MM/YYYY unless written out. Section numbers are example values only, not claims about what each section covers.

| # | What changed | Example (before -> after) | Verdict | Severity | Why |
|---|---|---|---|---|---|
| 1 | Nothing. Exact same file | `FIR_0142.pdf` -> same bytes | Identical | n/a | SHA-256 matches (R1). |
| 2 | Rescan of the same paper | 300 dpi scan -> new 200 dpi scan, slightly skewed | Equivalent | n/a | Content matches after OCR and normalization. Only capture differs. |
| 3 | Phone photo, tilted, low light | Flat scan -> phone photo at 20 degrees in dim light | Equivalent | n/a | Everything is read above c_min and matches. If a critical field is unreadable and nothing else changed, the verdict is Inconclusive instead (see #38). |
| 4 | Reprint with a different font | Times New Roman -> Helvetica, same text | Equivalent | n/a | Font is format. |
| 5 | PDF metadata only | PDF "Author" and "ModDate" changed, page content same | Equivalent | n/a | Content unchanged. The metadata difference is recorded as a note in the forensic report. |
| 6 | Date written with or without leading zeros | `5/3/2026` -> `05/03/2026` | Equivalent | n/a | Both normalize to `2026-03-05`. |
| 7 | Indian vs plain number format | `Rs 5,00,000/-` -> `Rs. 500000` | Equivalent | n/a | Both normalize to `500000`. |
| 8 | Date written in another format | `12/03/2026` -> `12 March 2026` | Equivalent | n/a | Both normalize to `2026-03-12`. |
| 9 | Honorific added | `Ramesh Kumar` -> `Shri Ramesh Kumar` | Equivalent | n/a | Honorifics are removed before matching. The raw text is stored. |
| 10 | Section reference written another way | `u/s 303(2) BNS` -> `Section 303 (2) of BNS` | Equivalent | n/a | Both normalize to `BNS:303(2)`. |
| 11 | Name case and spacing between words | `RAMESH  KUMAR` -> `Ramesh Kumar` | Equivalent | n/a | Whitespace collapse and case fold give the same value. |
| 12 | Reflowed layout, wider line spacing | Narrative wraps at 80 characters -> 60 characters, 1.5 line spacing | Equivalent | n/a | Spacing between words and lines is format. |
| 13 | Standard grouping inside a vehicle number | `ZZ 01 AB 1234` -> `ZZ-01-AB-1234` | Equivalent | n/a | Spaces and hyphens between the standard groups of a vehicle number are format. |
| 14 | Law sections listed in another order | `303(2), 3(5) BNS` -> `3(5), 303(2) BNS` | Equivalent | n/a | Sections compare as a set. |
| 15 | OCR noise in the narrative | `the complainant` -> OCR reads `tbe cornplainant` | Equivalent | n/a | The narrative hash ignores OCR noise. No narrative entity is involved. |
| 16 | Date changed by one day | Date of incident `12/03/2026` -> `13/03/2026` | Tampered | Major | Critical field changed. A learned hash alone could miss this, which is why F exists. |
| 17 | Time changed | Time of incident `14:30` -> `16:30` | Tampered | Major | Critical field changed. |
| 18 | Amount changed by one digit | Property value `Rs 45,000` -> `Rs 48,000` | Tampered | Major | Critical field changed. |
| 19 | Accused name changed | Accused `Suresh Yadav` -> `Mahesh Yadav` | Tampered | Major | Critical field changed. |
| 20 | Extra accused added | Accused: `A1` -> `A1, A2` | Tampered | Major | Value added to a critical field. |
| 21 | Law section replaced | `BNS:303(2)` -> `BNS:305` | Tampered | Major | Section set changed. |
| 22 | Law section added | `BNS:303(2)` -> `BNS:303(2), BNS:3(5)` | Tampered | Major | Section added. |
| 23 | Vehicle number, one character | `ZZ01AB1234` -> `ZZ01AB1284` | Tampered | Major | Critical field changed. |
| 24 | Space inserted inside an ID | FIR No. `142/2026` -> `14 2/2026` | Tampered | Major | A space that splits a value inside an ID is content. |
| 25 | Order of accused names swapped | `1. A, 2. B` -> `1. B, 2. A` | Tampered | Minor | Name order only (D44). |
| 26 | Complainant address changed | `House No. 12` -> `House No. 21` | Tampered | Minor | Non-critical field. |
| 27 | One word swapped in the narrative | "a **red** car" -> "a **blue** car" | Tampered | Minor | Narrative wording. No entity, no negation. |
| 28 | Negation added | "the accused **did** threaten me" -> "the accused **did not** threaten me" | Tampered | Major | Negation flip (D42). |
| 29 | Date changed inside the narrative only | "On 12/03/2026 at about 14:30 ..." -> "On 13/03/2026 at about 14:30 ..." | Tampered | Major | Narrative entity changed (D45). |
| 30 | Name changed inside the narrative only | "...saw Suresh Yadav near my house" -> "...saw Mahesh Yadav near my house" | Tampered | Major | Narrative entity changed. |
| 31 | Sentence added with no entity | "The street lights were working." added | Tampered | Minor | Narrative change only. |
| 32 | Sentence added with an entity | "He also took Rs 5,000 from my pocket." added | Tampered | Major | A narrative entity (amount) was added. |
| 33 | Sentence removed with no entity | "My family is very afraid." removed | Tampered | Minor | Narrative change only. |
| 34 | Same meaning, reworded sentence | "I saw him take the bag." -> "I watched as he took the bag." | Tampered | Minor | Wording is content. Equivalent covers format only. |
| 35 | Punctuation only | "No, he ran away." -> "No he ran away." | Tampered | Minor | Punctuation is content. Detection is limited because OCR often misreads punctuation (open item E4). |
| 36 | Stamp removed | Police station seal on page 2 -> no seal | Tampered | Major | Visual region missing. |
| 37 | Stamp swapped | Seal of "PS Station A" -> seal of "PS Station B" | Tampered | Major | Visual region changed. |
| 38 | Signature swapped | Officer signature -> a different signature | Tampered | Major | Visual region changed. |
| 39 | Court receipt stamp added | A "RECEIVED" stamp added on page 1 | Tampered | Major | A stamp or seal added is a visual change. |
| 40 | Page added | 2-page statement -> 3 pages | Tampered | Major | Page change (D43). |
| 41 | Page removed | 3-page FIR -> pages 1 and 3 only | Tampered | Major | Page change. |
| 42 | Page order changed | Pages 1, 2, 3 -> 1, 3, 2 | Tampered | Major | Page change. |
| 43 | Handwritten note in a blank margin | Pen note "seen, ok" beside paragraph 2 | Tampered | Minor (flagged) | Unsealed annotation outside critical fields (D46). |
| 44 | Handwritten note over a critical field | Pen mark written across the date of incident | Tampered | Major | Unsealed annotation overlapping a critical field. If the date can no longer be read, it is also listed as "could not verify". |
| 45 | Homoglyph swap in a digital PDF | Name `Ramesh` with Latin `a` -> `Rаmesh` with Cyrillic `а` (U+0430) in the text layer | Tampered | Major | Normalization flags mixed script instead of fixing it. The field value no longer matches. |
| 46 | Zero-width character inserted | `ZZ01AB1234` -> `ZZ01AB` + U+200B + `1234` in a PDF text layer | Equivalent (with warning) | n/a | Zero-width characters are removed in normalization. A warning is raised because this is a known attack pattern (open item E10). |
| 47 | Critical field too blurry, nothing else changed | Date of report blurred, OCR confidence 0.41 (c_min, say, 0.80) | Inconclusive | n/a | R7. The date of report is listed as "could not verify". |
| 48 | One field blurred, another clearly edited | Date of report blurred; property value `Rs 45,000` -> `Rs 48,000` | Tampered | Major | R6: the clear edit wins. Date of report listed as "could not verify" (D41). |
| 49 | Pen edit over a printed digit | Amount `45,000` overwritten by pen to look like `46,000` | Tampered | Major | Critical field read differently. If OCR is unsure, the field is "could not verify" and, with no other change, the verdict is Inconclusive. |
| 50 | QR copied onto a different document | Valid QR from FIR 0142 pasted onto a printout of FIR 0157 | Tampered | Major | The verify page checks content against the record named in the QR, not only the QR signature. |
| 51 | Redacted copy | Victim name blacked out | No verdict | n/a | R2: not supported in v1. Verification stops with the "not supported" message (D47). |

Count: 51 examples.

## 7. Edge cases and open questions

Status as of 16 October 2026.

| # | Topic | Status |
|---|---|---|
| E1 | Unreadable field could hide a clear edit | **Resolved (D41).** A clear edit wins (R6). Unreadable fields are listed as "could not verify". |
| E2 | Missing vs unreadable field (photo cut off part of the page) | **Open.** Draft: a field whose region was not captured counts as "could not verify", not as removed. Needs page alignment (Phase 14). |
| E3 | Spacing | **Resolved (D40).** Spacing between words and lines is format. Spacing that splits or merges a value inside an ID, number or date is content. |
| E4 | Punctuation | **Open (detection only).** Punctuation is content (Minor). How reliably it is detected will be measured and reported. |
| E5 | Negation and narrative entities | **Resolved (D42, D45).** Negation flips are Major. Narrative entities get exact fingerprints; a change is Major. |
| E6 | Page added or removed | **Resolved (D43).** Major. |
| E7 | Page order | **Resolved (D43).** Major. |
| E8 | Annotations | **Resolved (D46).** Unsealed annotations outside critical fields are Minor and flagged; overlapping a critical field is Major. Added stamps or seals are visual changes (Major). |
| E9 | Homoglyphs: PDF text layer vs OCR | **Open.** Decide whether verify reads the PDF text layer for born-digital PDFs or always OCRs the rendered page. Homoglyphs found in originals are flagged at intake. |
| E10 | Zero-width characters | **Open.** Draft: Equivalent with a warning. |
| E11 | PDF metadata | **Open.** Draft: Equivalent; differences noted in the forensic report. |
| E12 | Transliteration between scripts | **Not applicable.** English only (D39). |
| E13 | Ambiguous date order | **Open.** Draft: assume DD/MM; lower confidence if the document shows otherwise. |
| E14 | Lawful corrections | **Open.** Draft: a candidate is compared with the version named in the QR or chosen by the verifier. |
| E15 | Redacted copies | **Resolved (D47).** Not supported in v1; fail with a clear message. |
| E16 | Blank pages added by a scanner | **Open.** Draft: pages with no text and no regions are ignored and do not count as a page change. |
| E17 | Repeated field values | **Resolved by D45.** Header values are fields; mentions in the narrative are narrative entities. |
| E18 | Visual false alarms on photos | **Open.** Decide after Phase 14 numbers are known. |
