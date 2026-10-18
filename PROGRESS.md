# Progress Tracker

Update this at the end of every phase.

## Status

| Phase | Name | Status | Date done | Notes |
|---|---|---|---|---|
| 1 | Scope, tampering definition, literature, novelty | Partly done | | All 5 docs done and synced to the locked decisions (2026-10-16). Field list agreed via locked decisions (D55). Waiting on: 10-citation spot-check. Git skipped (D28) |
| 2 | Threat model, requirements, licences | Done | 2026-10-16 | All 4 exit criteria met and checked by 256 automated doc tests. Human items listed in the log |
| 3 | Project setup | Partly done | | Everything built and tested locally (384 tests, CI script 9 of 9 steps). Not met yet: Docker stack healthy, GitHub CI run, fresh-clone run (no Docker here; git paused) |
| 4 | FIR-Tamper dataset v1 | Partly done | | Tools done. dataset_v2 (teammate) audited: not usable for training. **v3 Stage 2 built 2026-10-18** (`dataset_v3/`, 230 bases, 19,680 samples, E0 to E19, held-out test_unseen split): validator PASS, QA PASS, audit 18 of 18, split hashes in `docs/DATASET.md`, 644 tests pass. Open: human 10% re-check, real and harder captures (Phase 10), 1,000-originals target (D95 sets 230) |
| 5 | Evidence intake (basic) | Partly done | | Built and tested without Docker (560 tests pass, 9 Docker tests skip; CI script 9 of 9). Exit criteria met on mocks; PostgreSQL, SeaweedFS Object Lock and the full upload are built, unverified until Docker. Phase 4 dataset items carried to the teammate |
| 6 | OCR pipeline | Not started | | |
| 7 | Fact check (field fingerprint) | Not started | | |
| 8 | Verify v1 | Not started | | |
| 9 | Basic UI (working demo milestone) | Not started | | |
| 10 | Real capture set and augmentation | Not started | | |
| 11 | Baselines | Not started | | |
| 12 | Narrative hash model | Not started | | |
| 13 | Smarter field extraction | Not started | | |
| 14 | Stamp and signature check | Not started | | |
| 15 | Final verdict logic and model integrity | Not started | | |
| 16 | Authentication | Not started | | |
| 17 | Access control and insider controls | Not started | | |
| 18 | Encryption and keys | Not started | | |
| 19 | Sealing | Not started | | |
| 20 | Transparency log | Not started | | |
| 21 | Chain of custody, legal hold, archive | Not started | | |
| 22 | App hardening | Not started | | |
| 23 | QR certificate | Not started | | |
| 24 | Tamper window | Not started | | |
| 25 | Backdating checks | Not started | | |
| 26 | Reports and UI polish | Not started | | |
| 27 | Evaluation and security testing | Not started | | |
| 28 | Wrap up | Not started | | |
| S | Contradiction check (stretch) | Not started | | |

## Phase log

(Add an entry per phase: what was built, how to run it, test results, known issues, what's next.)

### Phase 1: Scope, tampering definition, literature, novelty (2026-10-14, partly done)

**Built (documents only, no code):**

| File | What it is |
|---|---|
| `docs/SCOPE.md` | Problem, 6 roles (can and cannot see), document types, languages, in and out of scope (10 new out-of-scope items), assumptions |
| `docs/TAMPERING_DEFINITION.md` | Exact definitions of the 4 verdicts, severity rule, the "reworded is Altered" principle, decision rules R1 to R7, 41 worked examples, 18 open questions (E1 to E18) |
| `docs/CRITICAL_FIELDS.md` | 27 fields with type, criticality, document types, English and Hindi labels and normalization rule; 8 rows added with reasons; one example per type |
| `docs/LITERATURE.md` | 79 verified sources under 12 headings, gap table, 13 unverified sources listed separately |
| `docs/NOVELTY.md` | Gap in 3 sentences, 5 contributions (new vs reused), 3 research questions, 6 hypotheses with metrics, negative result plan |

**Counts:**
- Worked examples: 41 (target 25+)
- Sources verified: 79, of which 45 on a primary page (publisher, arXiv, ACL Anthology, RFC Editor, NIST, official government or ISO page) and 34 from the DOI registry record plus an abstract index, because publisher sites blocked automated access
- Sources unverified (not cited): 13
- Fact check: the BNS, BNSS and BSA commencement date (1 July 2024, BNS section 106(2) excepted) was confirmed from MHA-hosted copies of Gazette notifications S.O. 848(E), 849(E) and 850(E)

**How it was checked:** citations were found by web search and confirmed by opening pages. Banned-word scan and em dash scan on all docs: clean.

**Exit criteria:**
- [x] All five docs written and saved. Commit skipped by owner decision (D28)
- [x] Every cited source verified; unsure items marked `TODO: verify` or moved to the unverified list
- [x] Research gap stated in 3 sentences (`NOVELTY.md` section 1)
- [ ] Critical field list agreed by the team (waiting on owner)
- [ ] Team member spot-checks 10 citations in a browser (waiting on owner). Suggest choosing mostly entries marked (R)

**Not done, needs the owner:**
1. `PHASES.md` says Phase 1 makes four docs; `BUILD_PLAN.md` lists five. Not fixed yet (owner asked to hold)

**Owner decisions on 2026-10-15:**
- `PROJECT_BRIEF.md` is the agreed scope. The check against the official SIH26190 text is skipped and its TODO removed from `SCOPE.md` (D27). `PROBLEM_STATEMENT.md` itself is unchanged
- Git steps skipped for now. Files are saved only. `git init` was done on `main`; nothing is committed and no `phase-01` branch exists (D28)

**Open questions for the owner:**
- `SCOPE.md` Q2 to Q4 (name for the QR copy, clerk upload rights, field names on the public page). Q1 resolved by D27
- `TAMPERING_DEFINITION.md` E1 to E18. Most important: E1 (Inconclusive can hide a clear edit), E3 (spacing), E5 (negation and narrative numbers labelled Minor), E6 and E7 (page changes), E8 (allowed annotations), E15 (redacted copies)
- `CRITICAL_FIELDS.md` Q1 to Q6 (honorifics, list order, narrative entities as F fields, address criticality, who collects Hindi forms)

**Known issues:**
- 19 `TODO: verify` items in `CRITICAL_FIELDS.md`, mostly Hindi labels, need real blank Hindi forms
- Surya OCR model weights use a modified AI Pubs Open Rail-M licence with commercial limits (seen on its README). Must be decided in Phase 2 against the no-non-commercial rule. PaddleOCR may be the safer choice
- Novelty claims ("not found in our search") are limited to the 79 sources and must be rechecked with a wider search before the paper

**Next:** owner answers the open questions, agrees the field list and does the citation spot-check. Phase 2 must not start until Phase 1 exit criteria are all ticked.

### Dataset task: FIR-Tamper v0, English (2026-10-15, part of Phase 4)

Done on the owner's request, before Phases 2 and 3. Phase 1 exit items (field list agreement, citation spot-check) were still open; the owner's task treated the 27-field list as agreed.

**Built:**

| Path | What it is |
|---|---|
| `ml/data/generator/` | Generator: invented data (`fakedata.py`), document model and print formats (`model.py`), narrative templates (`narrative.py`), base documents (`generate.py`), page layout and PDF drawing (`render.py`), 40 tamper and format classes (`tamper.py`), label computation (`labels.py`), simulated scan and photo (`capture.py`), build script (`build.py`), QA checks (`check.py`) |
| `tests/ml/test_dataset_generator.py` | 11 tests: same seed gives identical files, text layer agrees with labels, no real personal data, split by base document, every class gives its declared verdict on all 3 document types, page-removed severity, display formats, one-digit edits |
| `dataset/` | The built dataset: `base_docs/`, `tampered/`, `captures/`, `labels.csv`, `labels.json`, `splits/`, `manifest.json`, `qa/`, `README.md`, `templates/` |
| `docs/DATASET.md` | Dataset card with split hashes and Phase 4 exit status |
| `docs/LICENCES.md` | Started: libraries used by the generator, plus items flagged for Phase 2 |
| `ml/requirements-data.txt`, `.gitignore` | Pinned libraries; generated dataset folders ignored |

**How to run:**
```
.venv/Scripts/python -m pip install -r ml/requirements-data.txt
.venv/Scripts/python -m ml.data.generator.build --out dataset      (about 20 minutes with captures)
.venv/Scripts/python -m ml.data.generator.check --data dataset
.venv/Scripts/python -m pytest tests/ml
```

**Results (real runs, seed 20261015):**
- 60 base documents (24 FIR, 21 charge sheet, 15 statement), 900 versions, 2,700 samples, about 1.6 GB
- Split by base document: 42 / 9 / 9 documents (1,890 / 405 / 405 samples)
- 40 classes, every class in every split (2 to 22 versions per class per split)
- 33.3% of samples untouched or format-only
- Expected verdicts: Altered 1,680, Equivalent 840, Identical 60, Inconclusive 120
- QA: 0 label mismatches, 0 text-layer failures (860 PDFs read back), 0 personal-data problems, 0 split leaks
- Same seed built twice: identical dataset hash `fc5b2955...819d`
- pytest: 11 passed

**Bugs found and fixed during the build:**
- Pillow's PDF writer stamped the current time into files, which broke byte-identical rebuilds. Switched to ReportLab invariant mode (D37)
- A one-digit edit to a phone number could change the "10" prefix and produce a real-looking mobile number. The personal-data test caught it. Phone edits now leave the prefix alone
- Field boxes were split per word. Fixed so a multi-word value has one box per line

**Known issues and gaps:**
- Human 10% re-check not done: `dataset/qa/recheck_10pct.csv` (270 samples) needs a second person
- All base documents are 2 pages, so a removed page is always Critical; the Minor case of E6 is not covered
- Scan and photo are simulated, not real (D33)
- Not in v0:
  - Hindi
  - Devanagari digits
  - homoglyphs
  - zero-width characters
  - pen edits
  - partial captures
  - transliteration
  - QR swap
  - accused statements
- No official charge sheet or statement form could be downloaded. The FIR layout follows the field order of Meghalaya Police Circular 03/2024 Annexure-1 (`dataset/templates/SOURCES.md`)
- BNS section numbers are example values, their mapping to offences is not verified (D38)
- Labels for E1, E4, E5, E6, E7, E8, E15, Q3, Q4, Q5 follow the current drafts and are tagged; they change if the owner decides differently (D31)
- Phase 4 exit criteria not met (1,000 originals, 5,000 pairs, Hindi). Phase 4 stays open

### Phase 2: Threat model, requirements, licences (2026-10-16, done)

**Step 0: docs synced to the decisions locked before Phase 2 (D39 to D56).** English only; verdicts Identical, Equivalent (Format), Tampered (Major or Minor), Inconclusive; a clear edit beats unreadable fields; negation, page changes, narrative entities and section add or remove are Major; name order is Minor; honorifics stripped for matching; spacing rule by value type; annotations rule; redacted copies rejected; clerks verify only; Supervisors issue QR-sealed copies; public page shows one fixed message; backdating built last. Updated: `docs/TAMPERING_DEFINITION.md` (rewritten, 51 examples), `docs/CRITICAL_FIELDS.md` (rewritten, Hindi column removed, narrative entities added), `docs/SCOPE.md`, `docs/NOVELTY.md`, `docs/LITERATURE.md` (gap table Hindi column removed), `LEGAL_HASH_SPEC.md`, `PROJECT_BRIEF.md`, `ARCHITECTURE.md`, `PHASES.md`, `BUILD_PLAN.md` (dependency map: P26 -> P25 -> P27), `SECURITY_FORENSICS.md`. Not touched: `dataset/` and `docs/DATASET.md` (owned by the dataset teammate, D56).

**Built:**

| File | What it is |
|---|---|
| `docs/THREAT_MODEL.md` | Assets, actors, trust boundaries, 59 threats (STRIDE per component plus insider, AI and verification groups), each with mitigation, phase and test idea; component x STRIDE coverage matrix; accepted residual risks |
| `docs/REQUIREMENTS.md` | 40 functional, 14 non-functional and 8 security requirements, each with an acceptance test and phase; ASVS documentation sections 4.1 to 4.10; data and privacy; legal context checked against official texts; traceability to threats |
| `docs/LICENCES.md` | 67 components with licence, commercial use, how used, status and source, all checked on official pages on 16 October 2026 |
| `docs/ASVS_CHECKLIST.md` | OWASP ASVS 5.0.0 Level 2: all 253 L1 and L2 items with status and phase (Done 14, Planned 168, Not applicable 69, Accepted gap 2), generated from the official CSV |
| `docs/asvs/OWASP_ASVS_5.0.0_en.csv`, `docs/asvs/asvs_l2_status.json` | Official ASVS list (CC BY-SA 4.0) and our status file |
| `tools/asvs_checklist.py` | Generates and checks the ASVS checklist; refuses incomplete or invalid input |
| `tests/docs/test_phase2_docs.py` | 256 automated checks of the Phase 2 exit criteria and of the locked rules in the worked examples |
| `docs/NOVELTY.md` section 6 | Paper-worthy points: what is new, what is measured, compared against what |
| `DECISIONS.md` D39 to D66 | Locked decisions and Phase 2 design decisions with reasons |

**Stack changes forced by the licence check:** OpenBao instead of HashiCorp Vault (BUSL-1.1), SeaweedFS instead of MinIO (repository archived, no longer maintained), Valkey instead of Redis (RSALv2/SSPLv1), PaddleOCR and Tesseract instead of Surya (weights restricted), segno and pyzbar for QR, PyMuPDF avoided (AGPL), ssdeep for evaluation only (GPL). SeaweedFS Object Lock (compliance mode, legal hold) confirmed on its official wiki; Phase 5 must test it.

**How to run the checks:**
```
.venv/Scripts/python tools/asvs_checklist.py --check
.venv/Scripts/python -m pytest tests
```
Result on 2026-10-16: `267 passed` (256 Phase 2 doc tests plus 11 dataset generator tests).

**Exit criteria:**

| Exit criterion | Result | Evidence |
|---|---|---|
| STRIDE table covers all components plus the 3 special groups | Met | `test_coverage_matrix_has_every_component_and_stride_cell`, `test_special_groups_are_covered` (insider 7, AI 10, verification 7) |
| Every threat mapped to a phase | Met | `test_every_threat_is_complete_and_mapped_to_a_phase` (59 rows) |
| Every requirement testable | Met | `test_every_requirement_is_testable_and_phased` (62 requirements) |
| No licence blockers | Met | `test_no_licence_blockers` (67 rows), `test_rejected_components_are_not_in_the_architecture` |
| Definition of done: new decisions in DECISIONS.md, libraries in LICENCES.md | Met | D39 to D66; LICENCES.md |
| Definition of done: merged from a phase branch, `docker compose up` still works | Not applicable yet | Git paused (D28); no Compose until Phase 3 |

**Needs a human (not ticked):**

| Item | Suggested owner |
|---|---|
| Relabel the dataset to the locked rules: `B_BLUR_PLUS_EDIT` becomes Tampered with a "could not verify" list; `N_NEGATION`, `N_ENTITY`, `P_PAGE_ADDED`, `P_PAGE_REORDER` become Major; `R_REDACTED` becomes "not supported" (no verdict); all "Altered" become "Tampered" and "Critical" become "Major"; `A_MARGIN_NOTE` gets a flag; remove Hindi from `docs/DATASET.md` | Dataset teammate (ML and Legal Hash) |
| Spot-check 10 citations in `docs/LITERATURE.md` (Phase 1) | Frontend, reports and docs |
| Read the legal context table (REQUIREMENTS.md section 6) against the linked official PDFs; open the Indian Evidence Act 1872 for the exact section 65B wording (TODO: verify) | Security and forensics |
| Peer review of THREAT_MODEL.md and REQUIREMENTS.md by a second teammate (BUILD_PLAN "anyone can review"; not a gate, D54) | Security and forensics |
| Confirm each PaddleOCR model file's licence when downloaded | ML and Legal Hash (Phase 6) |

**Known issues:**
- DPDP Act sections 8 and 17 are not yet in force (phased commencement from 13 November 2025; about May 2027 by our arithmetic). The design follows section 8(5) anyway.
- Two ASVS items are accepted gaps for the demo: V12.2.2 (self-signed certificate) and V16.4.3 (no full log shipping; tree heads exported instead).
- FreeTSA publishes no terms or SLA; demo only (D64).

### Phase 3: Project setup (2026-10-16, partly done)

**Gate check:** Phase 2 exit criteria all met with test evidence; full suite passed (267) before starting. Carried forward because Phase 3 does not depend on them: dataset relabelling, 10-citation spot-check, legal table re-read, threat model peer review, PaddleOCR model licences.

**Built:**

| Path | What it is |
|---|---|
| `app/main.py`, `app/config.py`, `app/logs.py`, `app/health.py`, `app/health_cli.py`, `app/db.py`, `app/worker.py`, `app/version.py` | FastAPI skeleton: validated settings from env (placeholders and weak secrets refused, secrets never shown), JSON logs in UTC with request IDs and redaction, generic error responses, `/health/live` and `/health` (PostgreSQL, Valkey, SeaweedFS, OpenBao, ClamAV, in parallel with timeouts), Celery worker with JSON-only messages |
| `app/<module>/`, `ml/train`, `ml/eval`, `ml/registry` | Module layout from ARCHITECTURE.md, each package naming the phase that builds it |
| `alembic.ini`, `migrations/` | Alembic with an empty first revision `0001`, run as the schema owner |
| `docker/postgres/init/01-roles.sh` | Least-privilege roles: `pramaan_owner` (migrations), `pramaan_app` (runtime) |
| `docker/api.Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` | Pinned base images, non-root users, nginx proxy that hides `/api/health` and the server version |
| `docker-compose.yml` | 8 services with health checks plus a one-shot `migrate` job; internal network; only the frontend published (127.0.0.1); required secrets; hardened app containers |
| `.env.example`, `tools/setup_env.py` | Placeholder template and the generator for `.env` and `docker/secrets/` |
| `frontend/` | React 19 + TypeScript + Vite 8 skeleton page with service status, 5 Vitest tests, pinned and locked dependencies |
| `tools/ci.py`, `.github/workflows/ci.yml`, `.gitleaks.toml` | One CI script for local and GitHub runs; actions pinned to SHAs; gitleaks checksum-verified |
| `requirements.txt`, `requirements-dev.txt` | Pinned Python dependencies |
| `tests/app/` (44), `tests/infra/` (60) | Settings, logging, API, health checks, worker, migrations, roles script, Compose, setup script, CI config, layout |
| Docs | `README.md` (run steps), `docs/LICENCES.md` (new components and images), `docs/ASVS_CHECKLIST.md` (23 Done), `docs/NOVELTY.md` (P9), `BUILD_PLAN.md` (stack and Node lines), `DECISIONS.md` D67 to D75 |

**How to run:** see `README.md` ("Run it" and "Develop and test").

**Test results (16 October 2026):**
- `pytest tests`: 384 passed (Phase 1 and 2 doc tests, dataset tests, and the new Phase 3 tests). One warning: Starlette's test client warns that its httpx support is deprecated.
- `python tools/ci.py`: 9 of 9 steps passed (pytest, ASVS check, frontend tests 5/5, frontend build, Bandit, Semgrep with 271 rules over 50 files and 0 findings, pip-audit, npm audit with 0 vulnerabilities, gitleaks). gitleaks still detects a planted test key.
- Real server smoke test: uvicorn started, `/health/live` returned 200 with a request ID, `/health` returned 503 naming each unreachable service, logs were JSON.

**Exit criteria:**

| Exit criterion | Result | Evidence |
|---|---|---|
| `docker compose up` brings all 8 containers to healthy | Not met | Docker is not installed on this machine. Static checks pass (`tests/infra/test_compose.py`: 8 services, health checks, pinned images, networks, secrets) and every image's health command was checked against its official source, but the stack has not run |
| `/health` returns OK | Not met | The endpoint works in-process (`tests/app/test_api.py`) and on a real server (returns 503 without services). "OK" needs the real services, so it needs Docker |
| CI passes with all security scanners running | Not met | The identical script passes locally, 9 of 9 steps. GitHub Actions has not run: git is paused (D28) and there is no remote |
| A fresh clone runs by following README alone | Not met | Needs git (clone) and Docker |

**Needs a human:**

| Item | Suggested owner |
|---|---|
| Install Docker Desktop (or Docker Engine in WSL), then run: `python tools/setup_env.py`, `docker compose up -d --build --wait`, `docker compose ps` (8 healthy), `docker compose exec api python -m app.health_cli` (exit 0). Report the output so the first two criteria can be ticked | Integration and backend |
| Turn git back on (D28), make the first commit, push to the private GitHub repo, and confirm the Actions run is green | Integration and backend |
| Fresh-clone test on a second machine following README only | Any teammate |
| Carried forward: dataset relabelling, citation spot-check, legal re-read, threat model peer review, PaddleOCR model licences | As listed in Phase 2 |

**Known issues:**
- Exit criteria above wait on Docker and git.
- During the smoke test a broad `taskkill` was used to stop the test server; it may also have closed other Python windows open at that time. No Python processes were running afterwards.
- Semgrep cannot share the app's environment (it downgrades a FastAPI dependency); it runs from its own environment (D68).
- Git commit is due once git is re-enabled (D28).

### Phase 4: FIR-Tamper dataset tools (2026-10-16, partly done)

**Gate check:** Phase 1 and 2 criteria met; `tools/ci.py` 9 of 9 after fixing one gitleaks false positive I introduced at the end of Phase 3 (the Valkey image name in the new LICENCES.md image table; the allowlist pattern now allows trailing whitespace, and a planted test key is still detected). Phase 3 stays open (Docker, GitHub CI, fresh clone).

**Scope (D76):** Phase 4 in PHASES.md is the dataset. The dataset in `dataset/` belongs to the dataset teammate (D56), so this session built the tools only. Nothing in `dataset/` or `docs/DATASET.md` was created or edited. **Docker split:** every Phase 4 item is pure logic (group A); there is no group B, so nothing here is "unverified until Docker" and no test is skipped for lack of Docker.

**Built:**

| Path | What it is |
|---|---|
| `ml/data/generator/labels.py` (rewritten) | Labels by the locked rules: Not supported for redacted copies (D47); a clear edit is Tampered with unreadable fields listed as "could not verify" (D41); Inconclusive only without a clear edit; Major for critical fields, sections added or removed, narrative entities, negation flips, page changes, stamps and signatures, notes over critical fields; Minor for wording, name order, the address field and margin notes (flagged) |
| `ml/data/generator/tamper.py` | 46 classes (10 new, D78), each tied to its worked example and decision |
| `ml/data/generator/model.py`, `narrative.py`, `render.py`, `build.py`, `check.py` | Honorifics stripped for matching (D48); IDs with an inner space print as tampered; complainant and witness names are narrative entities (D79); entity-bearing sentences; note over a field; Courier label fix (D81); new label columns `could_not_verify`, `flagged`, `rule_ref` |
| `ml/data/validate_labels.py` | Validator for any labels.csv: schema, values, locked rules (SEV, D41, D43, VIS, D46, D47, IDENT, TASK), class table, captures of one version, splits and leakage, files, split hashes; optional 10% re-check sample; read-only on the data |
| `tests/ml/test_locked_rules.py`, `tests/ml/test_validate_labels.py` | Locked-rule tests with a clean negative and a tampered case per rule, class vs worked example cross-check, every validator error kind, a generated dataset end to end |
| `tests/fixtures/labels_fixture/` | Hand-written 15-row labels.csv, marked as a test fixture (FIXTURE_README.txt), not part of the dataset |
| Docs | `DECISIONS.md` D76 to D81, `docs/NOVELTY.md` P10, `README.md` dataset tool commands |

**How to run:**
```
.venv/Scripts/python -m ml.data.generator.build --out <folder> [--no-captures]
.venv/Scripts/python -m ml.data.validate_labels --data <folder> --report <file> --sample-out <file>
```

**Test results (16 October 2026):** `tools/ci.py` 9 of 9 steps passed; pytest 484 passed, 0 skipped, 0 failed. Trial build (12 base documents, no captures): 0 label mismatches, 0 text-layer failures, 0 personal-data problems; validator PASS with all 3 split hashes matching; same seed rebuilds byte-identical (existing test). The validator, run read-only on the current `dataset/` (v0, labelled before the locked rules), reports FAIL with 1,860 errors: 1,680 rows using the old terms "Altered"/"Critical", 60 blur-plus-edit rows that should be Tampered, 120 rows contradicting the class table. No split leakage.

**Exit criteria (Phase 4):**

| Exit criterion | Result | Evidence |
|---|---|---|
| Dataset generated reproducibly from a seed | Not met for the dataset; met for the tools | `test_same_seed_gives_identical_files` (generator). The real dataset has not been regenerated with the new rules (teammate) |
| Labels validated on a sample | Not met for the dataset; validator built | `tests/ml/test_validate_labels.py`; current `dataset/` fails validation (old labels). The human 10% re-check is not done |
| Split hashes saved | Not met for the dataset | Validator recomputes and compares split hashes (`test_generated_dataset_validates_with_hashes`); the teammate's rebuild must record new hashes in `docs/DATASET.md` |

**Needs a human:**

| Item | Suggested owner |
|---|---|
| Regenerate the dataset with the updated generator (`--out dataset`), then run the validator until it reports PASS | Dataset teammate (ML and Legal Hash) |
| Human re-check of the 10% sample from `--sample-out` | A second teammate |
| Update `dataset/README.md` and `docs/DATASET.md` (new labels, classes, counts, split hashes; remove Hindi plans) | Dataset teammate |
| Carried forward: citation spot-check, legal re-read, threat-model peer review, PaddleOCR model licences | As listed in Phase 2 |

**Known issues:**
- Small builds may leave some of the 46 classes out of val or test; with 10 content versions per document, 36 content classes need about 9 or more documents per split. The validator warns (COVERAGE).
- All base documents are still 2 pages, so page edits always involve the header page.
- Commit due when git is re-enabled (D28).

### Phase 5: Evidence intake, basic (2026-10-16, partly done)

**Gate check:** depends on Phase 3, which is built but open (Docker stack, GitHub CI, fresh clone). Phase 4 is Not met (dataset not regenerated; the validator reports 1,860 errors on the v0 dataset). Phase 1 still waits on the citation spot-check. Owner decision: proceed and carry the Phase 4 items forward to the dataset teammate. Phase 6 (OCR) stays blocked until the dataset passes the validator. Phase 3 is not closed by this phase.

**Docker split:**
- Group A (verified here): file type and limit checks, SHA-256 at intake, schema and migration (on SQLite), access rules, custody events, the API, the intake order with its failure paths, and the exact S3 requests (botocore Stubber).
- Group B (**built, unverified until Docker**): migration and append-only grants on real PostgreSQL; Object Lock on real SeaweedFS (overwrite and delete refused); `storage-init` against SeaweedFS; a full upload through nginx, API, PostgreSQL and SeaweedFS. Group B tests are written and skip with the reason "needs Docker: start the stack with ... then set PRAMAAN_IT=1".

**Built:**

| Path | What it is |
|---|---|
| `app/cases/` (`models.py`, `service.py`, `api.py`) | Cases and members. Only an IO creates a case; server-generated case numbers; per-case access check used by every route (D89) |
| `app/evidence/models.py`, `app/custody/models.py`, `app/models.py` | Schema v1: cases, case_members, documents, document_versions, storage_objects, fingerprints, verdicts, custody_events. Database checks for verdict names, the severity rule, media types and SHA-256 length |
| `migrations/versions/0002_evidence_schema_v1.py` | Creates the schema; on PostgreSQL revokes UPDATE, DELETE, TRUNCATE on custody_events, document_versions, storage_objects from the app role (D87) |
| `app/evidence/filetypes.py`, `app/validation.py` | Magic bytes, extension match, real parser open (pdfium, Pillow), 25 MB, 30 pages, 40 megapixels checked before decoding; free text and file name cleaning (D90) |
| `app/evidence/storage.py`, `app/evidence/storage_init.py` | S3 Object Lock store (COMPLIANCE, versioning, Content-MD5, If-None-Match, refuses used keys and buckets without versioning); in-memory stand-in with the same rules; bucket setup job (D84 to D86) |
| `app/evidence/intake.py`, `app/evidence/documents.py`, `app/evidence/api.py` | Upload, corrected version (FR-06), list and detail. Hash first, check, store, one transaction; `upload.rejected` and `storage.orphaned` events (D83, D91) |
| `app/access/identity.py`, `app/errors.py`, `app/limits.py`, `app/deps.py`, `app/main.py` | Dev header identity, off by default (D82); one error shape that never echoes values; request body limit before parsing; routers wired in |
| `docker-compose.yml`, `.env.example`, `docker/compose.integration.yml` | `storage-init` one-shot service; new settings `PRAMAAN_S3_BUCKET`, `PRAMAAN_RETENTION_DAYS`, `PRAMAAN_DEV_IDENTITY=false`; integration overlay (127.0.0.1 ports, dev identity) |
| Tests | `tests/app/test_filetypes.py`, `test_storage.py`, `test_intake_api.py`; migration and compose tests updated; `tests/integration/` (9 Docker tests) |
| Docs | `DECISIONS.md` D82 to D91; `docs/LICENCES.md` (boto3 and its dependencies, python-multipart, pypdfium2 licence files); `docs/NOVELTY.md` P11; ASVS: 16 items Done at phase 5 (39 of 253 in total), V1.1.2 moved to Phase 9; `README.md` intake section |

**How to run:**
```
.venv/Scripts/python tools/ci.py                     # everything that runs without Docker
docker compose -f docker-compose.yml -f docker/compose.integration.yml up -d --build --wait
PRAMAAN_IT=1 .venv/Scripts/python -m pytest tests/integration -v     # the Docker tests
```

**Test results (16 October 2026):** `tools/ci.py` 9 of 9 steps passed (Bandit, Semgrep, pip-audit, npm audit, gitleaks clean). pytest: 560 passed, 9 skipped, 0 failed. Skipped, all for "needs Docker": `test_postgres_real.py` (6), `test_storage_seaweedfs.py` (2), `test_upload_stack.py` (1). Highlights: the stored SHA-256 equals a local `hashlib` calculation and the stored bytes; wrong type refused (415) by content, not name; one byte over the limit refused (413), exactly at the limit accepted; a chunked body with no Content-Length is cut off; Clerk, Auditor, Admin, non-member and role-mismatch uploads refused (403) and logged; one custody event per upload; version 2 leaves the bytes and row of version 1 unchanged; a storage outage saves nothing; a database failure after storage leaves a `storage.orphaned` event; migration and models compare equal on SQLite, and downgrade works.

**Exit criteria (Phase 5):**

| Exit criterion | Result | Evidence |
|---|---|---|
| Upload works end to end and stores SHA-256 | Met on mocks, unverified until Docker | `test_upload_stores_exact_bytes_with_matching_sha256_and_one_custody_event` (SQLite, in-memory store). Real stack: `tests/integration/test_upload_stack.py`, skipped |
| Overwrite and delete of an original fail at the storage level | Met on mocks, unverified until Docker | `test_fake_store_keeps_the_original_and_refuses_overwrite_and_delete`, Stubber tests of the S3 requests. Real SeaweedFS: `tests/integration/test_storage_seaweedfs.py`, skipped |
| Custody event recorded for each upload | Met on mocks, unverified until Docker | `test_one_event_per_upload`, rejection tests. Append-only grants on PostgreSQL: `tests/integration/test_postgres_real.py`, skipped |
| Tests pass in CI | Met locally; GitHub run not done | `tools/ci.py` 9 of 9. GitHub Actions needs git (paused, D28) |

Definition of done: tests, scanners, PROGRESS, DECISIONS and LICENCES done. Not done: merge from a `phase-05` branch (git paused); `docker compose up` from a clean clone (no Docker).

**Needs a human:**

| Item | Suggested owner |
|---|---|
| Run the Docker checks below once Docker is available | Integration and backend |
| Confirm the default retention of 3650 days for the demo (originals can never be deleted before then; only removing the volume clears them) | Project owner |
| Carried forward from Phase 4: regenerate the dataset and pass the validator; 10% human re-check; dataset docs | Dataset teammate |
| Carried forward: citation spot-check, legal re-read, threat-model peer review, PaddleOCR model licences | As listed in Phase 2 |

**Known issues:**
- Not built here, by plan: the 200 MB decompressed PDF limit and the ClamAV scan (Phase 22), upload rate limits (Phase 22), encryption of originals before storage (Phase 18), sealing (Phase 19), real login (Phase 16). Refused reads (403 on list and detail) are not yet logged as events; Phase 17 adds that (ASVS V16.3.2).
- SeaweedFS support for `If-None-Match` on PUT, Content-MD5 with Object Lock, and the boto3 checksum settings is unverified until Docker. If `If-None-Match` is not supported, the head check and versioning still protect the original (D84).
- No test for password-protected PDFs: no permissive tool here writes an encrypted PDF. The code refuses them on the pdfium password error.
- The test client prints a Starlette deprecation warning about httpx; it does not affect results.
- Commit due when git is re-enabled (D28).

### Dataset audit and FIR-Tamper v3 Stage 1 (2026-10-18, part of Phase 4)

**Audit of dataset_v2** (teammate's E0 to E15 build), read only, in `analysis/dataset_audit/` (`REPORT.md`, `issues.csv`, `stats.json`, scripts to rerun). Verdict: not ready to train the Legal Hash. 27 issues: 3 Blockers (sample ID and class code printed on every page and readable by OCR in 94% to 97% of images; 5 distinct narratives across 50 bases; one fixed replacement value per class), 15 Majors (E11, E12, E14, E15 fail their definition on all 50 samples; 4 validation bases; no format-only variants; court orders out of scope per D32; others), 9 Minors. `IMPROVEMENT_PLAN.md` compares v2 with the project generator.

**Decisions:** D92 (this session builds v3 in stages, replaces D76 for v3), D93 (three document types), D94 (E0 to E19 names in a derived label file; evidence and custody fields wait for Stage 2), D95 (Stage 1 size and seed). Plan: `docs/DATASET_V3_PLAN.md`.

**Built:**

| Item | What |
|---|---|
| `dataset_v3/` | 200 bases (80 FIR, 60 charge sheet, 60 statement), 3,000 versions, 9,000 samples, seed 20261018, 5.0 GB, 26 minutes on 12 cores. Card: `dataset_v3/README.md` |
| `ml/data/e_class.py` | Writes `labels_eclass.csv`: E0 to E19 and `verdict_3level` (Tampered named Materially Altered) next to the generator labels |
| `tests/ml/test_e_class.py` | 13 tests: every generator class maps, only harmless classes map to E0, narrative entity slots map, unknown classes fail loudly |
| `analysis/dataset_audit/audit_v3.py` | v3 audit against the plan's acceptance targets |
| `.gitignore` | v3 generated folders and the audit venv |

**How to run:** see `dataset_v3/README.md` (two commands). Checks: `.venv/Scripts/python -m ml.data.validate_labels --data dataset_v3`, `.venv/Scripts/python -m ml.data.generator.check --data dataset_v3`, and `analysis/dataset_audit/.venv/Scripts/python analysis/dataset_audit/audit_v3.py`.

**Test results (18 October 2026):** validator PASS (0 errors, 0 warnings, 3 of 3 split hashes match); generator QA PASS (0 declaration mismatches, 0 text-layer failures, 0 personal-data hits); audit 13 of 13 pass (no missing or corrupt files, no class code in printed text or metadata, no split leakage, val and test 15% each, 200 distinct narratives, 0 cross-split narrative pairs above 0.9, 33.3% harmless, every class and all five verdicts in every split); `pytest tests`: 576 passed, 9 skipped (Docker), 0 failed.

**Known issues:**
- 84% of test-document sentences (entities masked) share a template with training documents. Narrative-hash test results may overstate generalisation until Stage 2 adds held-out template families.
- E7, E9, E12, E13, E14 have no samples (Stage 2).
- E2, E3, E6, E8 have 24 to 27 test samples each. Rebuilding with `--content-per-doc 20` doubles them (CPU only).
- Captures are simulated, one level. File names contain the generator class code; loaders must read pairs from `labels_eclass.csv`.
- dataset_v2 is left as it is; its owner has the audit and fix list.

**Carried forward:**

| Item | Owner |
|---|---|
| Human re-check of the 900-row sample `analysis/dataset_v3_build/recheck_10pct.csv` | Dataset teammate |
| Decide the paper taxonomy (E1 to E15 or rule-based groups) before Stage 2 | Project owner |
| Stage 2 before Phase 12 | ML and dataset owners |

### FIR-Tamper v3 Stage 2 (2026-10-18, part of Phase 4)

**Goal:** close the gaps the Stage 1 audit left: shared templates (84%), five E-classes with no samples, small test counts, class codes in file names. Decision D96.

**Built:**

| Item | What |
|---|---|
| `ml/data/generator/` | 12 new classes: E_ROLE_SWAP (E7), E_EXHIBIT_ID and E_EXHIBIT_DESC (E9), N_MODAL (E12, Minor), C_CUSTODY_HOLDER, C_CUSTODY_DATE, C_CUSTODY_ENTRY_REMOVED (E13), T_BACKDATE (E14), N_ENTITY_NAME/DATE/TIME/NUMBER. Fields rows 28 to 31 (property items, exhibit IDs, seizure date, custody chain) with layouts. 8 new scenarios (12 in total). Template family B (3 scenarios plus its own generic sentences) for the new test_unseen split. Modal slots. E-class plan (`--eclass-plan`). Opaque version IDs and file names. Footer without a version tag |
| `ml/data/e_class.py`, `ml/data/validate_labels.py`, `ml/data/generator/check.py` | New classes mapped; test_unseen split; ratios over seen splits; coverage by split; check no longer flags an old sentence kept inside a new one |
| `tests/ml/test_stage2.py` | 56 tests: slot consistency of every template, disjoint families, each new class, entity kinds, opaque IDs, neutral footer, a small Stage 2 build (all 20 E-classes, test_unseen family B only with no train template, text layer and personal data) |
| `docs/CRITICAL_FIELDS.md`, `LEGAL_HASH_SPEC.md` | Rows 28 to 31 |
| `dataset_v3/` | Rebuilt: 230 bases (92 FIR, 69 charge sheet, 69 statement), 6,560 versions, 19,680 samples, 12 GB, 55 minutes |

**Bugs found by the new tests and fixed:** T_BACKDATE first moved only the report date before 1 July 2024, so a charge sheet date could stay after it (no anachronism); it now shifts by the latest date. The QA text check reported a false failure when a modal edit kept the old sentence inside the new one ("I know X" to "I think I know X").

**Test results (18 October 2026):** validator PASS (0 errors, 0 warnings, 4 of 4 split hashes); QA PASS (0 declaration mismatches, 0 text-layer failures, 0 personal-data hits, no class missing from a split); audit 18 of 18 (every E-class present, smallest test count 75 for E3, test_unseen template overlap with train 0%, no class code in text, metadata or paths, cross-split narrative similarity max 0.84); `pytest tests`: 644 passed, 9 skipped (Docker), 0 failed.

**Known issues:**
- The v0 dataset and v3 Stage 1 can no longer be rebuilt byte-for-byte: the generator changed and git is paused (D28), so the earlier code is not stored. v0 files are still on disk; Stage 1 files were replaced.
- Captures are simulated, one level (Phase 10).
- BNS section numbers and the BNS commencement date used by E14 are not verified against official text (D38, TODO: verify).
- Seen-family test documents share templates with train by design; generalisation is measured on test_unseen.

**Carried forward:**

| Item | Owner |
|---|---|
| Human re-check of `analysis/dataset_v3_build/recheck_10pct.csv` (1,968 rows) | Dataset teammate |
| Harder and real captures (Stage 3) | Phase 10 |
| Turn git back on and commit the generator, so datasets stay reproducible | Done 2026-10-18 (D97): first commit pushed to https://github.com/k3evlar/PramaanDMS |

### Verify when Docker is on (running list)

One session with Docker clears these. Phase 4 adds nothing to this list. Phase 5 adds five rows.

| From | Check | Command |
|---|---|---|
| Phase 3 | All 8 services healthy | `python tools/setup_env.py`, `docker compose up -d --build --wait`, `docker compose ps` |
| Phase 3 | `/health` OK against real services | `docker compose exec api python -m app.health_cli` (exit code 0) |
| Phase 3 | GitHub CI green | Re-enable git, commit, push, check the Actions run |
| Phase 3 | Fresh clone runs from README | Clone on a second machine and follow README only |
| Phase 5 | Migration 0002 on real PostgreSQL; the app role cannot UPDATE or DELETE evidence rows or create tables | `PRAMAAN_IT=1 pytest tests/integration/test_postgres_real.py -v` (with the integration overlay up) |
| Phase 5 | `storage-init` creates the bucket with versioning and a COMPLIANCE lock | `docker compose logs storage-init` shows the bucket ready; `test_bucket_has_versioning_and_compliance_lock` |
| Phase 5 | SeaweedFS refuses overwrite and delete of a locked original | `PRAMAAN_IT=1 pytest tests/integration/test_storage_seaweedfs.py -v` |
| Phase 5 | Full upload through nginx, API, PostgreSQL and SeaweedFS stores the SHA-256 | `PRAMAAN_IT=1 pytest tests/integration/test_upload_stack.py -v` |
| Phase 5 | SeaweedFS accepts the boto3 checksum settings, Content-MD5 and If-None-Match | Covered by the two tests above; if a PUT fails, check D86 and the API log |
