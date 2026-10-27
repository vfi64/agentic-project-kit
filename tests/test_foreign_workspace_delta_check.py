"""Acceptance harness must fail closed and exercise real external profiles."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("foreign_delta", ROOT / "scripts/foreign_workspace_delta_check.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_zero_exit_blocked_payload_is_not_accepted(monkeypatch, tmp_path):
    monkeypatch.setattr(AUDIT.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess([], 0, '{"result_status":"BLOCKED"}', ""))
    with pytest.raises(ValueError, match="Blocked command despite rc 0"):
        AUDIT.invoke(tmp_path, ROOT, [], "workspace", "init", "--json")


def test_actual_swift_candidate_recovers_all_profiles_and_commits_selectively(tmp_path, monkeypatch):
    # Make the installed console script explicit without adding a runtime route.
    executable = Path(sys.executable).parent / "agentic-kit"
    if not executable.is_file():
        executable = Path(shutil.which("agentic-kit") or "")
    assert executable.is_file(), "installed Kit console required"
    monkeypatch.setenv("PATH", str(executable.parent) + os.pathsep + os.environ["PATH"])
    root = tmp_path / "swift"
    AUDIT.fixture(root)
    records = []
    AUDIT.negative_checks(root, ROOT, records, baseline=False)
    AUDIT.acceptance(root, ROOT, records)
    passed_profiles = [r["command"][4] for r in records
                       if r["command"][1:3] == ["work", "check"] and r["rc"] == 0]
    assert passed_profiles == list(AUDIT.PROFILES)
    assert not (root / "tests").exists()
