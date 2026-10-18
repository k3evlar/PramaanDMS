# Architecture

Stack confirmed in Phase 2 against the licence check (`docs/LICENCES.md`, D57 to D61). English documents only.

## Stack

| Area | Choice | Why |
|---|---|---|
| Backend API | Python 3.11, FastAPI, Pydantic v2 | Same language as the ML code, fast, auto OpenAPI docs |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic | Reliable, row-level control, JSONB for fingerprints |
| Object storage | SeaweedFS (S3 API) with S3 Object Lock in compliance mode and versioning | Write-once originals. Replaces MinIO, whose community repository is archived and no longer maintained (D58) |
| Queue and worker | Valkey + Celery (JSON serializer only) | OCR and ML jobs run in the background. Valkey (BSD-3-Clause) replaces Redis, whose 7.4 licence is source-available only (D60) |
| Secrets and keys | OpenBao (dev mode for demo; same API as HashiCorp Vault) | Key hierarchy, rotation, audit of key use. Replaces Vault, which is under the Business Source License since 1.15 (D57) |
| OCR | PaddleOCR, with Tesseract as a fallback (pick in Phase 6 by benchmark) | English text with word boxes and confidence scores. Surya is excluded because its model weights restrict commercial use (D59) |
| ML | PyTorch, Hugging Face Transformers; narrative encoder chosen in Phase 12 from MuRIL, e5-base-v2, bert-base-uncased, all-MiniLM-L6-v2 | All candidates allow commercial use |
| Image | OpenCV, imagehash | Preprocessing and perceptual hashes |
| Timestamps | RFC 3161 client (rfc3161ng or similar) + public TSA (for example FreeTSA) | Trusted time |
| Signing | Ed25519 via `cryptography` | Fast, small signatures |
| Antivirus | ClamAV | Scan uploads |
| Frontend | React, TypeScript, Vite, Tailwind | Fast to build, phone friendly |
| PDF reports and rendering | WeasyPrint or ReportLab for reports; pypdfium2 for page rendering (PyMuPDF avoided, AGPL) | Forensic report and Section 63 draft |
| QR codes | segno (generate), pyzbar with ZBar (read) | QR-sealed copies |
| Run | Docker Compose | One command to run |
| CI | GitHub Actions: tests, Bandit, Semgrep, pip-audit, npm audit, gitleaks | Secure build |

Final library choices and licences go in `docs/LICENCES.md`.

## Containers

```
frontend   (React app, served by nginx)
api        (FastAPI)
worker     (Celery: OCR, Legal Hash, reports)
postgres
seaweedfs  (S3 API, object lock)
valkey
openbao
clamav
```

## Backend modules (inside one FastAPI app)

```
app/
  auth/         login, TOTP, sessions, lockout
  access/       roles, case access, two-person approvals
  cases/        cases, assignments
  evidence/     intake, storage, encryption, legal hold, archive
  crypto/       key management (OpenBao client), signing, hashing
  seal/         intake seal, RFC 3161 timestamps
  ledger/       Merkle transparency log, STH, proofs, export
  custody/      chain of custody views
  legalhash/    preprocess, OCR, fields, normalize, F/N/V, verdict
  verify/       verify API, QR issue and check
  investigate/  tamper window, backdating rules (backdating built at the end of the build)
  reports/      forensic PDF, Section 63 draft
  admin/        user management (no evidence access)
ml/
  data/         FIR-Tamper generator, augmentation, capture set tools
  train/        narrative hash training
  eval/         baselines, metrics, ablations
  registry/     signed model registry
```

## Main data flows

### Intake
Upload -> magic byte check + size limit -> ClamAV -> SHA-256 -> encrypt with new data key -> store in SeaweedFS (object lock, compliance mode) -> sign intake record -> RFC 3161 timestamp -> log event -> background job computes Legal Hash -> fingerprint record signed and stored -> log event.

### Verify (inside the system)
Candidate file -> SHA-256 compare -> Legal Hash pipeline on candidate -> compare with stored fingerprint -> verdict + changes -> verdict record stored with versions -> log event.

### Verify (public, QR)
Phone photo -> verify page reads QR -> checks signature -> fetches fingerprint record -> runs pipeline on the photo -> returns one fixed public message (for example "A critical field was changed."), with no field names, values or locations -> log event. Authenticated staff with access to the case see the full change list.

### Tamper window
Tampered verdict -> find last checkpoint where the document version was Equivalent and the first where it was Tampered -> list custody events between them -> show users and actions in that window.

## Core tables (first draft, refine in Phase 5)

users, roles, user_roles, mfa_secrets, sessions, cases, case_members, documents, document_versions, storage_objects, data_keys (wrapped), intake_seals, timestamps, fingerprints, verdicts, custody_events, ledger_entries, tree_heads, approvals (two-person), legal_holds, qr_certificates, reports, model_registry, settings (signed).
