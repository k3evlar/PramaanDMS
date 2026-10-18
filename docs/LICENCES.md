# Licences

Phase 2 deliverable. Every planned library, service, model and data source, with its licence.

Rule (CLAUDE.md, D18): no non-commercial licences. Copyleft (GPL, LGPL, MPL, AGPL) is allowed only when we use the component unmodified and the table says how. Source-available licences with use limits (BUSL, RSAL, SSPL, OpenRAIL with commercial limits) are blockers for anything we ship.

**How this was checked (16 October 2026).** Each licence was read from an authoritative page:
- the project's official repository LICENSE file (often through the GitHub licence API)
- the PyPI package metadata
- the Hugging Face model card metadata
- the official website

The page is listed in the Source column. Nothing is taken from memory. Rows marked "PyPI only" were confirmed from package metadata, because the LICENSE file could not be opened directly.

**Status values:**

| Status | Meaning |
|---|---|
| **Chosen** | Part of the product we build and demo |
| **Dev/test only** | Used in development, CI or tests; never shipped |
| **Evaluation only** | Used only to run research baselines; never shipped |
| **Alternative** | Allowed, kept as a fallback, not used now |
| **Rejected** | Not allowed or too risky; reason given |

## 1. Platform and backend

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| FastAPI | MIT | yes | API framework | Chosen | https://github.com/fastapi/fastapi/blob/master/LICENSE |
| Pydantic | MIT | yes | Validation | Chosen | https://github.com/pydantic/pydantic/blob/main/LICENSE |
| Uvicorn | BSD-3-Clause | yes | ASGI server | Chosen | https://github.com/Kludex/uvicorn/blob/main/LICENSE.md |
| Starlette | BSD-3-Clause | yes | Web toolkit under FastAPI | Chosen | https://pypi.org/pypi/starlette/json |
| pydantic-settings | MIT | yes | Settings from environment variables | Chosen | https://pypi.org/pypi/pydantic-settings/json |
| httpx | BSD-3-Clause | yes | HTTP client for health checks | Chosen | https://pypi.org/pypi/httpx/json |
| boto3 | Apache-2.0 | yes | S3 client for SeaweedFS (Phase 5, D86) | Chosen | https://pypi.org/pypi/boto3/json |
| botocore | Apache-2.0 | yes | Pulled in by boto3 | Chosen | https://pypi.org/pypi/botocore/json |
| s3transfer | Apache-2.0 | yes | Pulled in by boto3 | Chosen | https://pypi.org/pypi/s3transfer/json |
| jmespath | MIT | yes | Pulled in by botocore | Chosen | https://pypi.org/pypi/jmespath/json |
| python-dateutil | BSD-3-Clause OR Apache-2.0 (dual licence, PyPI classifiers) | yes | Pulled in by botocore | Chosen | https://pypi.org/pypi/python-dateutil/json |
| six | MIT | yes | Pulled in by python-dateutil | Chosen | https://pypi.org/pypi/six/json |
| urllib3 | MIT | yes | HTTP library used by botocore | Chosen | https://pypi.org/pypi/urllib3/json |
| python-multipart | Apache-2.0 | yes | Multipart form parsing for uploads (Phase 5) | Chosen | https://pypi.org/pypi/python-multipart/json |
| opentelemetry-api | Apache-2.0 | yes | Pulled in by FastAPI | Chosen | https://pypi.org/pypi/opentelemetry-api/json |
| SQLAlchemy | MIT | yes | ORM | Chosen | https://github.com/sqlalchemy/sqlalchemy/blob/main/LICENSE |
| Alembic | MIT | yes | Migrations | Chosen | https://github.com/sqlalchemy/alembic/blob/main/LICENSE |
| psycopg 3 | LGPL-3.0-only | yes (copyleft conditions) | Unmodified library dependency | Chosen | https://github.com/psycopg/psycopg/blob/master/LICENSE.txt |
| PostgreSQL server | PostgreSQL | yes | Database, separate container | Chosen | https://www.postgresql.org/about/licence/ |
| Celery | BSD-3-Clause | yes | Background worker (JSON serializer only, D60) | Chosen | https://raw.githubusercontent.com/celery/celery/main/LICENSE |
| kombu | BSD-3-Clause | yes | Messaging library used by Celery | Chosen | https://pypi.org/pypi/kombu/json |
| redis (redis-py client library) | MIT | yes | Client for Valkey (same protocol); the client library is MIT, unlike the Redis server | Chosen | https://pypi.org/pypi/redis/json |
| Valkey | BSD-3-Clause | yes | Queue broker, separate container (D60) | Chosen | https://github.com/valkey-io/valkey/blob/unstable/COPYING |
| SeaweedFS | Apache-2.0 | yes | S3 object storage with Object Lock, separate container (D58) | Chosen | https://github.com/seaweedfs/seaweedfs/blob/master/LICENSE |
| OpenBao | MPL-2.0 | yes (copyleft conditions) | Key store, unmodified separate container (D57) | Chosen | https://github.com/openbao/openbao/blob/main/LICENSE |
| ClamAV | GPL-2.0 | yes (copyleft conditions) | Antivirus, unmodified separate `clamd` container, used over a socket, not linked | Chosen | https://github.com/Cisco-Talos/clamav/blob/main/COPYING.txt |
| nginx | BSD-2-Clause | yes | Reverse proxy and TLS | Chosen | https://github.com/nginx/nginx/blob/master/LICENSE |
| Docker Engine (moby) | Apache-2.0 | yes | Containers | Chosen | https://github.com/moby/moby/blob/master/LICENSE |
| Docker Compose | Apache-2.0 | yes | One-command run | Chosen | https://github.com/docker/compose/blob/main/LICENSE |
| RQ | BSD-2-Clause | yes | Queue library | Alternative | https://raw.githubusercontent.com/rq/rq/master/LICENSE |
| Redis server 7.4 | RSALv2 OR SSPLv1 | restricted | n/a | Rejected: source-available, not open source. Valkey used instead (D60) | https://redis.io/legal/licenses/ |
| Redis server 8.x | RSALv2 OR SSPLv1 OR AGPL-3.0 | yes only under AGPL-3.0 | n/a | Rejected: licence choice adds confusion; Valkey is a drop-in replacement | https://raw.githubusercontent.com/redis/redis/unstable/LICENSE.txt |
| MinIO server | AGPL-3.0 | yes (copyleft conditions) | n/a | Rejected: repository archived, "no longer maintained", no new community binaries or images (D58) | https://github.com/minio/minio/blob/master/LICENSE and README |
| HashiCorp Vault 1.15+ | BUSL-1.1 | restricted | n/a | Rejected: source-available with a competitive-use limit (D57) | https://raw.githubusercontent.com/hashicorp/vault/main/LICENSE |

## 2. Cryptography, authentication and time

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| cryptography (pyca) | Apache-2.0 OR BSD-3-Clause | yes | AES-256-GCM, Ed25519, HMAC, SHA-256 | Chosen | https://raw.githubusercontent.com/pyca/cryptography/main/LICENSE |
| argon2-cffi | MIT | yes | Argon2id password hashing | Chosen | https://github.com/hynek/argon2-cffi/blob/main/LICENSE |
| pyotp | MIT | yes | TOTP | Chosen | https://raw.githubusercontent.com/pyauth/pyotp/main/LICENSE |
| rfc3161ng | MIT | yes | RFC 3161 time-stamp client | Chosen | https://raw.githubusercontent.com/trbs/rfc3161ng/master/LICENSE |
| FreeTSA service | No licence or terms published | unclear | Public TSA for the demo only; URL is configuration (D64) | Chosen (demo only) | https://freetsa.org/index_en.php |

## 3. OCR, ML and images

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| PaddleOCR | Apache-2.0 | yes | OCR engine candidate (D59). TODO: verify each downloaded model's own licence in Phase 6 | Chosen | https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE |
| PaddlePaddle | Apache-2.0 | yes | Runtime for PaddleOCR | Chosen | https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE |
| Tesseract | Apache-2.0 | yes | OCR fallback and benchmark candidate | Chosen | https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE |
| PyTorch | BSD-3-Clause (wheel bundles other permissive licences, including BSL-1.0 = Boost) | yes | Model training and inference | Chosen | https://raw.githubusercontent.com/pytorch/pytorch/main/LICENSE |
| Hugging Face Transformers | Apache-2.0 | yes | Model loading | Chosen | https://github.com/huggingface/transformers/blob/main/LICENSE |
| google/muril-base-cased | Apache-2.0 | yes | Narrative encoder candidate | Chosen (candidate) | https://huggingface.co/api/models/google/muril-base-cased |
| intfloat/e5-base-v2 | MIT | yes | English encoder candidate | Chosen (candidate) | https://huggingface.co/api/models/intfloat/e5-base-v2 |
| google-bert/bert-base-uncased | Apache-2.0 | yes | English encoder candidate | Chosen (candidate) | https://huggingface.co/api/models/google-bert/bert-base-uncased |
| sentence-transformers/all-MiniLM-L6-v2 | Apache-2.0 | yes | English encoder candidate, plain embedding baseline | Chosen (candidate) | https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2 |
| sentence-transformers/LaBSE | Apache-2.0 | yes | Embedding baseline | Evaluation only | https://huggingface.co/api/models/sentence-transformers/LaBSE |
| intfloat/multilingual-e5-base | MIT | yes | Embedding baseline | Evaluation only | https://huggingface.co/api/models/intfloat/multilingual-e5-base |
| ai4bharat/indic-bert, IndicBERT v2 | MIT | yes | Not needed while English only (D39) | Alternative | https://huggingface.co/api/models/ai4bharat/indic-bert |
| Surya OCR code | Apache-2.0 | yes | n/a | Rejected: the code licence is fine, but it is only useful with the restricted weights below (D59) | https://github.com/datalab-to/surya/blob/master/LICENSE |
| Surya OCR weights | Modified AI Pubs OpenRAIL-M (older weights CC BY-NC-SA-4.0) | restricted | n/a | Rejected: free only for research, personal use and startups under a revenue limit (D59) | https://raw.githubusercontent.com/datalab-to/surya/master/README.md |
| opencv-python | Apache-2.0 (package); MIT (wrapper repo) | yes | Image processing | Chosen | https://github.com/opencv/opencv-python/blob/4.x/LICENSE.txt |
| imagehash | BSD-2-Clause | yes | Perceptual hashes | Chosen | https://github.com/JohannesBuchner/imagehash/blob/master/LICENSE |
| NumPy | BSD-3-Clause | yes | Arrays | Chosen | https://raw.githubusercontent.com/numpy/numpy/main/LICENSE.txt |
| Pillow | MIT-CMU | yes | Images | Chosen | https://raw.githubusercontent.com/python-pillow/Pillow/main/LICENSE |

## 4. Documents, PDF and QR

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| ReportLab (open source) | BSD (PyPI only) | yes | PDF drawing (dataset generator, reports) | Chosen | https://pypi.org/pypi/reportlab/json |
| WeasyPrint | BSD-3-Clause | yes | HTML to PDF reports | Chosen | https://github.com/Kozea/WeasyPrint/blob/main/LICENSE |
| pypdfium2 | BSD-3-Clause OR Apache-2.0 (PyPI only) | yes | PDF rendering and text extraction | Chosen | https://pypi.org/pypi/pypdfium2/json |
| PDFium | BSD-3-Clause | yes | Bundled in pypdfium2 | Chosen | https://pdfium.googlesource.com/pdfium/+/refs/heads/main/LICENSE |
| segno | BSD-3-Clause | yes | QR generation (D61) | Chosen | https://github.com/heuer/segno/blob/master/LICENSE |
| pyzbar | MIT | yes | QR reading (D61) | Chosen | https://github.com/NaturalHistoryMuseum/pyzbar/blob/master/LICENSE.txt |
| ZBar | LGPL-2.1 | yes (copyleft conditions) | Shared library loaded unmodified by pyzbar | Chosen | https://github.com/mchehab/zbar/blob/master/LICENSE.md |
| python-qrcode | BSD-3-Clause (PyPI also shows an "Other/Proprietary" classifier) | yes, minor doubt | n/a | Alternative: segno avoids the doubt | https://raw.githubusercontent.com/lincolnloop/python-qrcode/main/LICENSE |
| PyMuPDF | AGPL-3.0 or Artifex commercial | yes (copyleft conditions) | n/a | Rejected: AGPL for an in-process library; pypdfium2 does the same job | https://github.com/pymupdf/PyMuPDF/blob/main/COPYING |

## 5. Frontend

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| React | MIT | yes | UI | Chosen | https://github.com/react/react/blob/main/LICENSE |
| TypeScript | Apache-2.0 | yes | UI language | Chosen | https://github.com/microsoft/TypeScript/blob/main/LICENSE.txt |
| Vite | MIT | yes | Build tool | Chosen | https://github.com/vitejs/vite/blob/main/LICENSE |
| Tailwind CSS | MIT | yes | Styling | Chosen | https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE |
| Node.js | MIT (bundles third-party licences) | yes | Builds the frontend (24 LTS, D69) | Chosen | https://github.com/nodejs/node/blob/main/LICENSE |
| Vitest | MIT | yes | Frontend tests | Dev/test only | https://www.npmjs.com/package/vitest |
| jsdom | MIT | yes | Browser environment for frontend tests | Dev/test only | https://www.npmjs.com/package/jsdom |
| @testing-library/react | MIT | yes | Frontend tests | Dev/test only | https://www.npmjs.com/package/@testing-library/react |
| @vitejs/plugin-react | MIT | yes | Vite plugin for React | Dev/test only | https://www.npmjs.com/package/@vitejs/plugin-react |
| @types/react, @types/react-dom | MIT | yes | TypeScript types | Dev/test only | https://www.npmjs.com/package/@types/react |

## 6. Baselines (research only)

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| ssdeep (C library) | GPL-2.0-or-later | yes (copyleft conditions) | ssdeep baseline runs only, never shipped (D61) | Evaluation only | https://raw.githubusercontent.com/ssdeep-project/ssdeep/master/COPYING |
| python ssdeep bindings | LGPL-3.0-or-later (links GPL libfuzzy) | yes (copyleft conditions) | Same as above | Evaluation only | https://github.com/DinoTools/python-ssdeep/blob/master/LICENSE |
| ppdeep | Apache-2.0 (PyPI only) | yes | Pure-Python ssdeep, preferred where results match | Evaluation only | https://pypi.org/pypi/ppdeep/json |
| TLSH / py-tlsh | Apache-2.0 OR BSD | yes | TLSH baseline | Evaluation only | https://raw.githubusercontent.com/trendmicro/tlsh/master/LICENSE |

## 7. Development, CI and security tools

| Component | Licence (SPDX) | Commercial use | How we use it | Status | Source |
|---|---|---|---|---|---|
| pytest | MIT | yes | Tests | Dev/test only | https://github.com/pytest-dev/pytest/blob/main/LICENSE |
| PyYAML | MIT | yes | Reads docker-compose.yml and the workflow in tests | Dev/test only | https://pypi.org/pypi/PyYAML/json |
| Bandit | Apache-2.0 | yes | Python SAST in CI | Dev/test only | https://github.com/PyCQA/bandit/blob/main/LICENSE |
| Semgrep CE engine | LGPL-2.1-or-later | yes (copyleft conditions) | SAST in CI, not shipped | Dev/test only | https://github.com/semgrep/semgrep/blob/develop/LICENSE |
| Semgrep Registry rules | Semgrep Rules License v1.0 | yes (internal business use only, no redistribution) | Run in CI only; never copied into the repo, because the licence forbids redistribution | Dev/test only | https://semgrep.dev/legal/rules-license/ |
| pip-audit | Apache-2.0 | yes | Dependency audit in CI | Dev/test only | https://github.com/pypa/pip-audit/blob/main/LICENSE |
| gitleaks | MIT | yes | Secret scanning in CI | Dev/test only | https://github.com/gitleaks/gitleaks/blob/master/LICENSE |
| OWASP ZAP | Apache-2.0 | yes | DAST scan (Phase 27) | Dev/test only | https://github.com/zaproxy/zaproxy/blob/main/LICENSE |

## 8. Container base images

| Image | Licence of the main software | Status | Source |
|---|---|---|---|
| python:3.12.15-slim-trixie | PSF-2.0 (Python), Debian packages under their own free licences | Chosen | https://hub.docker.com/_/python |
| node:24.22.0-alpine3.24 (build stage only) | MIT (Node.js) | Chosen | https://hub.docker.com/_/node |
| nginxinc/nginx-unprivileged:1.30.6-alpine3.24 | BSD-2-Clause (nginx) | Chosen | https://hub.docker.com/r/nginxinc/nginx-unprivileged |
| postgres:17.11-alpine3.24 | PostgreSQL | Chosen | https://hub.docker.com/_/postgres |
| valkey/valkey:8.1.10-alpine3.24 | BSD-3-Clause | Chosen | https://hub.docker.com/r/valkey/valkey |
| chrislusf/seaweedfs:4.48 | Apache-2.0 | Chosen | https://hub.docker.com/r/chrislusf/seaweedfs |
| openbao/openbao:2.7.1 | MPL-2.0 | Chosen | https://hub.docker.com/r/openbao/openbao |
| clamav/clamav:1.4.6 | GPL-2.0 (separate container, unmodified) | Chosen | https://hub.docker.com/r/clamav/clamav |

## 9. Data and documents we reuse

| Item | Licence or terms | How we use it | Status | Source |
|---|---|---|---|---|
| OWASP ASVS 5.0.0 (CSV of requirements) | CC BY-SA 4.0 | Copied into `docs/asvs/` to generate `ASVS_CHECKLIST.md`, with attribution | Chosen | https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0_release/LICENSE.md |
| Meghalaya Police Circular No. 03/2024 (FIR format) | Government publication; reuse terms not stated (TODO: verify before redistributing the PDF) | Field order for our own FIR layout; the PDF is kept for reference only | Chosen (reference only) | https://megpolice.gov.in/sites/default/files/circular-no.3-2024-first-information-report.pdf |

## Open items

- PaddleOCR model files: confirm each downloaded model's licence in Phase 6. The repository is Apache-2.0, and no separate weights licence was found.
- ReportLab and ppdeep were confirmed from PyPI metadata only. Open their LICENSE files when they are installed.
- pypdfium2 5.14.0 (installed in Phase 5): the wheel ships Apache-2.0, BSD-3-Clause and CC-BY-4.0 licence texts, plus build licences for the bundled libraries (PDFium, FreeType, ICU, Little CMS, libjpeg-turbo, OpenJPEG, libpng, zlib, Abseil and others). CC BY 4.0 allows commercial use with attribution. Which files the CC-BY-4.0 text covers is not stated in the package metadata (TODO: verify in the pypdfium2 repository).
- boto3, botocore, s3transfer, jmespath, python-dateutil, six, urllib3 and python-multipart (Phase 5) were confirmed from installed package metadata only.
- Docker Desktop has its own terms. If anyone uses Docker Desktop instead of Docker Engine, check them (TODO: verify).
