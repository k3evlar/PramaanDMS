# Threat Model

Phase 2 deliverable. Method: STRIDE per component, plus three special groups from `SECURITY_FORENSICS.md` part C (insider threats, attacks on the AI, verification abuse). Format decision: D63 (one table, at most 60 rows, plus a coverage matrix).

Every threat has a mitigation, the phase that builds it, and a test idea. Phase numbers follow `BUILD_PLAN.md`; Phase 25 (backdating) is built last (D52).

## 1. What we protect (assets)

| Asset | Why it matters |
|---|---|
| Original documents (FIRs, statements, charge sheets) | Evidence. Must never change, leak or disappear |
| Fingerprint records (S, F, N, V) and intake seals | The reference every verification is compared against |
| Verdict records | Repeatable results that may be shown to a court |
| Transparency log and signed tree heads | Proof of who did what and when |
| Keys (data keys, key encryption keys, HMAC field key, Ed25519 signing key) | Whoever holds them can read evidence or forge seals |
| The narrative model, thresholds and normalization rules | They decide verdicts |
| User accounts, sessions, roles, case membership | They decide who can see what |
| Personal data inside documents (names, addresses, phone numbers) | Privacy (DPDP Act 2023 safeguards, `REQUIREMENTS.md` section 6) |

## 2. Actors

| Actor | Trust |
|---|---|
| Investigating Officer, Supervisor, Court Clerk, Auditor | Authenticated staff, trusted only for their role and cases |
| System Admin | Trusted to run the system, **not** trusted with evidence content (insider threat) |
| Public verifier | Anonymous, untrusted |
| Outside attacker | Untrusted, may reach the public verify page and any exposed port |
| Insider with server or database access (DBA, operator) | Can bypass the application. Detection, not prevention, is the realistic goal |
| Time-Stamping Authority (FreeTSA in the demo) | Trusted for time only |

## 3. Components and trust boundaries

```
Internet --> [nginx: TLS] --> Web UI (React)
                         --> API (FastAPI) --+--> PostgreSQL (records, verdicts, users)
Public verify page ------^                   +--> SeaweedFS (encrypted originals, Object Lock)
                                             +--> OpenBao (keys)
                                             +--> Valkey --> Worker (OCR, Legal Hash, model)
                                             +--> Transparency log (in PostgreSQL) --> daily STH export (outside)
                                             +--> RFC 3161 TSA (outside)
```

Trust boundaries: Internet to nginx; nginx to API; API to each backing service; worker to model files; the system to the outside STH copy and TSA.

## 4. Threat table

Group: **core** (STRIDE per component), **insider** (C1), **AI** (C2), **verification** (C3).

| ID | Component | STRIDE | Group | Threat | Mitigation | Phase | Test idea |
|---|---|---|---|---|---|---|---|
| T01 | API | S | core | A stolen password or session is used to call the API | Argon2id passwords, TOTP required for all staff, lockout, HttpOnly Secure SameSite cookies, idle and absolute timeouts | 16 | Correct password without TOTP is refused; expired session is refused |
| T02 | API | T | core | Request body sets fields it should not (uploader, case, timestamps): mass assignment | Pydantic schemas with explicit allowed fields; server sets actor and time | 5 | Extra or server-owned fields in a request are rejected with 422 |
| T03 | API | R | core | A user denies having viewed, downloaded or verified a document | Every action writes a custody event (actor from the session, time, source IP, reason for sensitive actions) into the transparency log | 20 | Each endpoint call produces exactly one log entry with the session's actor |
| T04 | API | I | core | IDOR: changing a document or case ID in a URL reveals another case | Case-level membership check in one dependency used by every route; deny by default | 17 | IDOR test for every resource; a route-list test fails if any route lacks the dependency |
| T05 | API | D | core | Upload floods or huge files exhaust disk, memory or the OCR queue | File size, page count and pixel limits; rate limits on login, upload and verify; bounded queue | 5 | Oversized file rejected with 413; burst of requests gets 429 |
| T06 | API | E | core | An IO calls a Supervisor-only action (issue QR-sealed copy, approve) | Function-level role checks, deny by default, access matrix | 17 | Every cell of the access matrix has a passing test |
| T07 | API | T | core | SQL or command injection through field text, search terms or file names | ORM with bound parameters; no shell calls with user input; file names never used as paths; Bandit and Semgrep in CI | 3 | Injection payloads in every text input cause no query or command change; SAST clean |
| T08 | API | I | core | Error pages or logs leak stack traces, field values or tokens | Generic error responses; log scrubbing; structured logs with metadata only | 22 | A forced server error returns no traceback; a log scan finds no field values or tokens |
| T09 | Storage | T | core | An original file is overwritten or deleted | SeaweedFS Object Lock in compliance mode with versioning; no update or delete API | 5 | Overwrite and delete through the S3 API both fail |
| T10 | Storage | T | core | Someone with server access swaps a stored file | SHA-256 at intake in a signed intake record and in the log; integrity re-check on every read and on a schedule | 19 | Replace a raw object; the next read or scheduled check reports a hash mismatch |
| T11 | Storage | I | core | A stolen disk or bucket copy exposes evidence | AES-256-GCM per document with its own data key; keys only in OpenBao | 18 | Reading a raw stored object shows no plaintext; decrypt round trip works |
| T12 | Storage | S, E | core | Default or shared S3 credentials let any service read or write every bucket | Generated per-service credentials; least-privilege bucket policies; no default credentials | 3 | Config check fails on default credentials; the worker's credentials cannot write originals |
| T13 | Storage | D | core | Object Lock retention fills the disk and stops intake | Capacity alarm in the health check; documented retention period; demo sizing | 22 | Health check reports a warning above the set disk threshold |
| T14 | Database | T | core | A DBA edits a fingerprint, verdict or custody row directly | Fingerprint, intake and verdict records are Ed25519-signed; every change is in the Merkle log; background consistency checker | 20 | Edit a row in PostgreSQL; signature check and log checker both flag it |
| T15 | Database | I | core | A database dump exposes personal data from documents | Database holds HMAC fingerprints and metadata; extracted text and field values are stored encrypted with the document's data key | 18 | A dump of all tables contains no plaintext field values from the seeded documents |
| T16 | Database | S, E | core | The application connects as a superuser, so a bug can rewrite anything | Separate database roles: the app role cannot update or delete log rows; migrations use another role | 3 | The app role's UPDATE or DELETE on the log table fails |
| T17 | Database | D | core | Unbounded custody searches overload the database | Pagination limits, indexes, query timeouts | 21 | A search over a huge date range returns one bounded page within the timeout |
| T18 | Transparency log | T | core | An admin rewrites or deletes log entries to hide an action | Append-only Merkle tree (RFC 6962 style), signed tree heads, consistency proofs, daily tree head export outside the system | 20 | Delete or edit a log row; the consistency checker and a standalone verifier both detect it |
| T19 | Transparency log | S | core | The log shows the auditor a different history than everyone else (split view) | Signed tree heads exported daily to an outside copy the auditor keeps; auditor compares heads | 20 | Two signed heads of the same size with different roots are detected |
| T20 | Transparency log | R | core | A log entry claims an action by someone else | The actor comes only from the authenticated session, never from the request body; entries are signed by the system key | 20 | An actor field in a request body is ignored; the entry shows the session user |
| T21 | Transparency log | I | core | Log entries carry document content | Entries hold event type, actor, document ID, hashes and time only | 20 | Log schema test: no content fields; a scan of the log finds no field values |
| T22 | Transparency log | D | core | Log flooding hides events or fills storage | Rate limits on actions; batching; size monitoring | 22 | A load test keeps the log consistent and within the size alarm |
| T23 | Transparency log | E | core | The tree-head signing key is used to sign fake heads | Signing key held in OpenBao; key access needs two people; every key use is logged | 18 | Key use without a second approval is refused and logged |
| T24 | Worker | S, T | core | A forged or malicious job is injected into the queue (for example a pickle payload) | Celery uses the JSON serializer only (D60); Valkey requires a password and is on the internal network only; job payloads are validated | 3 | A pickle-serialized task is rejected; the Valkey port is not published by Compose |
| T25 | Worker | D | core | A malicious PDF or image hangs or crashes OCR (decompression bomb, huge pixel count) | ClamAV scan; page, pixel and decompression limits; per-task time and memory limits | 22 | A crafted bomb file is rejected within the time limit and the worker stays up |
| T26 | Worker | E | core | A parser bug in a PDF or image library gives code execution | Pinned, maintained libraries with pip-audit; worker runs as non-root with a read-only file system and no key store access beyond what it needs | 22 | Container runs as non-root; write to the code path fails |
| T27 | Worker | I | core | Decrypted evidence is left in temporary files on the worker | Processing in memory or tmpfs; cleanup after every job | 18 | After a job, a scan of the worker's temp space finds no document bytes |
| T28 | Worker | R | core | A verdict cannot be traced to the code and model that made it | Every verdict record stores model, OCR, rules and code versions and the job ID; re-run endpoint | 8 | A stored verdict re-run gives the same result and the same versions |
| T29 | Verify page | S | verification | A forged QR code points to a fake record | QR payload signed with Ed25519; verify page checks the signature with a pinned public key and an algorithm allowlist | 23 | A QR with a changed byte or wrong key is rejected |
| T30 | Verify page | T | verification | A valid QR is copied onto an altered or different printout (replay) | The verify page compares the photographed content with the record named in the QR, not just the QR signature | 23 | A QR copied onto another document gives Tampered |
| T31 | Verify page | I | verification | The public response leaks field names, values or locations, or lets someone enumerate documents | One fixed message per outcome (D51); no content in responses; unguessable record references in the QR; rate limits | 23 | Response schema test: only the allowed fixed messages; random references return the same "not valid" message |
| T32 | Verify page | D | verification | Scripted uploads to the free public page exhaust OCR capacity | Per-IP rate limits, size limits, bounded queue, short timeouts | 22 | A burst from one address gets 429; the queue stays bounded |
| T33 | Verify page | R | verification | Someone claims the page gave them a different result | Every public verify is logged with the request hash, record reference, result and time | 23 | A public verify creates one log entry with these fields |
| T34 | Verify page | E | verification | Data in the QR is used to reach internal services (SSRF) or inject script | The QR is parsed as fixed-schema data only; the server never fetches URLs from a QR; output is escaped | 23 | A QR holding a URL or script is rejected as invalid |
| T35 | Model | T | AI | The narrative model file is swapped for one that misses edits | Signed model registry; the service refuses a model whose hash is not registered | 15 | Replace the model file; verification refuses to start |
| T36 | Model | T | AI | Thresholds (c_min, t_N, t_V) are changed to hide edits | Thresholds in a signed config; changes need two-person approval | 15 | Edit the config file; signature check fails and the service refuses it |
| T37 | Model | T | AI | Training data is poisoned so the model learns to ignore real edits | Dataset and split hashes recorded; training only on generated data with recorded seeds | 12 | Training refuses a dataset whose manifest hash does not match |
| T38 | Model | S | AI | Adversarial edits make a changed document pass as Equivalent (homoglyphs, zero-width characters, tiny pixel edits on digits) | Exact fingerprints for fields and narrative entities; homoglyph flagging; zero-width warnings; adversarial test set | 27 | The adversarial set's edits are all caught or flagged; results reported |
| T39 | Model | I | AI | Fingerprints or narrative codes reveal document content | HMAC with a secret key for fields and entities; fingerprint records stay on the server; the public page never receives codes | 23 | Public responses contain no fingerprints; guessing a date field without the key fails |
| T40 | Model | D | AI | Slow inference on large documents blocks the queue | Per-page time limits; page limits; CPU latency measured and capped | 15 | A 20-page document finishes or times out within the documented limit |
| T41 | Model | R | AI | A verdict cannot be reproduced later | Versions of model, OCR, rules and code stored with each verdict; deterministic inference | 15 | Re-running stored verdicts gives identical results |
| T42 | Model | E | AI | Loading a model file runs code (pickle in model weights) | Only safetensors weights are loaded, after the hash check | 12 | Loading a pickle-based weight file is refused |
| T43 | Admin console | I | insider | The System Admin opens evidence content | Admin role has no content permission; the attempt is blocked, logged and alerted | 17 | Admin download of an original returns 403 and creates an alert log entry |
| T44 | Access control | E | insider | One insider releases a legal hold, exports in bulk or rotates keys alone | Two-person rule with request, second approver and expiry; nobody approves their own request | 17 | A request approved by its requester fails; an expired approval fails |
| T45 | Evidence | T | insider | An insider hard-deletes evidence | No delete route anywhere; archive only; Object Lock | 21 | Route-list test finds no delete route for evidence; delete through S3 fails |
| T46 | Evidence | T | insider | An IO quietly replaces an uploaded document to fix a mistake | Corrections are new versions, each sealed and logged; verify always names the version | 5 | Uploading a correction creates version 2; version 1 stays sealed and readable |
| T47 | Evidence | R | insider | A document is backdated (a new upload claims an old date) | RFC 3161 time-stamp at intake; backdating rules built last (Phase 25) | 19 | The time-stamp token verifies and shows the real intake time |
| T48 | QR-sealed copy | T | insider | A Supervisor issues a QR-sealed copy of an altered file | Copies are generated server-side only from the sealed stored version, never from an uploaded file; each issue is logged | 23 | No API accepts a file for issuing; the issued copy's hash matches the sealed version |
| T49 | Access control | E | insider | An admin grants themselves or a friend a higher role | Role grants for Supervisor and Admin need a second approver; self-grants are refused | 17 | A self-grant is refused; a grant without approval is refused |
| T50 | Key store | I | core | Keys are taken from OpenBao (for example a leaked root token) | Root token never stored in the repo; the app uses a scoped token with least-privilege policies; dev mode only in the demo, production path documented | 18 | The app token cannot read policies or other paths; gitleaks finds no token |
| T51 | Time | T | core | The server clock is changed to fake event times | NTP sync to NIC or NPL servers (CERT-In direction); RFC 3161 tokens and tree head times give outside evidence | 3 | Clock offset above the limit raises a health warning |
| T52 | Time-stamp authority | D | core | The TSA is unreachable, so intake cannot be time-stamped | Records marked "time-stamp pending" with a retry queue; a local TSA, labelled local, as the fallback (D64) | 19 | With the TSA blocked, intake succeeds as pending and is stamped after reconnecting |
| T53 | Build and supply chain | T | core | A malicious dependency or a leaked secret enters the repo | Pinned dependencies; pip-audit, npm audit, gitleaks, Bandit, Semgrep in CI; SBOM | 3 | CI fails on a planted test secret and on a known-vulnerable pinned package |
| T54 | Web UI | T | core | Script inside a document's text runs in an officer's browser (stored XSS through OCR text) | React escaping; no raw HTML rendering; Content-Security-Policy | 22 | A document whose narrative contains a script tag renders it as plain text |
| T55 | Web UI | S | core | Cross-site request forgery makes an officer's browser approve or issue something | SameSite cookies plus a CSRF token on every state-changing request | 22 | A cross-site POST without the token is rejected |
| T56 | Reports | T | core | A forensic report or Section 63 draft is edited after it is generated | Reports are Ed25519-signed and can be verified | 26 | Changing one byte of a report makes its signature check fail |
| T57 | Verify (all) | T | verification | A redacted copy is submitted so a changed field cannot be compared | Redacted copies are detected and rejected with a clear message (D47) | 8 | A copy with a blacked-out field returns the "not supported" message and no verdict |
| T58 | Verify (all) | T | AI | One field is blurred on purpose to force Inconclusive and hide an edit elsewhere | A clear edit always wins; unreadable fields are listed as "could not verify" (D41) | 8 | Blur one field and edit another: the verdict is Tampered with the blurred field listed |
| T59 | Verify (all) | T | AI | An ink mark is drawn over a critical field to hide its value | Annotation over a critical field is Major; an unreadable field is listed as "could not verify" (D46) | 14 | A mark over the date of incident gives Tampered, Major |

Rows: 59 (limit 60).

## 5. Coverage matrix

Every core component from `BUILD_PLAN.md` Phase 2 against every STRIDE category. Each cell names the threats that cover it, or says why none applies.

| Component | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| API | T01, T55 | T02, T07 | T03 | T04, T08 | T05 | T06 |
| Storage | T12 | T09, T10, T46 | n/a: storage is reached only through the API, whose actions are logged (T03) | T11 | T13 | T12 |
| Database | T16 | T14 | n/a: users never reach the database directly; actions are logged in the transparency log (T03, T20) | T15 | T17 | T16 |
| Transparency log | T19 | T18 | T20 | T21 | T22 | T23 |
| Worker | T24 | T24 | T28 | T27 | T25 | T26 |
| Verify page | T29 | T30, T57 | T33 | T31 | T32 | T34 |
| Model | T38 | T35, T36, T37 | T41 | T39 | T40 | T42 |

Special groups: insider T43 to T49 (7 threats), AI T35 to T42, T58, T59 (10 threats), verification T29 to T34, T57 (7 threats).

## 6. Residual risks (accepted for the demo)

| Risk | Why accepted | Where stated |
|---|---|---|
| An insider with full server and database access can still destroy data | Detection is guaranteed by the outside tree head copy and signatures; prevention would need hardware and organisational controls we do not have | `LIMITATIONS.md` (Phase 28) |
| OpenBao runs in dev mode and keys are not in an HSM | No HSM available (SCOPE.md) | `KEY_MANAGEMENT.md` (Phase 18) |
| Logs are not shipped in full to a separate system | Signed tree heads are exported; full log shipping is out of demo scope (ASVS V16.4.3 accepted gap) | `ASVS_CHECKLIST.md` |
| The original may have been false before intake | The system checks later copies, not the truth of the original (SCOPE.md) | `SCOPE.md` |
| FreeTSA has no published terms or SLA | Demo only; the TSA URL is configuration (D64) | `LICENCES.md` |
