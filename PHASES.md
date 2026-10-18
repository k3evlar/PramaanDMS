# Build Phases (28 core + 1 stretch)

Updated on 16 October 2026 to the decisions locked before Phase 2 (`DECISIONS.md` D39 to D61): English only, Tampered with Major or Minor severity, QR-sealed copies issued by Supervisors, backdating built at the end, stack confirmed by the licence check.

Order rule: **working demo first, then the AI, then full security, then investigation features, then proof.** If time runs short, there is always a working demo of the main idea.

Each phase: goal, what to build, exit criteria. Do one phase per session. Update `PROGRESS.md` at the end.

Rough timeline (adjust to real college dates):

| Stage | Phases | When |
|---|---|---|
| 1. Foundation | 1 to 3 | Late Oct 2026 |
| 2. Working demo | 4 to 9 | Nov 2026 |
| 3. AI brain | 10 to 15 | Dec 2026 to Jan 2027 |
| 4. Security and forensics core | 16 to 22 | Feb 2027 |
| 5. Investigation and product | 23 to 26 | Mar 2027 |
| 6. Proof and finish | 27 to 28 | Apr 2027 |

---

## Stage 1: Foundation

### Phase 1: Scope, tampering definition, literature, novelty
**Build:**
- `docs/SCOPE.md`: users, roles, document types, in and out of scope
- `docs/TAMPERING_DEFINITION.md`: Equivalent vs Tampered, Major vs Minor, Inconclusive, with 20+ worked examples (including "reworded statement = Tampered")
- Final critical field list with types
- `docs/LITERATURE.md`: 30+ real papers and systems grouped by topic (secure DMS, chain of custody, fuzzy hashing, perceptual hashing, semantic hashing, contrastive learning, Indic OCR, document tampering detection, transparency logs, legal NLP). Every citation must be real and verifiable. Mark unsure ones `TODO: verify`
- `docs/NOVELTY.md`: research gap, contributions, 2 to 3 research questions, hypotheses
- `docs/CRITICAL_FIELDS.md`: final critical field list with types
**Exit:** all five docs written, no invented citations, gap clearly stated.

### Phase 2: Threat model, requirements, licences
**Build:**
- `docs/THREAT_MODEL.md`: STRIDE table plus insider, AI and verification threats (see `SECURITY_FORENSICS.md`)
- `docs/REQUIREMENTS.md`: functional, non-functional (performance targets, availability), legal context (IT Act 2000, BSA 2023 Section 63, DPDP Act 2023, BNS transition date). Mark any legal claim to verify
- `docs/LICENCES.md`: every planned library and model with licence. Reject non-commercial licences
- `docs/ASVS_CHECKLIST.md`: OWASP ASVS Level 2 items marked planned / done / not applicable
**Exit:** threat table covers all groups, every requirement is testable, licence table has no blockers.

### Phase 3: Project setup
**Build:**
- Repo structure per `ARCHITECTURE.md`
- Docker Compose with all containers healthy
- FastAPI skeleton with health endpoint, settings, logging
- React skeleton
- Alembic set up
- CI: pytest, Bandit, Semgrep, pip-audit, npm audit, gitleaks
- `.env.example`, `README.md` with run steps
**Exit:** `docker compose up` starts everything, CI passes, health check works.

---

## Stage 2: Working demo first

### Phase 4: FIR-Tamper dataset v1
**Build:**
- Generator for synthetic FIRs, witness statements, charge sheets in English with realistic fields
- Render to PDF and images
- Tamper generator: field edits (date, name, amount, section), narrative edits (word swap, negation, sentence add/remove), visual edits (stamp removed or swapped)
- Equivalence traps: number formats, date formats, standard separators, honorifics, reflowed layout, different fonts
- Labels: verdict, severity, list of changes with locations
- Fixed train / validation / test split with dataset hash recorded
**Exit:** dataset generated reproducibly from a seed, labels validated on a sample, split hashes saved.

### Phase 5: Evidence intake (basic)
**Build:**
- DB schema v1 (documents, versions, storage objects, fingerprints, verdicts, custody events)
- Upload API: magic byte check, size limit, SHA-256 at intake
- Store original in SeaweedFS with S3 Object Lock in compliance mode (no overwrite)
- Basic custody event on every upload
**Exit:** upload works, overwrite attempt fails, SHA-256 recorded, tests pass.

### Phase 6: OCR pipeline
**Build:**
- Preprocessing: deskew, perspective correction, denoise, page split
- Benchmark PaddleOCR vs Tesseract on a dataset sample (accuracy on English, speed, confidence quality). Record results and choose. Surya is excluded by its weights licence
- OCR output: text, boxes, per-token confidence, stored per page
- Runs in the background worker
**Exit:** OCR choice made with real numbers in `DECISIONS.md`, pipeline returns text + boxes + confidence.

### Phase 7: Fact check (field fingerprint)
**Build:**
- Field extraction with rules and regex using OCR boxes and labels
- Normalization module per `LEGAL_HASH_SPEC.md` section 5, with unit tests for every rule
- HMAC field and narrative entity fingerprints (key from config for now, OpenBao later)
- Equivalence traps test: must not produce changes
**Exit:** field extraction accuracy measured on the dataset, all equivalence traps pass, one-digit change test caught.

### Phase 8: Verify v1
**Build:**
- Verify API: candidate file vs stored document
- Identical (SHA-256), field diff, Tampered with severity (a clear edit wins), Inconclusive only when no clear edit and some fields unreadable, Equivalent; redacted copies rejected with a message
- Change list with page and box
- Verdict record with versions (repeatability)
**Exit:** end to end verify works on dataset samples, verdict re-run gives the same result.

### Phase 9: Basic UI
**Build:**
- Login placeholder (simple, replaced in Phase 16)
- Upload page, document list, document detail
- Verify page: upload candidate, show verdict, highlight changed fields on the page image
**Exit:** full demo works in the browser: upload, then verify a phone photo, see the verdict and highlighted change. **Milestone: working demo.**

---

## Stage 3: The AI brain

### Phase 10: Real capture set and augmentation
**Build:**
- Print 100 to 200 dataset documents, photograph on 3 to 4 phones in different light, angles, folds. Tools to label and match captures to originals
- Augmentation pipeline: blur, noise, JPEG compression, perspective, shadows, folds, stamps
**Exit:** capture set stored with labels, augmentation produces realistic variants, both versioned.

### Phase 11: Baselines
**Build:**
- Run SHA-256, ssdeep, TLSH, pHash, OCR text diff, plain embedding cosine on the test set
- Metrics script (shared with later evaluation)
**Exit:** baseline results table from real runs saved in `docs/RESULTS.md`.

### Phase 12: Narrative hash model
**Build:**
- MuRIL encoder + projection + binary hash head
- Triplet training with hard negatives and quantization loss
- Training on Colab or Kaggle GPU if needed, config and seed saved
- Threshold selection on validation set
**Exit:** model trained, narrative change recall and false alarm rate measured on validation, model saved with hash.

### Phase 13: Smarter field extraction
**Build:**
- MuRIL token tagger for fields, trained on dataset labels
- Combine with rules (rules first, tagger fills gaps, conflicts flagged)
**Exit:** field extraction accuracy improves over Phase 7 on the test set (report both).

### Phase 14: Stamp and signature check
**Build:**
- Region detection (heuristics, optional small detector)
- Alignment and perceptual hash per region
**Exit:** stamp swap and removal caught on the dataset, false alarms measured on Equivalent copies.

### Phase 15: Final verdict logic and model integrity
**Build:**
- Combine F + N + V per `LEGAL_HASH_SPEC.md` section 9
- Tune thresholds on validation
- Signed model registry: refuse to load unknown model hash
- Thresholds in signed config
**Exit:** full Legal Hash runs end to end, ablation (F, N, F+N, F+N+V) on validation recorded, model swap test blocked.

---

## Stage 4: Security and forensics core

### Phase 16: Authentication
**Build:** Argon2id passwords, TOTP MFA, lockout, secure sessions, password rules, login events logged.
**Exit:** auth tests pass, lockout works, MFA required for all staff roles.

### Phase 17: Access control and insider controls
**Build:**
- RBAC + case-level access on every endpoint
- Admin cannot read evidence content
- Two-person approval workflow for risky actions
- IDOR tests for every resource
**Exit:** access matrix tests pass, admin evidence access blocked and logged, two-person rule enforced.

### Phase 18: Encryption and keys
**Build:**
- OpenBao integration, key hierarchy, per-document data keys, AES-256-GCM
- KEK rotation, every key use logged
- Move HMAC field key and signing key to OpenBao
**Exit:** files encrypted at rest (verify by reading the raw stored object), rotation works without data loss.

### Phase 19: Sealing
**Build:** Ed25519 signed intake records and fingerprint records, RFC 3161 timestamp at intake, verification of both.
**Exit:** seal and timestamp verify correctly, tampered seal detected.

### Phase 20: Transparency log
**Build:**
- Merkle log, signed entries, signed tree heads
- Inclusion and consistency proofs with an API
- Daily STH export to an outside location
- Background job that checks consistency and alerts
**Exit:** direct DB edit of a log row is detected, proofs verify, STH export works.

### Phase 21: Chain of custody, legal hold, archive
**Build:**
- Full custody history view per document
- Legal hold (blocks archive), release needs two-person approval
- Archive only, no hard delete anywhere
**Exit:** custody view complete, delete attempts impossible, legal hold enforced.

### Phase 22: App hardening
**Build:** TLS, security headers, CSRF, rate limits, ClamAV scan and quarantine, input validation, safe error messages, no sensitive data in logs.
**Exit:** ASVS checklist updated, header and rate limit tests pass, EICAR test file quarantined.

---

## Stage 5: Investigation and product

### Phase 23: QR-sealed copy
**Build:**
- Issue QR-sealed copy (Supervisor only): PDF with QR (signed payload per spec section 10)
- Public phone-friendly verify page: scan or upload photo, check signature, run Legal Hash, return one fixed public message (no field names, values or locations)
- Rate limits on public verify
**Exit:** print, alter with a pen, photograph: the public page says "A critical field was changed." and an authenticated clerk sees the correct field. Forged QR rejected.

### Phase 24: Tamper window
**Build:** checkpoints (each verify and access creates a fingerprint check), find the window between last good and first bad, list custody events and users in the window.
**Exit:** demo scenario shows the correct window and users.

### Phase 25: Backdating checks (built last, after Phase 26)
**Build:**
- Law anachronism rule: document date before 1 July 2024 citing BNS / BNSS / BSA sections, and related checks (verify the effective date in Phase 2)
- Timeline sanity: incident date after report date, statement before FIR, and similar
- Timestamp evidence: compare claimed document date with RFC 3161 sealing time
- Each flag explained in plain language
**Exit:** rule tests pass on crafted examples, no flags on clean dataset samples (false flag rate measured).

### Phase 26: Reports and UI polish
**Build:**
- Signed forensic PDF report (verdict, changes, custody, hashes, timestamps, tool versions, known error rates)
- Section 63 draft certificate (clearly marked draft for officer review)
- Role dashboards (IO, Supervisor, Clerk (verify only), Auditor, Admin)
- UI polish, phone layout
**Exit:** reports generate and verify, every role can complete its main task in the UI.

---

## Stage 6: Proof and finish

### Phase 27: Evaluation and security testing
**Build:**
- Final test-set evaluation: all metrics, baselines, ablations, per capture condition, latency
- Adversarial tests (homoglyphs, zero-width, digit pixel edits, screen re-photo)
- Attack demo per `SECURITY_FORENSICS.md` Part G
- OWASP ZAP scan, fix findings, final ASVS checklist
**Exit:** `docs/RESULTS.md` complete with real numbers and known error rates, attack demo scripted and working.

### Phase 28: Wrap up
**Build:**
- Research paper draft
- Project report
- OpenAPI docs, `docs/LIMITATIONS.md`, user guide
- 5-minute demo script and seeded demo data
- Backup and restore test
- Final clean deployment from scratch
**Exit:** fresh machine runs the full demo from README in one command, all docs complete.

---

## Stretch (only if time is left)

### Phase S: Contradiction check
NLI model to flag contradictions between statements in the same case (for example two witness statements disagreeing on time). Time-boxed. Must not block anything above.
