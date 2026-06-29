from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import subprocess
from typing import Callable


Runner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]

MAIN_BRANCHES = {"main", "master"}


@dataclass(frozen=True)
class WorktreeChange:
    status: str
    path: str


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _step(name: str, completed: subprocess.CompletedProcess[str], *, allowed: set[int] | None = None) -> dict[str, object]:
    allowed_returncodes = allowed or {0}
    return {
        "name": name,
        "argv": list(completed.args) if isinstance(completed.args, list) else [],
        "returncode": completed.returncode,
        "ok": completed.returncode in allowed_returncodes,
        "allowed_returncodes": sorted(allowed_returncodes),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def parse_porcelain_status(status_text: str) -> tuple[WorktreeChange, ...]:
    changes: list[WorktreeChange] = []
    for raw_line in status_text.splitlines():
        if len(raw_line) < 4:
            continue
        status = raw_line[:2]
        path = raw_line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip().strip('"')
        if path:
            changes.append(WorktreeChange(status=status, path=path))
    return tuple(changes)


def discard_signature(branch: str, status_text: str) -> str:
    material = f"{branch}\0{status_text}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _untracked_paths(changes: tuple[WorktreeChange, ...]) -> list[str]:
    return [change.path for change in changes if change.status == "??"]


def _payload(
    *,
    branch: str,
    status_text: str,
    dry_run: bool,
    execute: bool,
    steps: list[dict[str, object]],
    blockers: list[str] | None = None,
) -> dict[str, object]:
    changes = parse_porcelain_status(status_text)
    all_blockers = [*(blockers or ()), *[str(step["name"]) for step in steps if not step["ok"]]]
    result_status = "PASS" if not all_blockers else "BLOCKED"
    signature = discard_signature(branch, status_text)
    return {
        "schema_version": 1,
        "kind": "human_work_discard_changes_result",
        "action": "work-discard-changes",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": dry_run,
        "execute": execute,
        "destructive": True,
        "branch": branch,
        "signature": signature,
        "changed_paths": [change.path for change in changes],
        "untracked_paths": _untracked_paths(changes),
        "blockers": all_blockers,
        "steps": steps,
        "next_action": (
            "Confirm discard to remove all feature-branch changes."
            if dry_run and changes and result_status == "PASS"
            else "Workflow completed."
            if result_status == "PASS"
            else "Inspect blockers before discarding changes."
        ),
    }


def discard_all_changes(
    root: Path | str = ".",
    *,
    execute: bool = False,
    expected_signature: str = "",
    runner: Runner = _run,
) -> dict[str, object]:
    base = Path(root)
    branch_completed = runner(["git", "branch", "--show-current"], base)
    branch_step = _step("current-branch", branch_completed)
    branch = branch_completed.stdout.strip() if branch_completed.returncode == 0 else ""
    status_completed = runner(["git", "status", "--porcelain=v1", "--untracked-files=all"], base)
    status_step = _step("status-porcelain", status_completed)
    steps = [branch_step, status_step]
    status_text = status_completed.stdout if status_completed.returncode == 0 else ""
    blockers: list[str] = []
    if branch in MAIN_BRANCHES or not branch:
        blockers.append("main-branch")
    if expected_signature and expected_signature != discard_signature(branch, status_text):
        blockers.append("signature-mismatch")
    if not execute:
        return _payload(branch=branch, status_text=status_text, dry_run=True, execute=False, steps=steps, blockers=blockers)
    if blockers or any(not bool(step["ok"]) for step in steps):
        return _payload(branch=branch, status_text=status_text, dry_run=False, execute=True, steps=steps, blockers=blockers)
    reset_completed = runner(["git", "reset", "--hard", "HEAD"], base)
    steps.append(_step("reset-hard", reset_completed))
    untracked = _untracked_paths(parse_porcelain_status(status_text))
    if untracked and reset_completed.returncode == 0:
        clean_completed = runner(["git", "clean", "-fd", "--", *untracked], base)
        steps.append(_step("clean-untracked", clean_completed))
    return _payload(branch=branch, status_text=status_text, dry_run=False, execute=True, steps=steps, blockers=blockers)
