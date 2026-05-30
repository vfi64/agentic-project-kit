from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.transfer_local_runner import TransferLocalRun, run_local_transfer


@dataclass(frozen=True)
class TransferRemoteNextRun:
    branch: str
    local_run: TransferLocalRun
    head: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "branch": self.branch,
            "head": self.head,
            "local_run": self.local_run.as_json_data(),
            "result_status": self.local_run.result_status,
            "returncode": self.local_run.returncode,
            "next_action": self.local_run.next_action,
        }


def _run(argv: list[str], cwd: Path) -> str:
    process = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(argv)}\nstdout={process.stdout}\nstderr={process.stderr}"
        )
    return process.stdout.strip()


def _ensure_clean(project_root: Path) -> None:
    status = _run(["git", "status", "--short"], project_root)
    if status:
        raise RuntimeError(f"worktree must be clean before transfer remote-next:\n{status}")


def _validate_branch_name(branch: str) -> str:
    value = branch.strip()
    if not value:
        raise ValueError("branch must not be empty")
    if value.startswith("-") or ".." in value or value.endswith(".lock"):
        raise ValueError(f"unsafe branch name: {branch}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-")
    if any(char not in allowed for char in value):
        raise ValueError(f"unsafe branch name: {branch}")
    return value


def run_remote_next_transfer(project_root: Path, branch: str) -> TransferRemoteNextRun:
    root = project_root.resolve()
    safe_branch = _validate_branch_name(branch)

    _ensure_clean(root)
    _run(["git", "fetch", "origin", safe_branch], root)
    _run(["git", "switch", safe_branch], root)
    _run(["git", "pull", "--ff-only", "origin", safe_branch], root)

    local_run = run_local_transfer(root)
    head = _run(["git", "rev-parse", "--short", "HEAD"], root)
    return TransferRemoteNextRun(branch=safe_branch, local_run=local_run, head=head)
