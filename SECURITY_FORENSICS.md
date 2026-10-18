# Security and Forensics Requirements

Pramaan DMS is a digital forensics and cybersecurity project. These rules apply in every phase.

## Part A: Digital forensics principles

| Principle | Meaning | Implementation |
|---|---|---|
| Preserve the original | Originals never change | Write-once storage (SeaweedFS S3 Object Lock, compliance mode). No update or overwrite API for originals |
| Hash at acquisition | Fingerprint at the moment of intake | SHA-256 and Legal Hash computed at upload, before any processing. Intake record signed |
| Chain of custody | Record every touch | Every view, download, share, verify, export logged with who, when, from where, why |
| Trusted time | Prove when | RFC 3161 timestamp at sealing. Server clock synced (NTP) |
| Repeatability | Same input, same answer | Every verdict stores model, OCR, rules and code versions. Re-run must match |
| Known error rate | Tool states how often it is wrong | Benchmark report publishes false alarm and miss rates |
| Documented findings | Clear report | Signed forensic PDF report |

Standards to reference (say "designed in line with", never "certified"):

- ISO/IEC 27037 (identification, collection, acquisition, preservation of digital evidence)
- NIST SP 800-86 (integrating forensic techniques into incident response)
- ACPO Good Practice Guide principles for digital evidence
- BSA 2023 Section 63 (certificate for electronic records, includes hash values). Generate **drafts** only

Verify exact wording and current versions of each standard before quoting them in the report or paper.

## Part B: Security goals

- **Confidentiality:** AES-256-GCM per file, envelope encryption, TLS in transit
- **Integrity:** SHA-256, Legal Hash, Ed25519 signatures, Merkle log
- **Availability:** backups, tested restore
- **Authentication:** Argon2id passwords, TOTP MFA, lockout
- **Authorization:** RBAC + case-level access + least privilege
- **Non-repudiation:** signed actions and signed log entries
- **Accountability:** complete audit trail

Design principles: least privilege, defence in depth, zero trust (every request authenticated and authorized), secure by default, fail closed.

## Part C: Threat model (STRIDE)

Build the full table in Phase 2. Must cover at least:

- **Spoofing:** stolen passwords, session hijack, forged QR
- **Tampering:** DB edits, file swap in storage, log rewrite, model file swap, edits to printed copies
- **Repudiation:** "I never opened that file"
- **Information disclosure:** stolen storage, admin reading evidence, leaks in logs or URLs
- **Denial of service:** upload floods, huge files, zip bombs
- **Elevation of privilege:** role abuse, IDOR (accessing another case by changing an ID)

Plus three special threat groups:

### C1. Insider threats (highest priority)
- Admin cannot read evidence content. Admins manage users and config only
- **Two-person rule** for: key access or rotation, releasing a legal hold, granting supervisor or admin roles, bulk export, archival
- **No hard delete** of evidence. Only archive, with legal hold support
- Log integrity does not depend on trusting the admin: signed tree heads are published outside the system daily
- Separation of duties between IO, Supervisor, Auditor, Admin

### C2. Attacks on the AI
- Adversarial edits (homoglyphs, zero-width characters, tiny digit edits)
- Model file replacement (blocked by signed model registry)
- Training data poisoning (dataset versioning and hashes)
- Threshold manipulation (thresholds stored in signed config, changes need two-person approval)

### C3. Verification abuse
- Forged QR codes (QR is signed, verify page checks signature)
- Replay of an old valid QR on a new altered printout (verify compares content, not just the QR)
- Verify endpoint scraping (rate limits, returns verdict only, never document content to public users)

## Part D: Cryptography and keys

- Algorithms: AES-256-GCM, SHA-256, HMAC-SHA-256, Ed25519, Argon2id. Use well-known libraries only (`cryptography`, `argon2-cffi`, `pyotp`). **Never write your own crypto.**
- Key hierarchy: master key (OpenBao) -> key encryption keys -> per-document data keys
- Rotation schedule for KEKs and signing keys. Old keys kept for verification only
- Every key use logged
- Designed in line with NIST SP 800-57 key management guidance

## Part E: Transparency log

- Append-only Merkle tree (RFC 6962 style)
- Each entry signed by the system key and contains: event type, actor, document, timestamp, previous tree size
- Signed Tree Head (STH) after each batch
- Inclusion proofs (this event is in the log) and consistency proofs (the log only grew, nothing was rewritten)
- Daily STH exported to an outside location (a public git repo, email, or file the auditor keeps)

## Part F: Application security

- Checklist: **OWASP ASVS Level 2**. Test against **OWASP Top 10**
- Input validation, file type check by magic bytes, size limits, ClamAV scan, quarantine
- Security headers, CSRF protection, rate limiting, secure cookies
- No sensitive data in URLs or logs
- Secure build: Bandit, Semgrep, pip-audit, npm audit, gitleaks in CI. Pinned dependencies

## Part G: Proof (attack demo in Phase 27)

1. Edit a row in the database directly -> log consistency check catches it
2. Replace a stored file -> hash check catches it
3. Admin tries to open evidence -> blocked and logged
4. Swap the model file -> service refuses to start verification
5. Forge a QR -> verify page rejects it
6. OWASP ZAP scan -> report included
