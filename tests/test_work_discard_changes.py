from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_project_kit.work_discard_changes import (
    discard_all_changes,
    discard_signature,
    parse_porcelain_status,
)


def _completed(argv: list[str], stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def test_parse_porcelain_status_lists_tracked_and_untracked_paths() -> None:
    changes = parse_porcelain_status(" M src/app.py\n?? new.txt\nR  old.py -> renamed.py\n")

    assert [change.path for change in changes] == ["src/app.py", "new.txt", "renamed.py"]


def test_discard_changes_dry_run_does_not_execute_reset_or_clean(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_runner(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        if argv == ["git", "branch", "--show-current"]:
            return _completed(argv, "codex/demo\n")
        if argv == ["git", "status", "--porcelain=v1", "--untracked-files=all"]:
            return _completed(argv, " M src/app.py\n?? new.txt\n")
        return _completed(argv, returncode=99, stderr="unexpected")

    result = discard_all_changes(tmp_path, runner=fake_runner)

    assert result["result_status"] == "PASS"
    assert result["dry_run"] is True
    assert result["destructive"] is True
    assert result["changed_paths"] == ["src/app.py", "new.txt"]
    assert ["git", "reset", "--hard", "HEAD"] not in calls
    assert not any(call[:3] == ["git", "clean", "-fd"] for call in calls)


def test_discard_changes_blocks_on_main(tmp_path: Path) -> None:
    def fake_runner(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if argv == ["git", "branch", "--show-current"]:
            return _completed(argv, "main\n")
        if argv == ["git", "status", "--porcelain=v1", "--untracked-files=all"]:
            return _completed(argv, " M src/app.py\n")
        return _completed(argv)

    result = discard_all_changes(tmp_path, execute=True, runner=fake_runner)

    assert result["result_status"] == "BLOCKED"
    assert "main-branch" in result["blockers"]


def test_discard_changes_execute_requires_matching_signature_when_supplied(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_runner(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        if argv == ["git", "branch", "--show-current"]:
            return _completed(argv, "codex/demo\n")
        if argv == ["git", "status", "--porcelain=v1", "--untracked-files=all"]:
            return _completed(argv, " M src/app.py\n")
        return _completed(argv)

    result = discard_all_changes(tmp_path, execute=True, expected_signature="wrong", runner=fake_runner)

    assert result["result_status"] == "BLOCKED"
    assert "signature-mismatch" in result["blockers"]
    assert ["git", "reset", "--hard", "HEAD"] not in calls


def test_discard_changes_execute_resets_tracked_and_cleans_untracked(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    status = " M src/app.py\n?? new.txt\n"
    signature = discard_signature("codex/demo", status)

    def fake_runner(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        if argv == ["git", "branch", "--show-current"]:
            return _completed(argv, "codex/demo\n")
        if argv == ["git", "status", "--porcelain=v1", "--untracked-files=all"]:
            return _completed(argv, status)
        if argv == ["git", "reset", "--hard", "HEAD"]:
            return _completed(argv, "HEAD is now at demo\n")
        if argv == ["git", "clean", "-fd", "--", "new.txt"]:
            return _completed(argv, "Removing new.txt\n")
        return _completed(argv, returncode=99, stderr=f"unexpected command: {argv}")

    result = discard_all_changes(tmp_path, execute=True, expected_signature=signature, runner=fake_runner)

    assert result["result_status"] == "PASS"
    assert ["git", "reset", "--hard", "HEAD"] in calls
    assert ["git", "clean", "-fd", "--", "new.txt"] in calls
