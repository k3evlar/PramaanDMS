"""Run every CI check, the same way locally and in GitHub Actions.

Usage (from the repo root):
    python tools/ci.py                 # run all steps
    python tools/ci.py --list          # show the steps
    python tools/ci.py --only bandit   # run one step (repeatable)

Steps: Python tests, ASVS checklist check, frontend tests and build, Bandit, Semgrep,
pip-audit, npm audit, gitleaks. A missing tool is a failure, never a silent skip, so a
green run always means every scanner ran (Phase 3 exit criterion, D68).

Tools are found on PATH first, then in the git-ignored .tools/ folder (portable Node,
gitleaks, and a separate Semgrep environment, because Semgrep's dependencies conflict with
the application's).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SCAN_PATHS = ["app", "tools", "ml", "migrations"]


def find_tool(name: str) -> str | None:
    """PATH first, then .tools/ (node-*/ for npm, gitleaks*/ for gitleaks)."""
    found = shutil.which(name)
    if found:
        return found
    tools = ROOT / ".tools"
    patterns = {"npm": ["node-*/npm.cmd", "node-*/bin/npm"], "gitleaks": ["gitleaks*/gitleaks.exe", "gitleaks*/gitleaks"],
                "semgrep": ["semgrep-venv/Scripts/semgrep.exe", "semgrep-venv/bin/semgrep"]}
    for pattern in patterns.get(name, []):
        hits = sorted(tools.glob(pattern))
        if hits:
            return str(hits[-1])
    scripts = Path(sys.executable).parent
    for candidate in (scripts / f"{name}.exe", scripts / name):
        if candidate.exists():
            return str(candidate)
    return None


@dataclass(frozen=True)
class Step:
    name: str
    tool: str | None  # external tool that must exist, or None for Python modules
    args: list[str]
    cwd: Path = ROOT
    hint: str = ""


def steps() -> list[Step]:
    return [
        Step("pytest", None, [PY, "-m", "pytest", "-q", "tests"]),
        Step("asvs-checklist", None, [PY, "tools/asvs_checklist.py", "--check"]),
        Step("frontend-tests", "npm", ["test"], ROOT / "frontend", "install Node 24 LTS"),
        Step("frontend-build", "npm", ["run", "build"], ROOT / "frontend", "install Node 24 LTS"),
        Step("bandit", None, [PY, "-m", "bandit", "-q", "-r", *SCAN_PATHS, "-ll", "-x", "tests"]),
        Step("semgrep", "semgrep", ["scan", "--config", "p/python", "--config", "p/typescript",
                                    "--config", "p/secrets", "--error", "--metrics=off", "--quiet",
                                    *SCAN_PATHS, "frontend/src"],
             hint="install semgrep in its own environment (pipx install semgrep, or a venv at .tools/semgrep-venv)"),
        Step("pip-audit", None, [PY, "-m", "pip_audit", "-r", "requirements-dev.txt", "--progress-spinner", "off"]),
        Step("npm-audit", "npm", ["audit", "--audit-level=high"], ROOT / "frontend", "install Node 24 LTS"),
        Step("gitleaks", "gitleaks", ["dir", ".", "--config", ".gitleaks.toml", "--redact", "--no-banner"],
             hint="download gitleaks from https://github.com/gitleaks/gitleaks/releases"),
    ]


def run(step: Step) -> tuple[bool, str, float]:
    start = time.perf_counter()
    env = dict(os.environ)
    if step.tool:
        exe = find_tool(step.tool)
        if not exe:
            return False, f"missing tool '{step.tool}': {step.hint}", 0.0
        cmd = [exe, *step.args]
        # A portable tool (for example npm from .tools/node-*) needs its own folder on PATH,
        # because npm starts "node" by name.
        env["PATH"] = str(Path(exe).parent) + os.pathsep + env.get("PATH", "")
    else:
        cmd = step.args
    print(f"\n=== {step.name}: {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}", flush=True)
    proc = subprocess.run(cmd, cwd=step.cwd, env=env, check=False)  # noqa: S603 - fixed argument lists, no shell
    return proc.returncode == 0, f"exit code {proc.returncode}", time.perf_counter() - start


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run all CI checks.")
    ap.add_argument("--only", action="append", default=[], help="run only this step (repeatable)")
    ap.add_argument("--list", action="store_true", help="list the steps and exit")
    args = ap.parse_args(argv)
    all_steps = steps()
    if args.list:
        for s in all_steps:
            print(s.name)
        return 0
    unknown = set(args.only) - {s.name for s in all_steps}
    if unknown:
        print(f"unknown step(s): {sorted(unknown)}", file=sys.stderr)
        return 2
    chosen = [s for s in all_steps if not args.only or s.name in args.only]
    results = [(s.name, *run(s)) for s in chosen]
    print("\n=== Summary")
    for name, ok, detail, secs in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<15} {secs:6.1f}s  {'' if ok else detail}")
    failed = [r[0] for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} steps passed" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
