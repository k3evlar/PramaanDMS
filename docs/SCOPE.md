# Scope

Phase 1 deliverable, updated on 16 October 2026 to the decisions locked before Phase 2 (`DECISIONS.md` D39 to D56).

## 1. Problem in plain words

Police and courts now keep FIRs, witness statements and charge sheets as digital files. Today the usual integrity check is a cryptographic hash such as SHA-256. That check is too strict: a rescan, a reprint or a phone photo of the same page gives a different hash, so an honest copy looks "changed". It also says too little: it can only say "different", not what changed or whether the change matters. Existing systems also rarely deal with insiders who have access and quietly edit a record. And an outside party, such as a court clerk holding a paper copy, usually cannot check that copy without getting the original file. Pramaan DMS stores these documents securely, keeps a chain of custody, detects real content changes while ignoring harmless format changes, explains what changed, and controls who can see what.

**Agreed scope source:** `PROJECT_BRIEF.md` is the agreed scope for this project (owner decision, D27). This section and the rest of this document follow it. Our reading of SIH26190 is:

- Store legal and investigation documents (FIRs, statements, charge sheets) securely
- Keep a reliable chain of custody
- Detect and explain tampering
- Control who can see what

## 2. Users and roles

Access is deny by default. Every staff user signs in with a password and TOTP. Access to documents is per case: a staff user sees a case only if they are a member of it.

| Role | What they do | What they can see | What they cannot see or do |
|---|---|---|---|
| **Investigating Officer (IO)** | Creates cases. Uploads documents to their own cases. Runs verification on copies. Requests QR-sealed copies and sensitive actions (for example archive). | Content, fingerprints, verdicts and custody history of documents in cases they are a member of. | Cases they are not a member of. Cannot approve their own requests. Cannot delete evidence. Cannot release a legal hold. |
| **Supervisor (SHO or senior officer)** | Oversees cases in their unit. Uploads documents. Approves sensitive actions as the second person. Places legal holds. The only role that issues QR-sealed copies (D50). | Content, verdicts and custody of cases they supervise. Pending approval requests. Backdating and tamper flags. | Cases outside their unit. Cannot approve a request they made. Cannot delete evidence. |
| **Court Clerk / Verifier** | Verifies copies brought to court. Verify only (D50). | Verdicts and full change details (field, location, old and new values) for cases shared with their court. | Cases not shared with their court. Cannot upload evidence, issue QR-sealed copies or change anything. |
| **Auditor** | Reviews the transparency log, custody history and inclusion and consistency proofs. Checks that the log has not been rewritten. | Log entries, custody events, signed tree heads, proofs, verdict metadata (verdict, time, actor, versions). | Document content, extracted field values, old and new values in a change list. |
| **System Admin** | Manages user accounts, role requests and system settings. Monitors health. | User list, role assignments, system health, configuration. | Document content and original files. Cannot grant a supervisor or admin role, change thresholds, or touch keys without a second approver. Cannot delete evidence or log entries. |
| **Public verifier (no login)** | Scans the QR on a QR-sealed copy, or uploads a photo, on the public verify page. | One fixed message per outcome, for example "A critical field was changed." (D51). | Field names, values, locations, narrative text, names, custody history. |

Notes:

- "QR-sealed copy" is the agreed term for a copy with a signed QR code (D53).
- Old and new values in a change list are shown only to authenticated staff who can already see the document content.

## 3. Document types in scope

| Type | Notes |
|---|---|
| First Information Report (FIR) | Main document for the demo. Has the most critical fields. |
| Witness statement | Mostly narrative text. Wording changes matter most here. |
| Charge sheet | Long document with sections, accused details and lists of witnesses. |

Only these three types are in scope. Other police documents (for example case diaries, seizure memos, medical reports) are out of scope (section 6).

## 4. Languages and input formats

- **Language:** English only (D39). Hindi is future work.
- **Text type:** typed or printed. A small handwritten edit made with a pen on a printed copy is in scope as a tampering case. Fully handwritten documents are not.
- **Input formats:**
  - PDF (born digital or scanned)
  - Scanned images (PNG, JPEG, TIFF)
  - Phone photos (JPEG, PNG)

## 5. In scope

Matches `PROJECT_BRIEF.md`.

**Legal Hash and verification**

- Legal Hash: field fingerprints (F), narrative hash (N), visual region hashes for stamps and signatures (V), plus SHA-256 (S)
- Four verdicts: Identical, Equivalent (Format), Tampered (Major or Minor), Inconclusive (see `TAMPERING_DEFINITION.md`)
- Change list for every Tampered verdict: what changed and where (page and box), plus a "could not verify" list for unreadable fields
- Redacted copies are rejected with a clear message (not supported in v1)
- Repeatable verdicts: each verdict stores model, OCR, rules and code versions

**Security layers**

1. Lock: Argon2id passwords, TOTP, roles, case-level access
2. Protect: AES-256-GCM per file, keys held in OpenBao (an open-source fork of HashiCorp Vault, D57)
3. Seal: Ed25519 signature and RFC 3161 trusted timestamp at intake
4. Track: Merkle transparency log of every action, signed tree heads published outside the system
5. Verify and investigate: Legal Hash verification, tamper window, backdating checks, forensic reports

**Demo features**

- QR-sealed copy: issued by a Supervisor, carries a QR with the signed fingerprint reference, checked on a public phone-friendly page that shows one fixed message
- Tamper window: the time range in which a change happened and who had access then
- Backdating checks: rule based (law anachronism, timeline sanity, timestamp evidence). In scope, scheduled at the end of the build (D52)
- Signed forensic PDF report
- Section 63 draft certificate, marked "Draft for officer review"
- Insider protection: admin cannot read evidence, two-person rule for risky actions, no hard delete

**Research outputs**

- FIR-Tamper dataset (synthetic English documents, real phone captures, equivalence traps, adversarial edits)
- Benchmark against SHA-256, ssdeep, TLSH, pHash, OCR text diff and plain embedding similarity, with published error rates
- Verify API with OpenAPI docs

## 6. Out of scope

From `PROJECT_BRIEF.md`:

| Item | Reason |
|---|---|
| Handwritten documents beyond basic | Handwritten OCR is not reliable enough on our hardware and data. |
| Languages other than English, including Hindi | English only (D39). Hindi is future work. Keeps the dataset, OCR testing and model training achievable for a student team. |
| Integration with real police systems (CCTNS, e-Sakshya, ICJS) | No access to these systems. We expose an API that such systems could call. |
| Any claim of legal admissibility or certification | Only a court can decide this. We generate drafts for officer review. |
| Production HSM | Not available to us. We simulate key custody with OpenBao in dev mode. |

Added in Phase 1:

| Item | Reason |
|---|---|
| Other document types (case diaries, seizure memos, medical and post-mortem reports, court orders) | Each needs its own field list and templates. Three types are enough to prove the method. |
| Audio, video and photo evidence (non-document media) | The Legal Hash is built for text documents with fields, narrative, stamps and signatures. |
| Proving the original was genuine at intake | The system checks later copies against the sealed original. It cannot tell if the original was already false when uploaded. Backdating checks give only partial signals. |
| Judging whether a statement is true | We detect changes to a document, not whether its content is correct. |
| Real filled police documents in the dataset | Privacy and legal risk. We use synthetic documents and blank official templates only. |
| IT Act digital signatures (licensed DSC or eSign) | Our Ed25519 keys are system keys for tamper evidence. They are not digital or electronic signatures under the IT Act 2000. See `REQUIREMENTS.md` section 6 (legal context). |
| Production deployment, high availability, large scale load | This is a demo deployment on student hardware. |
| Native mobile apps | The public verify page is a phone-friendly web page. |
| Multi-state or multi-agency deployment | One demo organisation with one set of roles. |
| Contradiction checks between statements | Stretch phase only. Not part of the core plan. |
| Redacted copies | Not supported in v1. Verification stops with a clear message (D47). |
| Court orders and court-stamped copies as a document type | Court orders are out of scope. A court receipt stamp on a copy is handled as a visual change. |

## 7. Assumptions and constraints

**Team and time**

- Student team of up to 4, part time, around exams. Build window late October 2026 to April 2027.

**Hardware and compute**

- Development on laptops (target 16 GB RAM). Heavy containers (ClamAV, OpenBao) may need Compose profiles.
- Free GPU only (Google Colab or Kaggle) for model training. This limits model size, batch size and training time.
- Inference must run on CPU for the demo. Latency will be measured and reported honestly.

**Deployment**

- Demo deployment with `docker compose up`, not production.
- OpenBao in dev mode simulates key custody. A public RFC 3161 TSA may be unreachable on the college network. Fallback: a local TSA, clearly labelled as local.

**Data**

- Synthetic documents built from blank public templates. No real FIRs or personal data.
- A real capture set (printed and photographed by the team) is used only for validation and testing, never training.

**Licences**

- Libraries and models must have licences that allow commercial use. No non-commercial licences.

**Wording**

- Results are reported from real runs only, with known error rates.
- Outputs are "drafts for officer review". The system "supports" investigation and is "designed in line with" standards.

## 8. Questions for the owner (all resolved)

| # | Question |
|---|---|
| Q1 | Resolved 2026-10-15: `PROJECT_BRIEF.md` is the agreed scope (D27). |
| Q2 | Resolved 2026-10-16: "QR-sealed copy" (D53). |
| Q3 | Resolved 2026-10-16: Court Clerks verify only. Supervisors issue QR-sealed copies (D50). |
| Q4 | Resolved 2026-10-16: the public page shows one fixed message, no field name, value or location (D51). |
