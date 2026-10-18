# Pramaan DMS: Project Brief (Final, Oct 2026)

Updated on 16 October 2026 to the decisions locked before Phase 2 (`DECISIONS.md` D39 to D56).

## One line

A secure evidence system for FIRs and statements that can tell a harmless copy from a real edit, show exactly what changed, and prove who had access and when.

## Domain

Digital forensics and cybersecurity, with applied AI (document understanding, contrastive learning).

## The problem

Police and courts store FIRs, witness statements, and charge sheets digitally. Today, integrity is checked with a normal cryptographic hash (SHA-256). That has two problems:

1. **Too strict.** Any rescan, reprint, or phone photo of the same page gives a different hash, so it looks "tampered" even when nothing changed.
2. **Says nothing useful.** It can only say "different". It cannot say *what* changed, or whether the change matters.

Also, existing systems rarely handle the **insider** case well (someone with access quietly edits a record), and they rarely let an outside party verify a paper copy without getting the original file.

## Our solution

Pramaan DMS adds a **Legal Hash**: a hybrid fingerprint that ignores harmless format changes but catches real content edits, and explains them.

- **Fact check (deterministic):** extract critical fields (FIR number, dates, names, places, amounts, law sections, police station, officer), normalize them, and fingerprint each field exactly. A one-digit change is always caught.
- **Story check (learned):** an AI model (MuRIL, trained with contrastive triplet loss, binary hash output) fingerprints the free-text narrative. It learns to ignore OCR noise, scan and photo artefacts, but react to real wording changes.
- **Visual check:** stamps and signatures get their own perceptual fingerprints.

SHA-256 is still kept for exact-file integrity and for the BSA Section 63 certificate.

## The 4 verdicts

| Verdict | Meaning |
|---|---|
| **Identical** | Exact same file (SHA-256 match) |
| **Equivalent (Format)** | Same content, only capture or format differs (rescan, photo, reprint, spacing, fonts) |
| **Tampered** | Content changed. Severity: **Major** (a critical field, a narrative date, name, number or section, a negation flip, a page, a stamp or signature, or an annotation over a critical field) or **Minor** (wording, punctuation, name order, a non-critical field, an annotation outside critical fields). Always shows what changed and where to authorised staff. Unreadable fields are listed as "could not verify" |
| **Inconclusive** | No clear change, but some critical fields could not be read. Sent to human review |

Note: a reworded witness statement with the "same meaning" is **Tampered**, not Equivalent. In legal documents, wording matters. A clear edit always wins over unreadable fields. Redacted copies are not supported in v1 and are rejected with a clear message.

## The 5 security layers

1. **Lock:** login with Argon2 passwords and TOTP, roles, case-level access
2. **Protect:** AES-256-GCM encryption per file, keys in a key vault (OpenBao)
3. **Seal:** Ed25519 signature and RFC 3161 trusted timestamp at intake
4. **Track:** tamper-evident Merkle transparency log of every action, with signed tree heads published outside the system
5. **Verify and Investigate:** Legal Hash verification, tamper window, backdating checks, forensic reports

## Key features for the industry demo

1. **QR-sealed copy:** a Supervisor issues an official copy that carries a QR with the signed fingerprint. Anyone photographs the paper and gets a verdict, without needing the original file. The public page shows one fixed message (for example "A critical field was changed"), never field names or values.
2. **Tamper window:** when a change is found, the system narrows the time range and lists who had access in that window.
3. **Backdating checks** (in scope, built at the end of the build): rule-based. Example: BNS, BNSS and BSA came into force on 1 July 2024, so a document dated earlier that cites BNS sections is flagged. Plus timeline sanity checks and trusted timestamp evidence.
4. **Forensic report:** one-click signed PDF with verdict, changes, custody history, hashes, tool versions.
5. **Section 63 draft:** auto-filled draft certificate for officer review.
6. **Insider protection:** admin cannot read evidence, two-person rule for risky actions, no hard delete.

## Users (roles)

- **Investigating Officer (IO):** uploads and works on own cases, requests QR-sealed copies
- **Supervisor (SHO / senior officer):** oversees cases, uploads, approves sensitive actions, issues QR-sealed copies
- **Court Clerk / Verifier:** verifies copies only
- **Auditor:** reads logs and custody history, cannot read document content
- **System Admin:** manages users and system, **cannot read evidence**
- **Public verifier (no login):** uses the QR verify page only and sees one fixed message

## Document types in scope

FIRs, witness statements, charge sheets. English only (Hindi is future work). Typed or printed. Inputs: PDF, scans, phone photos.

## Out of scope (say this clearly in demos)

- Handwritten documents beyond basic
- Languages other than English, including Hindi (future work)
- Redacted copies (not supported in v1)
- Integration with real police systems (CCTNS, e-Sakshya, ICJS). We expose an API that such systems *could* call
- Any claim of legal admissibility or certification
- Production HSM (we simulate with OpenBao in dev mode)

## Research contributions (for the paper)

1. A legal-domain **tampering definition** that separates format changes from content changes, with severity
2. The **hybrid field-aware Legal Hash** (deterministic field fingerprints + learned narrative hash + visual region hashes)
3. The **FIR-Tamper dataset** (synthetic English documents, real phone captures, equivalence traps, adversarial edits)
4. **Tamper window detection** that links fingerprint checkpoints to a transparency log
5. Benchmark against SHA-256, ssdeep, TLSH, pHash, OCR text diff, and plain embedding similarity, with published error rates

## Final deliverables

- Working app, one command to run (`docker compose up`), with seeded demo data
- Phone-friendly QR verify page
- Forensic report and Section 63 draft generator
- Verify API with OpenAPI docs
- Benchmark report with error rates
- Threat model (STRIDE) and OWASP ASVS Level 2 checklist
- Licence table
- Limitations page
- Research paper draft and project report
- 5-minute demo script
