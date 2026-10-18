# Requirements

Phase 2 deliverable. English documents only (D39).

Every requirement has an ID, an acceptance test, and the phase that builds it. Numbers marked **target** are goals set now. They are checked against real measurements later and reported honestly whether met or not. They are not results.

Sources for the rules: `docs/SCOPE.md`, `docs/TAMPERING_DEFINITION.md`, `docs/CRITICAL_FIELDS.md`, `LEGAL_HASH_SPEC.md`, `SECURITY_FORENSICS.md`, and the decisions D39 to D66 in `DECISIONS.md`. Threat IDs (T01 to T59) refer to `docs/THREAT_MODEL.md`.

## 1. Functional requirements by role

| ID | Requirement | Acceptance test | Phase |
|---|---|---|---|
| FR-01 | An Investigating Officer or Supervisor can upload a PDF, PNG, JPEG or TIFF document to a case they are a member of. | Upload by a member succeeds and returns a document ID; upload to a case the user is not a member of returns 403. | 5, 17 |
| FR-02 | Court Clerks, Auditors, System Admins and public users cannot upload evidence (D50). | Upload attempts by each of these roles return 403 and create a log entry. | 17 |
| FR-03 | At intake the system computes SHA-256 of the exact bytes before any processing, stores the original write-once, and records a custody event. | Stored SHA-256 equals a local calculation; overwrite and delete through storage fail; one custody event per upload. | 5 |
| FR-04 | Every original is sealed: an Ed25519-signed intake record (document ID, SHA-256, size, uploader, time) and an RFC 3161 time-stamp token. | Seal and token verify; changing one byte of the record makes verification fail. | 19 |
| FR-05 | The background worker computes the Legal Hash fingerprint record (S, F for fields and narrative entities, N, V) and signs it. | A sealed document gets a signed fingerprint record; the signature verifies. | 7, 15, 19 |
| FR-06 | A corrected document is stored as a new version; earlier versions stay sealed and readable. | Uploading a correction creates version 2; version 1 is unchanged and verifiable. | 5 |
| FR-07 | An authorised user can verify a candidate file against a chosen document version and gets one of Identical, Equivalent, Tampered or Inconclusive. | Each verdict is reached on crafted samples. | 8, 15 |
| FR-08 | Tampered gives a severity, Major or Minor, by the rule in `TAMPERING_DEFINITION.md` section 2. | The 51 worked examples give the listed verdict and severity. | 8, 15 |
| FR-09 | A clear edit always gives Tampered, even when other fields are unreadable; unreadable fields are listed as "could not verify" (D41). | Blur one field and edit another: Tampered, with the blurred field in the "could not verify" list. | 8 |
| FR-10 | Inconclusive is returned only when no clear change exists and at least one critical field or narrative entity is below the confidence threshold. | Blur one field, change nothing else: Inconclusive, listing that field. | 8 |
| FR-11 | Spacing between words and lines, fonts, letter case, metadata, standard separators, date and number formats, honorifics and the order of law sections are format and give Equivalent. | Every equivalence trap in the test set gives Equivalent. | 7 |
| FR-12 | A space that splits or merges a value inside an ID, number, date or time is content (D40). | `142/2026` vs `14 2/2026` gives Tampered, Major. | 7 |
| FR-13 | A changed, added or removed critical field value, including a law section added or removed, is Major. | One-digit edits in dates, amounts, IDs and a section added or removed all give Major. | 7 |
| FR-14 | Dates, times, names, numbers, amounts, vehicle and section numbers inside the narrative are fingerprinted exactly; a change is Major (D45). | Changing only a date inside the narrative gives Tampered, Major, located in the narrative. | 7 |
| FR-15 | A negation flip in the narrative is Major (D42), detected by a deterministic rule as well as the learned hash. | "did" to "did not" gives Major even with the narrative model switched off. | 12, 15 |
| FR-16 | Narrative wording, punctuation and sentence changes with no narrative entity and no negation flip are Minor. | A one-word swap and a reworded sentence each give Tampered, Minor. | 12 |
| FR-17 | A change in the order of names in a list is Minor (D44). | Swapping accused 1 and 2 gives Tampered, Minor. | 7 |
| FR-18 | A page added, removed or reordered is Major (D43). | Each page edit gives Tampered, Major. | 8 |
| FR-19 | A stamp, seal or signature removed, added or swapped is Major. | Seal removed, seal swapped, signature swapped and court stamp added each give Major. | 14 |
| FR-20 | An unsealed annotation outside critical fields is Minor and flagged; overlapping a critical field it is Major (D46). | Margin note gives Minor with a flag; a mark across the date of incident gives Major. | 14 |
| FR-21 | A redacted copy is not verified; the user sees "Redacted copies are not supported in this version." (D47). | A copy with a blacked-out field gets that message and no verdict. | 8 |
| FR-22 | Every Tampered verdict lists each change with field or region name, page and location. Old and new values are shown only to authenticated users with access to the case. | The change list of each tampered sample names the right field and page; a user without case access gets 403. | 8, 17 |
| FR-23 | Every verdict record stores the verdict, changes, "could not verify" list, confidences, thresholds, model, OCR, rules and code versions, and time; a re-run gives the same result. | Re-running stored verdicts gives identical records apart from the run time. | 8 |
| FR-24 | Only a Supervisor can issue a QR-sealed copy; an IO can request one (D50). | Issue by a Supervisor succeeds; by an IO or Clerk returns 403; an IO request appears in the Supervisor's queue. | 23 |
| FR-25 | A QR-sealed copy is generated server-side from the sealed stored version, never from an uploaded file, and every issue is logged. | No issue endpoint accepts a file; the issued copy matches the sealed version; one log entry per issue. | 23 |
| FR-26 | The QR payload holds the document ID, version, a short record hash and an Ed25519 signature, and no document content. | Decoding a QR shows only these four items; a changed byte fails the signature check. | 23 |
| FR-PUB-1 | The public verify page needs no login and accepts a QR scan or a photo upload. | A phone browser can scan or upload and get a result. | 23 |
| FR-PUB-2 | The public page shows exactly one of these messages: "This copy matches the sealed record." (Identical or Equivalent); "A critical field was changed." (Tampered, Major); "This copy was changed. No critical field was changed." (Tampered, Minor); "This copy could not be verified. Please use a clearer photo or contact the issuing office." (Inconclusive); "Redacted copies are not supported in this version." (redacted); "This QR code is not valid." (bad signature or unknown record). | Response schema test: the body is one of the six messages and nothing else; no field names, values or locations (D51). | 23 |
| FR-27 | A Court Clerk can verify copies of documents shared with their court and sees full change details, but cannot upload, issue or change anything (D50). | Clerk verify works and shows the change list; every write endpoint returns 403 for a Clerk. | 17, 23 |
| FR-28 | An Auditor can read the transparency log, custody history, signed tree heads and proofs, but not document content or field values. | Auditor log and proof calls succeed; content calls return 403. | 17, 20 |
| FR-29 | A System Admin manages users, roles and settings, and cannot read evidence content or download originals. | Admin content calls return 403 and raise an alert log entry. | 17 |
| FR-30 | Granting Supervisor or Admin roles, releasing a legal hold, bulk export, archive and key access or rotation need a second approver; nobody approves their own request; approvals expire. | Self-approval fails; approval after expiry fails; a valid two-person approval succeeds. | 17 |
| FR-31 | Evidence can never be deleted through any route; only archived. Archived items stay verifiable. A legal hold blocks archive. | Route-list test finds no delete route; archive under legal hold fails. | 21 |
| FR-32 | Every view, download, upload, verify, issue, export and approval writes a custody event (who, what, when, from where, why for sensitive actions) into the transparency log. | Each action produces one log entry with these fields. | 20, 21 |
| FR-33 | The transparency log gives inclusion and consistency proofs and exports a signed tree head daily to a location outside the system. | Proofs verify with a standalone script; the daily export file appears outside the system. | 20 |
| FR-34 | When a document is found Tampered, the tamper window shows the last checkpoint where it was Equivalent, the first where it was Tampered, and every custody event and user between them. | The scripted 3-user scenario shows the correct window and users. | 24 |
| FR-35 | The custody history can be exported per document, listing the sequence of custody events, for use alongside a police report. | Export contains every custody event of the document in order, with signatures. | 21 |
| FR-36 | A signed forensic PDF report can be generated per verdict, with verdict, changes, custody history, hashes, time-stamps, tool and model versions and known error rates. | The report signature verifies; its content matches the database. | 26 |
| FR-37 | A Section 63 draft certificate can be generated, clearly marked "Draft for officer review", pre-filled with the SHA-256 hash value (D66), record details, and date and time in IST. | The draft shows the watermark, the SHA-256 value matches the stored hash, and times are in IST. | 26 |
| FR-38 | Backdating checks flag documents dated before 1 July 2024 that cite BNS, BNSS or BSA sections (allowing for the BNS section 106(2) exception), impossible timelines, and claimed dates far from the RFC 3161 sealing time, each explained in one plain sentence. Built last (D52). | Each rule passes crafted positive and negative cases; the false flag rate on clean samples is measured. | 25 |

## 2. Non-functional requirements

| ID | Requirement | Acceptance test | Phase |
|---|---|---|---|
| NFR-01 | **Target:** verifying a born-digital PDF takes at most 5 seconds per page on the demo laptop CPU (8 cores, 16 GB RAM). | Median and 95th percentile latency measured on the test split. | 15, 27 |
| NFR-02 | **Target:** verifying a scan or phone photo takes at most 15 seconds per page on the same machine. | Latency measured per capture type. | 15, 27 |
| NFR-03 | **Target:** a public verify of a 2-page photo returns a message within 60 seconds. | End-to-end timing on a real phone over the local network. | 23, 27 |
| NFR-04 | **Target:** one-digit edits to critical fields are caught in 100% of clean digital samples (Phase 7 exit). | Measured on the test split. | 7 |
| NFR-05 | **Target:** false alarm rate on Equivalent copies at most 5% for scans and 10% for phone photos; Inconclusive rate at most 15% for photos. Revisited after the baselines (Phase 11), never tuned on the test set. | Measured on the test split and real capture set. | 15, 27 |
| NFR-06 | Upload limits: at most 25 MB per file, 30 pages, 40 megapixels per page image, 200 MB of decompressed PDF streams. | Files over each limit are rejected with a clear message. | 5, 22 |
| NFR-07 | The whole system starts with `docker compose up` and seeded demo data, on a machine with 16 GB RAM. | Fresh-clone run following README only. | 3, 28 |
| NFR-08 | Demo availability: daily backup of PostgreSQL, SeaweedFS and OpenBao; restore within 2 hours, losing at most 24 hours of data. | Restore drill: restore last night's backup on a clean machine, time it, then check every seal, signature and log proof. | 28 |
| NFR-09 | Same input, same output: verdicts are deterministic for a given model, rules and code version. | Re-run test (FR-23). | 8 |
| NFR-10 | All server times are kept in UTC and synchronised by NTP to NIC or NPL servers (CERT-In direction, section 6); the UI and the Section 63 draft show IST. | Log timestamps carry UTC; the health check reports clock offset. | 3 |
| NFR-11 | Logs are kept for at least 180 days on systems inside India (CERT-In direction); the transparency log is append-only and never pruned. | Retention setting documented and checked by the health check. | 20 |
| NFR-12 | The public verify page works on a phone screen 360 pixels wide. | Manual test on a real phone; layout test. | 23, 26 |
| NFR-13 | All UI and documentation text is plain English, short sentences, no em dashes, and never uses the banned words in `CLAUDE.md`. | Automated text check (`tests/docs`). | all |
| NFR-14 | Every library and model is listed in `docs/LICENCES.md`; no chosen component has a restricted or non-commercial licence. | Automated licence table check (`tests/docs`). | 2, all |

## 3. Security requirements

The security target is OWASP ASVS 5.0.0 Level 2 (all L1 and L2 items). Each item's status and phase is in `docs/ASVS_CHECKLIST.md`.

| ID | Requirement | Acceptance test | Phase |
|---|---|---|---|
| SR-01 | All staff use a password and TOTP. | Login with a correct password but no TOTP fails. | 16 |
| SR-02 | Every route checks role and case membership through one shared dependency (deny by default). | Route-list test; IDOR tests for every resource. | 17 |
| SR-03 | Originals are encrypted with AES-256-GCM using a per-document data key; keys live only in OpenBao. | Raw stored objects are unreadable; no key material in code, config or logs. | 18 |
| SR-04 | Integrity is provided by SHA-256, HMAC-SHA-256 fingerprints, Ed25519 signatures and an RFC 6962-style Merkle log, using well-known libraries only. | Signature, proof and tamper tests (T09 to T23). | 5, 19, 20 |
| SR-05 | TLS 1.2 or 1.3 on every external connection; TLS on internal connections to the database, storage and key store. | TLS scan of the nginx endpoint; internal connections refuse plaintext. | 22 |
| SR-06 | Uploads are checked by magic bytes, size and page limits, and ClamAV before intake; infected files are quarantined. | EICAR file is quarantined; a renamed executable is rejected. | 5, 22 |
| SR-07 | Security headers (CSP, HSTS, X-Content-Type-Options, frame-ancestors, Referrer-Policy), CSRF protection and rate limits on login, upload and public verify. | Header and rate-limit tests. | 22 |
| SR-08 | CI runs pytest, Bandit, Semgrep, pip-audit, npm audit and gitleaks on every push. | CI log shows all scanners. | 3 |

## 4. Security documentation (ASVS documentation items)

These sections are the documentation that ASVS asks for. The checklist marks the matching items as done in Phase 2. The controls themselves are built in the phases listed.

### 4.1 Input validation rules (ASVS V2.1.1)

| Input | Rule |
|---|---|
| Uploaded file | Type by magic bytes: PDF (`%PDF-`), PNG, JPEG, TIFF only. Extension must match the detected type. Limits in NFR-06 |
| Case number, document ID, version | Server-generated IDs only (UUID or integer); client values are looked up, never trusted |
| Free text from users (reason for an action, search text) | UTF-8, at most 500 characters, control characters removed, stored as data, never used to build queries, paths or commands |
| Dates in requests (search ranges) | ISO 8601, between 2024-01-01 and today plus one day |
| QR payload | Fixed schema: document ID, version, short record hash, signature; base64url; at most 512 bytes; anything else is "This QR code is not valid." |
| Username | 3 to 64 characters, letters, digits, dot, hyphen, underscore |
| Password | 12 to 128 characters, any characters (ASVS V6.2.5), never changed or trimmed before checking |
| TOTP code | Exactly 6 digits |

### 4.2 Consistency rules for combined data (ASVS V2.1.2)

- A document version always belongs to exactly one case; a verify request must name a version of a document the user can access.
- An approval request names one action, one target and one requester; the approver must be a different user with the right role.
- A legal hold and an archive request cannot both be active on the same document.
- Extracted field values are checked for internal consistency only by the backdating rules (FR-38). The intake does not reject a document for inconsistent dates, because the system must store evidence as received.

### 4.3 Business logic limits (ASVS V2.1.3)

| Limit | Per user | Across the system |
|---|---|---|
| Uploads | 60 per hour | Queue depth 500 jobs |
| Staff verifications | 120 per hour | Shared queue limit above |
| Public verifications | 10 per IP address per hour | 200 per hour |
| Login attempts | 5 failures per account in 15 minutes, then a 15-minute lockout | 30 attempts per IP address per minute |
| QR-sealed copy issues | 50 per Supervisor per day | none |
| Bulk export | Only with two-person approval | one running at a time |
| Approval request lifetime | 24 hours | n/a |

### 4.4 File handling (ASVS V5.1.1)

Permitted types: PDF, PNG, JPEG, TIFF (multi-page TIFF up to 30 pages). Extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`. Maximum size: 25 MB per file; 200 MB of decompressed content per PDF; 40 megapixels per page image. Files are made safe by: magic-byte check, ClamAV scan, storing under a server-generated name (never the user's file name), encryption before storage, and serving downloads with `Content-Disposition: attachment` and a server-chosen name. Archives (zip and similar) are not accepted.

### 4.5 Authentication defences (ASVS V6.1.1, V6.1.2, V6.1.3)

- **Defences against credential stuffing and brute force:** account lockout and per-IP limits from section 4.3; TOTP for every staff account; generic login error messages; every failure logged.
- **Context-specific words that cannot be used in passwords:** pramaan, pramaandms, pramaan-dms, police, policestation, fir, chargesheet, charge-sheet, statement, court, clerk, auditor, supervisor, admin, administrator, password, sih26190, mha, bmsit, and the user's own username, name and officer ID, in any letter case.
- **Authentication pathways:** there is one pathway for staff: username, password and TOTP. Recovery: an Admin can reset a password only with a Supervisor's second approval, and the user must enrol TOTP again. The public page has no login. Service accounts between containers use separate credentials and never log in through the UI.

### 4.6 Sessions (ASVS V7.1.1, V7.1.2)

- Idle timeout: 15 minutes. Absolute lifetime: 8 hours (one duty shift). Justification: evidence systems are used on shared station computers, so short idle time matters more than convenience.
- Concurrent sessions: at most 2 per account (for example office desktop and court laptop). A third login ends the oldest session, and the user is told.

### 4.7 Communication needs (ASVS V13.1.1)

| From | To | Purpose | Allowed |
|---|---|---|---|
| Browser | nginx | UI, API, public verify | HTTPS 443 only |
| nginx | API, UI | Proxy | Internal network |
| API, worker | PostgreSQL | Records | Internal network, TLS |
| API, worker | SeaweedFS (S3) | Encrypted originals | Internal network, TLS |
| API, worker | OpenBao | Keys and signing | Internal network, TLS |
| API, worker | Valkey | Job queue | Internal network, password |
| Worker | ClamAV (clamd) | Virus scan | Internal network socket |
| API | RFC 3161 TSA (FreeTSA in the demo, D64) | Time-stamps | Outbound HTTPS to the configured URL only |
| Export job | Outside tree head location | Daily signed tree head | Outbound to one configured target |
| All servers | NTP (NIC or NPL) | Time sync | Outbound NTP |

No other outbound connections. Models are loaded from the local signed registry, never downloaded at run time. Users can never make the server fetch a URL they provide.

### 4.8 Data classification and protection (ASVS V14.1.1, V14.1.2)

| Level | Data | Protection |
|---|---|---|
| Secret | Keys, OpenBao tokens, password hashes, TOTP seeds, backup codes | Only in OpenBao or hashed; never logged; two-person rule for key access |
| Evidence (high) | Original files, extracted text, field values, narrative, change values | Encrypted at rest with a per-document key; case-level access; never in logs, URLs or public responses; never deleted, only archived |
| Personal (medium) | Staff names, usernames, officer IDs, roles | Access by role; shown to Auditors only as actor names in logs |
| Integrity metadata (low) | SHA-256 values, HMAC fingerprints, signatures, log entries without content, verdict labels | Signed and logged; HMAC keeps short values from being guessed; fingerprint records are not sent to the public |
| Public | The six public messages, the public signing key, this documentation | No restriction |

### 4.9 Third-party components (ASVS V15.1.1)

Dependencies are pinned. CI runs pip-audit and npm audit on every push and weekly. Remediation time frames from the date a fix is available: critical within 7 days, high within 30 days, medium within 90 days, low at the next planned update. A component past its time frame blocks the next milestone gate.

### 4.10 Resource-heavy functions (ASVS V15.1.3)

| Function | Why heavy | Control |
|---|---|---|
| OCR and Legal Hash pipeline | CPU and memory per page | Background queue, page and pixel limits, per-task time and memory limits |
| Public verify | Anonymous, runs the full pipeline | Per-IP and global rate limits, bounded queue, 60-second timeout |
| Forensic report and Section 63 draft generation | PDF rendering | Per-user rate limit; generated once and stored |
| Bulk export | Large reads | Two-person approval; one at a time |
| Log consistency checker | Reads the whole log | Scheduled, incremental from the last checked tree head |
| Custody search | Large date ranges | Pagination and query timeouts |

## 5. Data and privacy

- The project uses synthetic data only. No real FIRs, persons or cases (D34).
- The system is designed in line with the security safeguard duty of DPDP Act section 8(5) even for investigation data (see section 6). Personal data inside documents is Evidence level (section 4.8).
- Data is kept only on the demo machine. No analytics, trackers or third-party scripts in the UI.

## 6. Legal context

All items below were checked on 16 October 2026 against official texts (India Code, the Gazette copies hosted by MHA, MeitY, CERT-In, PIB). Headings are quoted as printed. Nothing here is legal advice. The system produces drafts for officer review and makes no claim about admissibility.

| Topic | What the official text says | How it shapes Pramaan | Source | Verified |
|---|---|---|---|---|
| New criminal laws in force | BNS (S.O. 850(E)), BNSS (S.O. 848(E)) and BSA (S.O. 849(E)), all dated 23 February 2024, appoint 1 July 2024 as commencement; BNS section 106(2) and its BNSS First Schedule entry are excepted | Backdating rule date (FR-38, D26) | https://www.mha.gov.in/sites/default/files/BhartiyaNyayaSanhita_24022024.pdf, https://www.mha.gov.in/sites/default/files/BharatiyaNagarikSurakshaSanhita_24022024.pdf, https://www.mha.gov.in/sites/default/files/BharatiyaSakshyaAdhiniyam_24022024.pdf | yes |
| BSA 2023, section 63 | "Admissibility of electronic records." Section 63(4) needs a certificate signed by a person in charge of the device or activity and an expert. The Schedule form "[See section 63(4)(c)]" asks for hash values with options "SHA1", "SHA256", "MD5" and "Other (Legally acceptable standard)", and says "(Hash report to be enclosed with the certificate)". It has Part A (party) and Part B (expert), with date, "Time (IST)" and place | Section 63 draft (FR-37) is pre-filled with SHA-256 only (D66), IST time, and stays a draft for the officer and expert to complete | https://www.mha.gov.in/sites/default/files/2024-04/250882_english_01042024_0.pdf | yes |
| BSA 2023, sections 57, 61, 62 | 57: "Primary evidence." 61: "Electronic or digital record." 62: "Special provisions as to evidence relating to electronic record." | Context for treating stored originals as electronic records | https://www.mha.gov.in/sites/default/files/2024-04/250882_english_01042024_0.pdf | yes |
| BSA 2023, section 170 | "The Indian Evidence Act, 1872 is hereby repealed", with a saving for matters pending before commencement | Section 65B of the Evidence Act applies only to pending older matters; new matters use BSA section 63. The exact wording of 65B was not checked (TODO: verify) | https://www.mha.gov.in/sites/default/files/2024-04/250882_english_01042024_0.pdf | yes (65B wording: no) |
| BNSS 2023, section 173 | "Information in cognizable cases." Information "may be given orally or by electronic communication"; electronically given information is taken on record when signed within three days by the informant | Intake must accept born-digital PDFs as well as scans | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | yes |
| BNSS 2023, section 180 | "Examination of witnesses by police." A proviso allows recording "by audio-video electronic means" | Witness statements are in scope as documents; audio and video are out of scope (SCOPE.md) | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | yes |
| BNSS 2023, section 193 | "Report of police officer on completion of investigation." The report may be forwarded through electronic communication and must state "the sequence of custody in case of electronic device" | Custody history export (FR-35) | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | yes |
| BNSS 2023, section 105 | "Recording of search and seizure through audio-video electronic means." | Context only; media evidence is out of scope | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | yes |
| IT Act 2000, sections 3, 3A, 4 | 3: "Authentication of electronic records." 3A: "Electronic signature." 4: "Legal recognition of electronic records." | Our Ed25519 seals are system integrity signatures, not digital or electronic signatures under these sections (SCOPE.md) | https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf | yes |
| IT Act 2000, sections 43, 43A, 65, 66, 72, 72A | 43: "Penalty and compensation for damage to computer, computer system, etc." 43A: "Compensation for failure to protect data." 65: "Tampering with computer source documents." 66: "Computer related offences." 72: "Penalty for Breach of confidentiality and privacy." 72A: "Punishment for disclosure of information in breach of lawful contract." | Motivates access control, audit logs and confidentiality controls; the system does not decide whether an offence happened | https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf | yes |
| DPDP Act 2023 | Act No. 22 of 2023, dated 11 August 2023. Section 8: "General obligations of Data Fiduciary." Section 17: "Exemptions." Section 17(1)(c) covers processing "in the interest of prevention, detection, investigation or prosecution of any offence"; the exemption does not cover section 8(1) and 8(5) (reasonable security safeguards). Section 44(2)(a) omits IT Act section 43A | Security safeguards apply even to investigation data, so the design follows them (section 5) | https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf | yes |
| DPDP commencement | G.S.R. 843(E), 13 November 2025, brings the Act into force in three phases: some sections at once, some after one year, and sections 3 to 17 (including 8 and 17) and 44(2) after eighteen months. Rules: G.S.R. 846(E), same date, also phased | On 16 October 2026, sections 8 and 17 are not yet in force (by our arithmetic, about May 2027). We follow section 8(5) anyway | https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf, https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf | yes (end dates are our arithmetic) |
| CERT-In Directions, 28 April 2022 | Under IT Act section 70B(6): connect to the NTP server of NIC or NPL (or traceable to them) for clock sync; keep logs of ICT systems for a rolling 180 days within Indian jurisdiction; report incidents within 6 hours | NFR-10 (time sync), NFR-11 (log retention) | https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf | yes |

## 7. Traceability

| Requirement group | Threats covered |
|---|---|
| FR-01 to FR-06 (intake and sealing) | T02, T09, T10, T11, T46, T47, T52 |
| FR-07 to FR-23 (verification rules) | T28, T38, T41, T57, T58, T59 |
| FR-24 to FR-27, FR-PUB (QR-sealed copies and public page) | T29 to T34, T48 |
| FR-28 to FR-35 (roles, approvals, custody, log) | T03, T04, T06, T14, T18 to T23, T43 to T45, T49 |
| FR-36 to FR-38 (reports, Section 63 draft, backdating) | T47, T56 |
| SR-01 to SR-08 | T01, T05, T07, T08, T11, T12, T16, T24 to T27, T50, T53 to T55 |
| NFR-10, NFR-11 (time and logs) | T51 |
