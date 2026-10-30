"""Reusable evidence within one trusted Kit closeout chain, never authorization.

Any unavailable or changed input declines reuse; callers retain their full checks.
No receipt is persisted and no user-facing prose is interpreted as proof.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess

from agentic_project_kit.workspace import load_workspace

_TERMINAL = {"NOOP", "COMPLETE", "REFRESH_ONLY_PR_NOOP"}
_SHA = re.compile(r"[0-9a-f]{40}")


def _json_value(value):
    if is_dataclass(value):
        return {field.name: getattr(value, field.name) for field in fields(value)}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError("Unsupported workspace value")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError("Repository observation unavailable")
    return result.stdout.strip()


def _local_state(root: Path, main_branch: str) -> dict[str, object]:
    root = root.resolve()
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("Not repository root")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("Dirty worktree")
    git_dir = Path(_git(root, "rev-parse", "--absolute-git-dir"))
    if any(
        (git_dir / name).exists()
        for name in (
            "MERGE_HEAD",
            "CHERRY_PICK_HEAD",
            "REVERT_HEAD",
            "rebase-merge",
            "rebase-apply",
            "BISECT_LOG",
        )
    ):
        raise ValueError("Repository operation in progress")
    head = _git(root, "rev-parse", "HEAD")
    if not _SHA.fullmatch(head) or _git(root, "branch", "--show-current") != main_branch:
        raise ValueError("Not final main branch")
    upstream = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream != f"origin/{main_branch}" or _git(root, "rev-parse", "@{upstream}") != head:
        raise ValueError("Upstream mismatch")
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    package = ws.handoff_packages_latest()
    required = {
        "validation_report.json",
        "execution_contract.json",
        "source_manifest.json",
        "successor_context.yaml",
    }
    if not all((package / name).is_file() for name in required):
        raise ValueError("Incomplete handoff evidence")
    if json.loads((package / "validation_report.json").read_text())["status"] != "PASS":
        raise ValueError("Handoff not PASS")
    files = sorted(path for path in package.rglob("*") if path.is_file())
    files += [ws.handoff_state_path(), ws.operational_handoff_state_path(), ws.rule_registry_path()]
    evidence = {
        str(path.relative_to(root)): _digest(path.read_bytes()) if path.is_file() else None
        for path in files
    }
    return {
        "repository": _digest(str(root).encode()),
        "head": head,
        "branch": main_branch,
        "upstream": upstream,
        "origin": _digest(_git(root, "remote", "get-url", "origin").encode()),
        "workspace": _digest(json.dumps(ws, sort_keys=True, default=_json_value).encode()),
        "evidence": evidence,
    }


def _snapshot(root: Path, main_branch: str) -> dict[str, object] | None:
    try:
        before = _local_state(root, main_branch)
        remote = _git(
            root, "ls-remote", "--exit-code", "origin", f"refs/heads/{main_branch}"
        ).split()
        if remote != [before["head"], f"refs/heads/{main_branch}"]:
            return None
        return before if before == _local_state(root, main_branch) else None
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return None


def make_completion_receipt(
    root: Path, *, after_pr: int, main_branch: str, lifecycle_state: str
) -> dict[str, object] | None:
    """Called only after successful lifecycle, carrier refresh and cleanup."""
    if (
        type(after_pr) is not int
        or after_pr <= 0
        or not isinstance(lifecycle_state, str)
        or lifecycle_state not in _TERMINAL
    ):
        return None
    state = _snapshot(root, main_branch)
    if state is None:
        return None
    return {
        "kind": "closeout_completion_receipt",
        "schema_version": 1,
        "after_pr": after_pr,
        "lifecycle_state": lifecycle_state,
        "state": state,
    }


def valid_completion_receipt(
    payload: object, root: Path, *, after_pr: int, main_branch: str, source_head: str | None = None
) -> bool:
    """Verify child success and exact current state; malformed/legacy means fallback."""
    if not isinstance(payload, dict) or payload.get("result_status") != "PASS":
        return False
    if payload.get("returncode", 0) != 0:
        return False
    if source_head is not None and (
        not isinstance(source_head, str)
        or not _SHA.fullmatch(source_head)
        or payload.get("expected_head_sha") != source_head
    ):
        return False
    receipt = payload.get("completion_receipt")
    if not isinstance(receipt, dict) or receipt.get("kind") != "closeout_completion_receipt":
        return False
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1:
        return False
    if (
        type(after_pr) is not int
        or after_pr <= 0
        or type(receipt.get("after_pr")) is not int
        or receipt["after_pr"] != after_pr
    ):
        return False
    if (
        not isinstance(receipt.get("lifecycle_state"), str)
        or receipt["lifecycle_state"] not in _TERMINAL
    ):
        return False
    state = _snapshot(root, main_branch)
    return state is not None and receipt.get("state") == state
