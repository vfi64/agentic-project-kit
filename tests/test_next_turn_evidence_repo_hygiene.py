from __future__ import annotations

import subprocess


FORBIDDEN_TRACKED_NEXT_TURN_EVIDENCE = {
    "docs/reports/terminal/next-turn-latest.log",
    "docs/reports/command_runs/next-turn-latest.json",
    "docs/reports/terminal/smoke-a10.log",
    "docs/reports/command_runs/smoke-a10.json",
    "docs/reports/terminal/verify-a10.log",
    "docs/reports/command_runs/verify-a10.json",
}


def git_ls_files() -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        text=True,
        capture_output=True,
        check=True,
    )
    return set(completed.stdout.splitlines())


def test_next_turn_transient_evidence_is_not_tracked() -> None:
    tracked = git_ls_files()
    assert not (FORBIDDEN_TRACKED_NEXT_TURN_EVIDENCE & tracked)
