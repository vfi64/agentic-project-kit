from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CommitGuardResult:
    ok: bool
    branch: str
    dirty: bool
    messages: tuple[str, ...]


def _run_git(repo_root: Path, args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def evaluate_commit_guard(repo_root: Path) -> CommitGuardResult:
    branch_rc, branch_output = _run_git(repo_root, ["branch", "--show-current"])
    if branch_rc != 0:
        return CommitGuardResult(False, "", False, (branch_output or "ERROR: unable to determine current branch.",))

    branch = branch_output.strip()
    if branch == "main":
        return CommitGuardResult(
            False,
            branch,
            False,
            (
                "ERROR: refusing commit/PR workflow on main.",
                "Create a feature or docs branch first, then rerun the commit/PR workflow.",
                "Expected action: create a feature or docs branch first.",
            ),
        )

    status_rc, status_output = _run_git(repo_root, ["status", "--porcelain"])
    if status_rc != 0:
        return CommitGuardResult(False, branch, False, (status_output or "ERROR: unable to read git status.",))

    dirty = bool(status_output.strip())
    if dirty:
        messages = (f"Commit/PR guard passed on branch: {branch}",)
    else:
        messages = (f"No local changes detected on branch: {branch}",)
    return CommitGuardResult(True, branch, dirty, messages)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    result = evaluate_commit_guard(Path(".").resolve())
    for message in result.messages:
        print(message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
