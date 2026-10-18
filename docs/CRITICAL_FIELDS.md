# Critical Fields

Phase 1 deliverable, updated on 16 October 2026 to the decisions locked before Phase 2 (`DECISIONS.md` D39 to D56). English documents only.

This list drives field extraction and normalization (Phase 7), the field tagger (Phase 13) and the backdating rules (scheduled at the end of the build). A change to a field marked **Critical: yes** makes a Tampered verdict Major (see `TAMPERING_DEFINITION.md` section 2).

## 1. Field table

Types: `date`, `time`, `number`, `name`, `place`, `section`, `id`, `text`.

Found in: **F** = FIR, **S** = witness statement, **C** = charge sheet.

| # | Field | Type | Critical? | Found in | Label examples | Normalization rule |
|---|---|---|---|---|---|---|
| 1 | FIR number (with year) | id | yes | F, S, C | "FIR No.", "F.I.R. No.", "Crime No." | ID rule. Store as `NUMBER/YEAR`, leading zeros removed. |
| 2 | Police station | place | yes | F, S, C | "Police Station", "P.S." | Place rule. |
| 3 | District | place | yes | F, S, C | "District", "Dist." | Place rule. |
| 4 | Date of report (information received at police station) | date | yes | F, C | "Date of report", "Information received at P.S. Date", "FIR date" | Date rule. |
| 5 | Time of report | time | yes | F | "Time", "Information received at P.S. Time" | Time rule. |
| 6 | Date of incident | date | yes | F, S, C | "Date of occurrence", "Date of incident" | Date rule. A date range (from, to) is stored as two values. |
| 7 | Time of incident | time | yes | F, S | "Time of occurrence" | Time rule. A time range is stored as two values. |
| 8 | Place of incident | place | yes | F, S, C | "Place of occurrence", "Place of incident" | Place rule. |
| 9 | Complainant or informant name | name | yes | F, C | "Complainant", "Informant", "Name" | Name rule. |
| 10 | Father's or husband's name of complainant | name | yes | F | "Father's/Husband's name", "S/o", "D/o", "W/o" | Name rule. Relation markers (S/o, D/o, W/o) stored as a separate tag. |
| 11 | Accused name(s) | name | yes | F, S, C | "Accused", "Name of accused" | Name rule. List compared as a multiset; order changes are Minor (section 4). |
| 12 | Father's or husband's name of accused | name | yes | F, C | "Father's/Husband's name", "S/o" | Name rule. Kept paired with its accused. |
| 13 | Age of accused | number | yes | F, C | "Age" | Number rule. Integer years. |
| 14 | Victim name(s) | name | yes | F, C | "Victim", "Name of victim" | Name rule. List compared as a multiset; order changes are Minor. |
| 15 | Witness name(s) | name | yes | S, C | "Witness", "List of witnesses", "Name of witness" | Name rule. List compared as a multiset; order changes are Minor. In a statement, the person making the statement is witness 1. |
| 16 | Law sections cited | section | yes | F, C | "Sections", "Acts and Sections", "u/s" | Section rule. Compared as a set: order is format, a section added, removed or replaced is Major. |
| 17 | Property or amount values | number | yes | F, C | "Value of property", "Amount", "Rs." | Number rule. Canonical integer rupees. |
| 18 | Vehicle numbers | id | yes | F, S, C | "Vehicle No.", "Registration No." | ID rule. |
| 19 | Phone numbers | id | yes | F, S | "Mobile No.", "Phone" | Phone rule. |
| 20 | Officer name | name | yes | F, S, C | "Name of officer", "Recorded by", "Investigating Officer" | Name rule. |
| 21 | Officer rank | text | yes | F, S, C | "Rank", "Designation" (SI, ASI, Inspector) | Rank rule. |
| 22 | Officer ID | id | yes | F, S, C | "ID No.", "Belt No." | ID rule. |
| 23 | Date of statement | date | yes | S | "Date of statement", "Statement recorded on" | Date rule. |
| 24 | Charge sheet number and date | id + date | yes | C | "Charge sheet No.", "Final report No.", "Date" | ID rule for the number, date rule for the date. |
| 25 | Court name | place | yes | C | "In the court of", "Court" | Place rule. |
| 26 | Complainant address | place | no | F | "Address" | Place rule. Fingerprinted, but a change is Minor. |
| 27 | Narrative (complaint text, statement body, brief facts) | text | see section 2 | F, S, C | "Brief facts", "Statement", "Contents of complaint" | Narrative entities are fingerprinted exactly (section 2). The rest is hashed by the narrative hash N (`LEGAL_HASH_SPEC.md` section 7). |
| 28 | Property items (description, colour, quantity) | text | yes | F, C | "Property involved", "Property seized", "Particulars of property" | Text rule: whitespace collapse and case fold. List compared as a multiset; a description changed, added or removed is Major. |
| 29 | Exhibit IDs of seized property | id | yes | C | "Exhibit No.", "M.R. No.", "Property seized" | ID rule. Kept paired with its property item. |
| 30 | Date of seizure | date | yes | C | "Date of seizure", "Seized on" | Date rule. |
| 31 | Chain of custody (holder and date of each entry) | name + date | yes | C | "Chain of custody", "Deposited with", "Malkhana" | Name rule for the holder, date rule for the date; entries kept in order. An entry changed, added or removed is Major. |

Officer name and rank were one item in the first draft of `LEGAL_HASH_SPEC.md` section 4. They are split because they have different types and normalization rules. Rows 5, 10, 12, 13, 23, 24, 25 and 26 were added in Phase 1 (D21). Rows 28 to 31 (evidence and custody) were added for FIR-Tamper v3 Stage 2 (D96), so that evidence and custody edits (E9, E13) are critical changes.

## 2. Narrative entities

Dates, names, numbers, amounts and section numbers inside the narrative get exact fingerprints, just like fields (D45). Times and vehicle numbers count as numbers. The rest of the narrative stays semantic (compared by the narrative hash N).

| Entity type | Found by | Normalized with | Example |
|---|---|---|---|
| Date | Date patterns in the narrative text | Date rule | "On 12th March 2026" -> `2026-03-12` |
| Time | Time patterns | Time rule | "at about 2:30 PM" -> `14:30` |
| Name | Names that match a person field of the same document, plus the field tagger (Phase 13) | Name rule | "Shri Suresh Yadav" -> `suresh yadav` |
| Number or amount | Number and currency patterns | Number rule | "Rs 5,00,000" -> `500000` |
| Vehicle number | Vehicle number pattern | ID rule | "ZZ 01 AB 1234" -> `ZZ01AB1234` |
| Section number | Section patterns ("u/s 303(2)", "Section 305 of BNS") | Section rule | "u/s 303(2) BNS" -> `BNS:303(2)` |

Entities are stored as an ordered list of (type, normalized value, sentence position). Comparison:

- an entity changed, added or removed: **Major**
- entities unchanged but the wording around them changed: compared by N; a change is **Minor** unless it is a negation flip (**Major**)

## 3. Normalization rules

These follow `LEGAL_HASH_SPEC.md` section 5. Steps that apply to **every** field and narrative entity, in this order:

1. Unicode NFC normalization.
2. Remove zero-width characters (U+200B, U+200C, U+200D, U+FEFF, U+2060) and raise a warning if any were found.
3. Detect mixed-script homoglyphs (for example a Cyrillic letter inside a Latin word). **Flag, do not fix.**
4. Collapse runs of whitespace between words to one space. Trim both ends.

**Spacing rule (D40).** Spacing between words and lines is format. Inside a value of type id, number, date or time, only the standard separators listed below are format. Any other space that splits or merges a value is content. The normalizer applies the separator list for the field's type, and a value that has a space in any other position does not normalize to the original value.

| Type | Standard separators that are format |
|---|---|
| Vehicle number | A space or hyphen between the state code, district number, series letters and number (`ZZ 01 AB 1234`, `ZZ-01-AB-1234`, `ZZ01AB1234`) |
| Phone number | A space after `+91`, and one space between the 5-digit groups (`+91 10879 32910`) |
| Amount | Indian or international digit-group commas, `Rs`, `Rs.`, `/-`, `.00`, and the words lakh or crore when the number is clear |
| Date | The separators of the supported date formats (`/`, `-`, `.`, or spaces between day, month name and year) |
| Time | The separators of the supported time formats (`:`, `.`, a space before AM, PM or hrs) |
| FIR, charge sheet and officer ID numbers | None inside the number. Only the `/` before the year |

Then the rule for the value's type:

| Type | Rule | Example (input -> normalized) |
|---|---|---|
| **date** | Parse DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, "12 March 2026", "12th Mar 2026". Assume day before month. Output ISO `YYYY-MM-DD`. Two-digit years and unclear formats lower the confidence. | `05-03-2026` -> `2026-03-05` |
| **time** | Parse 24-hour and 12-hour forms, "hrs", "AM/PM". Output `HH:MM` in 24-hour form. | `2:30 PM` -> `14:30`; `14.30 hrs` -> `14:30` |
| **number** | Remove currency marks (Rs, Rs., `/-`) and standard digit-group commas. Convert lakh and crore words when the number is clear ("5 lakh" -> 500000). Drop `.00`. Output a canonical integer. | `Rs 5,00,000/-` -> `500000` |
| **name** | Common steps, then case fold. Remove honorifics (Shri, Smt, Sri, Shrimati, Kumari, Mr, Mrs, Ms, Dr) for matching; the raw text, honorific included, is stored as well (D48). | `Shri RAMESH  KUMAR` -> `ramesh kumar` (raw text kept) |
| **place** | Same as name, without honorific removal. No synonym or abbreviation expansion in v1 (for example "Rd" is not expanded to "Road"). | `P.S.  Station A` -> `p.s. station a` |
| **section** | Find the act and section number in any written form. Map act names and abbreviations to a code (BNS, BNSS, BSA, IPC, CrPC and others listed in Phase 7). Output `ACT:NUMBER(SUB)(CLAUSE)`. A list of sections is stored as a sorted set. | `u/s 303(2) BNS` -> `BNS:303(2)`; `Section 303 (2) of BNS` -> `BNS:303(2)` |
| **id** | Uppercase Latin letters. Remove only the standard separators for that ID type. For FIR and charge sheet numbers, output `NUMBER/YEAR` with leading zeros removed from the number. | `ZZ-01-AB-1234` -> `ZZ01AB1234`; `FIR No. 0142/2026` -> `142/2026`; `14 2/2026` -> no match with `142/2026` |
| **id (phone)** | Remove the standard separators and a leading `+91`, `91` or `0` to give 10 digits. | `+91 10879 32910` -> `1087932910` |
| **text (rank)** | Map to a fixed list of rank codes. Unknown ranks are kept as written and lower the confidence. | `Sub-Inspector`, `SI` -> `SUB_INSPECTOR` |

After normalization, each field and each narrative entity is fingerprinted as `HMAC-SHA-256(k_field, name || ":" || normalized_value)` (`LEGAL_HASH_SPEC.md` section 6). The record also keeps the page and bounding box.

Every rule above must have unit tests in Phase 7, and every example in this section becomes a test case.

## 4. Comparison rules for lists

| List | Compared as | Order change | Value changed, added or removed |
|---|---|---|---|
| Law sections | Set | Format (not a change) | Major |
| Accused, victim and witness names | Multiset, with order kept for reporting | Minor (D44) | Major |
| Accused father's names and ages | Paired with their accused | Follows the accused | Major |
| Vehicle and phone numbers | Multiset | Minor | Major |

## 5. Decisions taken (formerly open questions)

| # | Question | Decision |
|---|---|---|
| Q1 | Honorifics: strip or keep? | Strip for matching, store raw text (D48). |
| Q2 | Does name order matter? | A name order change is Minor (D44). |
| Q3 | Does section order matter? | No. Sections compare as a set; added or removed is Major (D44). |
| Q4 | Fingerprint dates, numbers, names and sections inside the narrative? | Yes (D45). |
| Q5 | Is the complainant address critical? | No. A change is Minor. |
| Q6 | Labels in another language? | Not applicable. English only (D39). |
