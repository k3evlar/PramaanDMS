# Pramaan DMS

Secure document management with tamper-evident verification for FIRs, witness statements and charge sheets (SIH26190). English documents only. All data is synthetic.

## Run it

You need: Git, Docker (Docker Desktop on Windows or macOS, Docker Engine on Linux) with Compose v2, Python 3.12 or newer, and about 16 GB RAM. ClamAV downloads virus signatures (about 300 MB) on first start, so the first run needs internet and takes several minutes.

```
git clone <repo-url> pramaan-dms
cd pramaan-dms
python tools/setup_env.py                 # once: creates .env and docker/secrets/ with random secrets
docker compose up -d --build --wait       # builds and starts all services, waits until healthy
docker compose ps                         # all 8 services should show "healthy"
docker compose exec api python -m app.health_cli    # full dependency report, exit code 0 when all pass
```

Then open http://127.0.0.1:8080. The page says "The service is running." when the API is reachable.

Stop with `docker compose down`. To delete all data as well (for example after `setup_env.py --force`), use `docker compose down -v`.

Services: `frontend` (React, served by unprivileged nginx on port 8080), `api` (FastAPI), `worker` (Celery), `postgres`, `seaweedfs` (S3 storage with Object Lock), `valkey` (job queue), `openbao` (keys, dev mode), `clamav` (virus scan). Two short jobs run before the API starts: `migrate` applies database migrations, and `storage-init` creates the write-once originals bucket. Only the frontend port is published, on 127.0.0.1 unless `PRAMAAN_HTTP_BIND` in `.env` says otherwise.

## Develop and test

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt     # Windows (use .venv/bin/python on Linux or macOS)
cd frontend && npm ci && cd ..                                   # Node 24 LTS
.venv/Scripts/python tools/ci.py                                 # every CI check: tests, ASVS check, frontend, Bandit, Semgrep, pip-audit, npm audit, gitleaks
.venv/Scripts/python tools/ci.py --only pytest                   # one step
```

Dataset tools (the dataset itself is built by the dataset owner):

```
.venv/Scripts/python -m ml.data.generator.build --out <folder>          # generate documents, versions and labels from a seed
.venv/Scripts/python -m ml.data.validate_labels --data <folder> --report <file> --sample-out <file>   # check labels against the tampering rules
```

### Evidence intake (Phase 5)

API routes (behind nginx at `/api/`): `POST /cases`, `GET /cases`, `POST /cases/{id}/members`, `POST /cases/{id}/documents` (multipart: `file`, `doc_type`, `title`), `POST /documents/{id}/versions` (multipart: `file`, `reason`), `GET /cases/{id}/documents`, `GET /documents/{id}`. Until login exists (Phase 16), the caller is named by the `X-Pramaan-User` and `X-Pramaan-Role` headers, and only when `PRAMAAN_DEV_IDENTITY=true` in a dev or test environment (D82).

Status: the app logic is tested without Docker (SQLite and an in-memory write-once store). These parts are **built, unverified until Docker**:

- the migration and the append-only grants on real PostgreSQL
- Object Lock on real SeaweedFS (overwrite and delete refused, `storage-init` bucket setup)
- a full upload through nginx, the API, PostgreSQL and SeaweedFS

Their tests are in `tests/integration` and skip until Docker is running:

```
docker compose -f docker-compose.yml -f docker/compose.integration.yml up -d --build --wait
PRAMAAN_IT=1 .venv/Scripts/python -m pytest tests/integration -v
```

`tools/ci.py` is the same script GitHub Actions runs (`.github/workflows/ci.yml`). It looks for tools on PATH first, then in a git-ignored `.tools/` folder (portable Node, gitleaks, and Semgrep in its own environment, because Semgrep's dependencies conflict with the app's). A missing tool fails the run; it is never skipped.

## Context pack

The rest of this file describes the context pack used to build the project with Claude Code. This folder gives Claude Code the full scope of the project, so every session builds the right thing.

## Files

| File | What it is |
|---|---|
| `CLAUDE.md` | Rules Claude Code follows every session |
| `PROJECT_BRIEF.md` | The final idea in one place |
| `BUILD_PLAN.md` | Master build plan: every phase card, dependencies, deliverables, definition of done |
| `LEGAL_HASH_SPEC.md` | How the Legal Hash works (research core) |
| `SECURITY_FORENSICS.md` | Security and forensic rules |
| `ARCHITECTURE.md` | Stack, modules, data flows |
| `PHASES.md` | Short summary of the 28 phases (BUILD_PLAN.md wins if they differ) |
| `DECISIONS.md` | Every decision and why |
| `PROGRESS.md` | What is done (Claude Code updates it) |
| `PROBLEM_STATEMENT.md` | SIH26190 text (paste the official text in) |

## How to use

1. Create an empty project folder and copy all these files into its root.
2. Paste the official SIH26190 text into `PROBLEM_STATEMENT.md`.
3. Open the folder in Claude Code.
4. Start each session with the prompt below. Change the phase number each time.

## Session prompt (copy, change the number)

```
We are building Pramaan DMS. Read CLAUDE.md first, then PROJECT_BRIEF.md,
BUILD_PLAN.md (overview, dependency map, definition of done, and the full
card for this phase), PROGRESS.md and DECISIONS.md. Read LEGAL_HASH_SPEC.md
and SECURITY_FORENSICS.md if this phase touches them.

Today we do Phase <N> only.

Before writing any code:
1. Check this phase's dependencies against PROGRESS.md.
2. Restate the phase goal, deliverables and exit criteria in your own words.
3. List the steps you will take.
4. List any questions, missing info, or conflicts with earlier decisions.
Wait for my go-ahead.

Then build step by step, test each step, and finish by checking every exit
criterion, updating PROGRESS.md and DECISIONS.md, and committing.
```

## Tips

- Use the strongest model for Phases 12, 15, 17, 18, 19, 20 (training, crypto, access control, log).
- If a session goes off track, stop it, fix `PROGRESS.md`, and start a fresh session for the same phase.
- Do not skip exit criteria. They are your self-review.

- Do not ask Claude Code to build the whole plan in one go. It reads the full plan for context, then builds only the phase you name.
- The human copy of BUILD_PLAN.md lives in Claude Docs. If you edit one, update the other in the same sitting.
