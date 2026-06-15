from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentic_project_kit.transfer_state import build_transfer_state


@dataclass(frozen=True)
class WorkflowNextResult:
    state: str
    next_action: str
    command: tuple[str, ...]
    returncode: int = 0
    reasons: tuple[str, ...] = field(default_factory=tuple)
    repo: dict[str, Any] = field(default_factory=dict)
    transfer_state: dict[str, Any] = field(default_factory=dict)

    @property
    def result_status(self) -> str:
        return "PASS" if self.returncode == 0 else "BLOCKED"

    def as_json_data(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "transfer_workflow_next_result",
            "result_status": self.result_status,
            "returncode": self.returncode,
            "state": self.state,
            "next_action": self.next_action,
            "next": self.next_action,
            "command": list(self.command),
            "reasons": list(self.reasons),
            "repo": self.repo,
            "transfer_state": self.transfer_state,
            "chat_reply": "g" if self.returncode == 0 else "f",
        }


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_text(root: Path, *args: str) -> str:
    result = _run_git(root, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _repo_snapshot(root: Path) -> dict[str, Any]:
    return {
        "branch": _git_text(root, "branch", "--show-current") or "UNKNOWN",
        "head": _git_text(root, "rev-parse", "HEAD") or "UNKNOWN",
        "origin_main": _git_text(root, "rev-parse", "origin/main") or "",
        "status_short": _git_text(root, "status", "--porcelain=v1"),
    }


def run_workflow_next(project_root: Path = Path(".")) -> WorkflowNextResult:
    root = project_root.resolve()
    repo = _repo_snapshot(root)

    if repo["status_short"]:
        return WorkflowNextResult(
            state="DIRTY_WORKTREE",
            next_action="Inspect or normalize the dirty worktree before continuing.",
            command=("./.venv/bin/agentic-kit", "transfer", "repo-status", "--full"),
            returncode=2,
            reasons=("dirty_worktree",),
            repo=repo,
        )

    if repo["branch"] != "main":
        return WorkflowNextResult(
            state="ON_FEATURE_BRANCH",
            next_action="Continue or complete the active branch workflow before returning to main.",
            command=("./.venv/bin/agentic-kit", "transfer", "continue", repo["branch"]),
            reasons=("feature_branch_active",),
            repo=repo,
        )

    if repo["origin_main"] and repo["head"] != repo["origin_main"]:
        return WorkflowNextResult(
            state="MAIN_NOT_SYNCED",
            next_action="Fast-forward local main from origin/main before deciding the next workflow step.",
            command=("./.venv/bin/agentic-kit", "transfer", "sync-main"),
            returncode=2,
            reasons=("main_not_synced",),
            repo=repo,
        )

    try:
        transfer_state = build_transfer_state(root).as_json_data()
    except Exception as exc:  # defensive read-only diagnostic
        return WorkflowNextResult(
            state="TRANSFER_STATE_UNREADABLE",
            next_action="Inspect transfer state diagnostics before continuing.",
            command=("./.venv/bin/agentic-kit", "transfer", "repo-status", "--full"),
            returncode=2,
            reasons=("transfer_state_unreadable", type(exc).__name__),
            repo=repo,
        )

    capabilities = transfer_state.get("capabilities", {})
    primary_state = str(transfer_state.get("primary_state") or "")
    next_action = str(transfer_state.get("next_action") or "")

    if isinstance(capabilities, dict) and capabilities.get("run_next_command") is True:
        return WorkflowNextResult(
            state="TRANSFER_READY",
            next_action=next_action or "Run the queued transfer command.",
            command=("./.venv/bin/agentic-kit", "transfer", "remote-next"),
            reasons=("transfer_ready",),
            repo=repo,
            transfer_state=transfer_state,
        )

    if primary_state and primary_state not in {"CLEAN_READY", "NO_COMMAND", "READY"}:
        return WorkflowNextResult(
            state=primary_state,
            next_action=next_action or "Inspect transfer state before continuing.",
            command=("./.venv/bin/agentic-kit", "transfer", "repo-status", "--full"),
            returncode=2,
            reasons=tuple(str(reason) for reason in transfer_state.get("reasons", ())),
            repo=repo,
            transfer_state=transfer_state,
        )

    return WorkflowNextResult(
        state="READY_FOR_PLANNED_WORK",
        next_action="Start the next planned safe slice from clean synced main.",
        command=(),
        repo=repo,
        transfer_state=transfer_state,
    )


def workflow_next_json(project_root: Path = Path(".")) -> str:
    return json.dumps(run_workflow_next(project_root).as_json_data(), indent=2, sort_keys=True)
