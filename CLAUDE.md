# CLAUDE.md: Rules for building Pramaan DMS

You are building **Pramaan DMS**, a final-year capstone project (BE, AI and ML, BMSIT&M Bengaluru) based on Smart India Hackathon problem statement **SIH26190** (Ministry of Home Affairs): a secure digital document management system for legal and investigation documents.

The project will be shown to an **industry panel** and turned into a **research paper** (IEEE or Springer conference). Everything must be complete, runnable, and honest.

## Read these files first, every session

1. `PROJECT_BRIEF.md` : what we are building and why
2. `BUILD_PLAN.md` : the master build plan. Read the overview, the dependency map, and the full card for today's phase (goal, depends on, inputs, build tasks, deliverables, tests, exit criteria). This is the detailed source of truth for each phase
3. `PHASES.md` : short summary of all 28 phases. If it ever disagrees with `BUILD_PLAN.md`, follow `BUILD_PLAN.md` and flag the mismatch
4. `PROGRESS.md` : what is already done
5. `DECISIONS.md` : decisions already made. Do not silently change them
6. `LEGAL_HASH_SPEC.md` : the research core (read before any phase in Stage 2 or 3)
7. `SECURITY_FORENSICS.md` : security and forensic rules (read before any phase in Stage 4, and keep them in mind always)
8. `ARCHITECTURE.md` : stack, modules, data flow

## How to work

- **One phase per session.** Do not start the next phase unless told to.
- At the start of a phase: restate the phase goal, list what you will build, and list any questions or conflicts. Ask before building if something is unclear.
- Break the phase into small steps. Finish and test each step before the next.
- Every phase ends with its **exit criteria** from `BUILD_PLAN.md` checked and shown, plus the Definition of done in `BUILD_PLAN.md`.
- Before starting, check the phase's "Depends on" list in `BUILD_PLAN.md` against `PROGRESS.md`. If a dependency is not done, stop and say so.
- At the end of a phase:
  - Update `PROGRESS.md` (what was built, how to run it, test results, known issues)
  - Add any new decision to `DECISIONS.md` with a short reason
  - Commit with a clear message

## Code rules

- Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2. React + TypeScript + Vite for the frontend.
- Everything runs with `docker compose up`. No manual setup steps that are not written down.
- Type hints everywhere. Tests with pytest. Aim for real tests on security and verification logic, not just smoke tests.
- No secrets in code. Use `.env` (with `.env.example` committed).
- Every library and model added goes into `docs/LICENCES.md` with its licence. **No non-commercial licences** (for example CC BY-NC). Flag it if a choice needs one.
- Keep it a **modular monolith**: one FastAPI app with clear modules, plus one background worker. No microservices.

## Honesty rules (very important)

- **Never invent** citations, papers, statistics, legal sections, or standards. If unsure, write `TODO: verify` and tell the user.
- Do not use these words in code, docs, or UI: "tamper-proof", "unhackable", "100% secure", "court admissible", "legally valid", "certified", "compliant with". Use instead: "tamper-evident", "designed in line with", "supports", "draft for officer review".
- Report real numbers from real runs only. Never fill a results table with guessed values.
- If something fails or is cut, say so in `PROGRESS.md`. Do not hide it.

## Writing style for docs and UI text

- Simple, plain English. Short sentences.
- No em dashes.

## When in doubt

Stop and ask. A wrong guess costs more than a question.
