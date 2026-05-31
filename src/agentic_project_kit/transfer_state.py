from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_project_kit.rule_ack import (
    acknowledgement_from_json_data,
    validate_rule_acknowledgement,
)
from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot

PRIMARY_READY = "READY"
PRIMARY_WAIT = "WAIT"
PRIMARY_BLOCKED = "BLOCKED"
PRIMARY_FAILED = "FAILED"


@dataclass(frozen=True)
class TransferStateSnapshot:
    schema_version: int
    created_at: str
    repo: str
    branch: str
    head: str
    primary_state: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    next_action: str = ""
    capabilities: dict[str, bool] = field(default_factory=dict)
    last_result: dict[str, Any] | None = None
    closeout: dict[str, Any] = field(default_factory=dict)
    rule_snapshot: dict[str, Any] = field(default_factory=dict)
    rule_acknowledgement: dict[str, Any] = field(default_factory=dict)

    def as_json_data(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "repo": self.repo,
            "branch": self.branch,
            "head": self.head,
            "primary_state": self.primary_state,
            "reasons": list(self.reasons),
            "next_action": self.next_action,
            "capabilities": self.capabilities,
            "last_result": self.last_result,
            "closeout": self.closeout,
            "rule_snapshot": self.rule_snapshot,
            "rule_acknowledgement": self.rule_acknowledgement,
        }


def _run_git(project_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        return ""
    return process.stdout.strip()


def _read_repo_name(project_root: Path) -> str:
    remote_url = _run_git(project_root, "config", "--get", "remote.origin.url")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    if ":" in remote_url and "/" in remote_url:
        return remote_url.rsplit(":", 1)[-1]
    if "github.com/" in remote_url:
        return remote_url.rsplit("github.com/", 1)[-1]
    return Path(project_root).name


def _read_latest_result(project_root: Path) -> dict[str, Any] | None:
    latest = project_root / "docs/reports/command_runs/LATEST_COMMAND_RUN.txt"
    if not latest.exists():
        return None
    report_path = latest.read_text(encoding="utf-8").strip()
    if not report_path:
        return None
    report = project_root / report_path
    return {"report_path": report_path, "exists": report.exists()}


def _read_dirty_worktree(project_root: Path) -> str:
    status = _run_git(project_root, "status", "--short")
    kept_lines: list[str] = []
    for line in status.splitlines():
        path_text = line[3:] if len(line) > 3 else ""
        if path_text == ".agentic/rule_ack/current.json":
            continue
        if path_text.startswith(".agentic/rule_ack/"):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _has_pending_transfer_order(project_root: Path) -> bool:
    return (project_root / ".agentic/transfer/inbox/current.yaml").exists()


def _read_rule_acknowledgement(project_root: Path):
    path = project_root / ".agentic/rule_ack/current.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return acknowledgement_from_json_data(data)


def build_transfer_state(project_root: Path = Path(".")) -> TransferStateSnapshot:
    root = project_root.resolve()
    branch = _run_git(root, "branch", "--show-current") or "UNKNOWN"
    head = _run_git(root, "rev-parse", "--short", "HEAD") or "UNKNOWN"
    dirty = _read_dirty_worktree(root)
    reasons: list[str] = []

    if dirty:
        reasons.append("dirty_worktree")

    rule_snapshot = build_derived_rule_snapshot(root)
    if rule_snapshot.fail_closed:
        reasons.append("rule_snapshot_fail_closed")

    has_order = _has_pending_transfer_order(root)
    latest_result = _read_latest_result(root)
    acknowledgement = _read_rule_acknowledgement(root)
    acknowledgement_decision = validate_rule_acknowledgement(
        rule_snapshot,
        acknowledgement,
        repo_head=head,
        required_next_allowed_action="run_next_command",
    )
    if acknowledgement_decision.fail_closed:
        reasons.extend(acknowledgement_decision.blocking_reasons)

    rules_confirmed = acknowledgement_decision.is_confirmed

    if dirty:
        primary_state = PRIMARY_BLOCKED
        next_action = "Review or clean the worktree before running another transfer action."
    elif rule_snapshot.fail_closed:
        primary_state = PRIMARY_BLOCKED
        next_action = "Repair canonical rule sources before running transfer actions."
    elif not rules_confirmed:
        primary_state = PRIMARY_WAIT
        next_action = "Acknowledge the current rule snapshot before running transfer actions."
    elif has_order:
        primary_state = PRIMARY_READY
        next_action = "Run agentic-kit transfer inspect before apply."
    else:
        primary_state = PRIMARY_WAIT
        next_action = "Queue a transfer order or continue with a read-only diagnostic action."

    transfer_allowed = has_order and not dirty and rules_confirmed
    clean_for_closeout = latest_result is not None and not dirty and rules_confirmed

    capabilities = {
        "refresh_rules": True,
        "run_next_command": transfer_allowed,
        "closeout_last_run": clean_for_closeout,
        "diagnose": True,
        "rules_confirmed": rules_confirmed,
    }

    return TransferStateSnapshot(
        schema_version=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        repo=_read_repo_name(root),
        branch=branch,
        head=head,
        primary_state=primary_state,
        reasons=tuple(reasons),
        next_action=next_action,
        capabilities=capabilities,
        last_result=latest_result,
        closeout={
            "pending_transfer_order": has_order,
            "dirty_worktree": bool(dirty),
        },
        rule_snapshot=rule_snapshot.as_json_data(),
        rule_acknowledgement={
            "path": ".agentic/rule_ack/current.json",
            "present": acknowledgement is not None,
            "decision": acknowledgement_decision.as_json_data(),
        },
    )


def transfer_state_json(project_root: Path = Path(".")) -> str:
    return json.dumps(build_transfer_state(project_root).as_json_data(), indent=2, sort_keys=True)
