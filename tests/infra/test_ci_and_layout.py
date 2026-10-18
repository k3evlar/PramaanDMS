"""CI configuration and the repository layout from ARCHITECTURE.md."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tools import ci

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def test_ci_runs_every_required_scanner_and_test() -> None:
    names = [s.name for s in ci.steps()]
    for required in ("pytest", "bandit", "semgrep", "pip-audit", "npm-audit", "gitleaks",
                     "frontend-tests", "frontend-build", "asvs-checklist"):
        assert required in names, required


def test_missing_tool_is_a_failure_not_a_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ci, "find_tool", lambda name: None)
    step = next(s for s in ci.steps() if s.name == "gitleaks")
    ok, detail, _ = ci.run(step)
    assert ok is False and "missing tool" in detail


def test_unknown_step_is_rejected() -> None:
    assert ci.main(["--only", "no-such-step"]) == 2


def test_workflow_calls_the_same_script_with_least_privilege() -> None:
    steps = WORKFLOW["jobs"]["ci"]["steps"]
    runs = " ".join(s.get("run", "") for s in steps)
    assert "python tools/ci.py" in runs
    assert "sha256sum -c" in runs  # gitleaks download is checksum-verified
    assert WORKFLOW["permissions"] == {"contents": "read"}


def test_workflow_actions_are_pinned_to_commit_shas() -> None:
    uses = [s["uses"] for s in WORKFLOW["jobs"]["ci"]["steps"] if "uses" in s]
    assert uses
    for u in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u), u


@pytest.mark.parametrize("package", ["auth", "access", "cases", "evidence", "crypto", "seal", "ledger",
                                     "custody", "legalhash", "verify", "investigate", "reports", "admin"])
def test_app_modules_from_architecture_exist(package: str) -> None:
    init = ROOT / "app" / package / "__init__.py"
    assert init.is_file()
    assert re.search(r"Phase", init.read_text(encoding="utf-8")), "module docstring should name its phase"


@pytest.mark.parametrize("folder", ["data", "train", "eval", "registry"])
def test_ml_folders_from_architecture_exist(folder: str) -> None:
    assert (ROOT / "ml" / folder / "__init__.py").is_file()


def test_frontend_has_no_raw_html_or_eval() -> None:
    for f in (ROOT / "frontend/src").rglob("*.ts*"):
        text = f.read_text(encoding="utf-8")
        assert "dangerouslySetInnerHTML" not in text, f
        assert not re.search(r"\beval\(|new Function\(", text), f


def test_frontend_dependencies_are_pinned_and_locked() -> None:
    import json
    pkg = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    for section in ("dependencies", "devDependencies"):
        for name, version in pkg[section].items():
            assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"{name}@{version} is not an exact version"
    assert (ROOT / "frontend/package-lock.json").is_file()


def test_python_requirements_are_pinned() -> None:
    for f in ("requirements.txt", "requirements-dev.txt", "ml/requirements-data.txt"):
        for line in (ROOT / f).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-r")):
                continue
            assert re.fullmatch(r"[A-Za-z0-9_.\-\[\]]+==[0-9][\w.]*", line), f"{f}: {line}"
