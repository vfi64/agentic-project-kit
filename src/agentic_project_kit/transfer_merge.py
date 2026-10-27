"""Explicit, locally approved merge lifecycle; never rewrite or push history."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from .workspace_lock import WorkspaceLockBusy, workspace_mutation_lock


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True,
                          timeout=120, env={**os.environ, "GIT_EDITOR": "true", "GIT_TERMINAL_PROMPT": "0"})


def _read(root: Path, *args: str) -> str:
    result = _git(root, *args)
    if result.returncode:
        raise ValueError("git observation failed: " + " ".join(args[:2]))
    return result.stdout


def _git_path(root: Path, name: str) -> Path:
    path = Path(_read(root, "rev-parse", "--git-path", name).strip())
    return path if path.is_absolute() else root / path


def _observe(root: Path, branch: str, upstream: str, action: str) -> tuple[dict, list[str]]:
    reasons = []
    current = _read(root, "branch", "--show-current").strip()
    head = _read(root, "rev-parse", "--verify", "HEAD").strip()
    if not branch or current != branch:
        reasons.append("branch_mismatch")
    if current in {"main", "master", "trunk"} or current == upstream.removeprefix("origin/"):
        reasons.append("refuse_main_branch")
    if not re.fullmatch(r"origin/[A-Za-z0-9][A-Za-z0-9/_.-]*", upstream) or ".." in upstream:
        reasons.append("invalid_upstream_ref")
    if action not in {"start", "continue", "abort"}:
        reasons.append("invalid_action")
    if any(_git_path(root, name).exists() for name in ("rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD", "REVERT_HEAD")):
        reasons.append("other_git_operation_active")
    merge_path = _git_path(root, "MERGE_HEAD")
    merging = merge_path.exists()
    if action == "start" and merging:
        reasons.append("merge_already_active")
    if action != "start" and not merging:
        reasons.append("no_merge_in_progress")
    if merging:
        target = merge_path.read_text(encoding="utf-8").strip()
    elif "invalid_upstream_ref" not in reasons:
        target = _read(root, "rev-parse", "--verify", upstream + "^{commit}").strip()
    else:
        target = ""
    if not re.fullmatch(r"[a-f0-9]{40}", target):
        reasons.append("invalid_target_commit")
    # The lock itself is not user work; no other untracked path is ignored.
    status = [s for s in _read(root, "status", "--porcelain=v1", "--untracked-files=all", "-z").split("\0")
              if s and s != "?? .agentic/tmp/workspace.lock"]
    unmerged = [p for p in _read(root, "diff", "--name-only", "--diff-filter=U", "-z").split("\0") if p]
    if action == "start" and status:
        reasons.append("dirty_worktree")
    if action == "continue":
        if unmerged:
            reasons.append("unresolved_conflicts")
        if _read(root, "diff", "--name-only", "-z"):
            reasons.append("unstaged_changes")
        if any(s.startswith("?? ") for s in status):
            reasons.append("untracked_files")
    message = _git_path(root, "MERGE_MSG")
    digest = hashlib.sha256(_read(root, "diff", "--cached", "--binary").encode()).hexdigest()
    plan = {"action": action, "branch": current, "head": head, "upstream": upstream,
            "target_commit": target, "merge_active": merging, "status": status,
            "unmerged_files": unmerged, "index_sha256": digest,
            "message_sha256": hashlib.sha256(message.read_bytes()).hexdigest() if message.exists() else None}
    return plan, reasons


def _signature(plan: dict) -> str:
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]


def _blocked(reasons: list[str], plan: dict | None = None) -> dict:
    return {"result_status": "BLOCKED", "returncode": 2, "reasons": reasons, "plan": plan,
            "next_safe_action": "Inspect the reasons; preserve work and request a new preview after correcting the cause."}


def merge_upstream(root: Path, *, branch: str, upstream: str = "origin/main", action: str = "start",
                   execute: bool = False, expected_signature: str = "") -> dict:
    """Preview then approve exactly one start/continue/abort action on local Git state."""
    root = root.resolve()
    try:
        plan, reasons = _observe(root, branch, upstream, action)
        if reasons:
            return _blocked(reasons, plan)
        signature = _signature(plan)
        if not execute:
            return {"result_status": "AWAITING_APPROVAL", "returncode": 0, "plan": plan,
                    "approval_signature": signature, "reasons": [],
                    "next_safe_action": "Review the plan, then execute this action with its expected signature."}
        if not expected_signature or signature != expected_signature:
            return _blocked(["approval_signature_mismatch"], plan)
        with workspace_mutation_lock(root, "transfer merge-upstream"):
            checked, reasons = _observe(root, branch, upstream, action)
            if reasons or _signature(checked) != signature:
                return _blocked(reasons or ["approval_signature_mismatch"], checked)
            if action == "start":
                result = _git(root, "merge", "--no-commit", "--no-ff", plan["target_commit"])
            elif action == "continue":
                result = _git(root, "merge", "--continue")
            else:
                result = _git(root, "merge", "--abort")
            unmerged = [p for p in _read(root, "diff", "--name-only", "--diff-filter=U", "-z").split("\0") if p]
            active = _git_path(root, "MERGE_HEAD").exists()
            if result.returncode:
                status = "CONFLICT" if action == "start" and active and unmerged else "FAIL"
            elif action == "start":
                status = "READY_TO_COMMIT" if active else "NOOP"
            else:
                status = "PASS" if not active else "FAIL"
            return {"result_status": status, "returncode": 2 if status in {"CONFLICT", "FAIL"} else 0,
                    "plan": plan, "unmerged_files": unmerged, "merge_active": active,
                    "git_returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                    "next_safe_action": (
                        "Resolve the listed files through the Kit; regenerate generated artifacts with their owners, then preview continue."
                        if status == "CONFLICT" else
                        "Review staged changes and preview continue; preview abort to discard this merge instead."
                        if status == "READY_TO_COMMIT" else
                        "Inspect failure evidence; do not retry or discard it automatically."
                        if status == "FAIL" else "Merge action complete; inspect repository status before any push.")}
    except (ValueError, OSError, subprocess.TimeoutExpired, WorkspaceLockBusy) as exc:
        return _blocked([str(exc)])
