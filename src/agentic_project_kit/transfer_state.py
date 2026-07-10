from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentic_project_kit.rule_ack import (
    acknowledgement_from_json_data,
    validate_rule_acknowledgement,
)
from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot
from agentic_project_kit.workspace import load_workspace

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
    transfer_files: dict[str, Any] = field(default_factory=dict)
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
            "transfer_files": self.transfer_files,
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
    latest = load_workspace(project_root).latest_command_run_pointer()
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


def _read_key_value_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return {}
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"parse_error": "invalid_json"}
        return data if isinstance(data, dict) else {"parse_error": "json_root_not_object"}

    data: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\'\"")
        if key:
            data[key] = value
    return data


def _direct_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(item for item in path.iterdir() if item.is_file())


def _build_transfer_file_state(
    project_root: Path,
    *,
    branch: str,
    head: str,
    origin_main: str,
) -> dict[str, Any]:
    transfer_root = project_root / ".agentic" / "transfer"
    inbox_dir = transfer_root / "inbox"
    outbox_dir = transfer_root / "outbox"
    current_command = inbox_dir / "current.yaml"
    legacy_command = inbox_dir / "next_command.py.txt"
    last_result = outbox_dir / "last_result.txt"

    inbox_files = _direct_files(inbox_dir)
    outbox_files = _direct_files(outbox_dir)
    current_command_meta = _read_key_value_metadata(current_command)
    last_result_meta = _read_key_value_metadata(last_result)

    unexpected_inbox_files = [
        str(path.relative_to(project_root))
        for path in inbox_files
        if path.name not in {"current.yaml", "next_command.py.txt"}
    ]
    unexpected_outbox_files = [
        str(path.relative_to(project_root))
        for path in outbox_files
        if path.name != "last_result.txt"
    ]

    command_id = str(current_command_meta.get("command_id") or current_command_meta.get("id") or "")
    result_command_id = str(last_result_meta.get("command_id") or last_result_meta.get("id") or "")
    expected_branch = str(current_command_meta.get("expected_branch") or "")
    expected_head = str(current_command_meta.get("expected_head") or "")
    expected_origin_main = str(current_command_meta.get("expected_origin_main") or "")
    reasons: list[str] = []

    state = "NO_COMMAND"
    next_action = "queue_transfer_command"

    if unexpected_inbox_files or unexpected_outbox_files:
        state = "CONFLICT"
        next_action = "inspect_duplicate_or_obsolete_transfer_files"
        reasons.append("duplicate_or_obsolete_active_transfer_files")
    elif current_command.exists() and expected_origin_main and origin_main == "UNKNOWN":
        state = "REMOTE_UNREACHABLE"
        next_action = "retry_remote_check_later"
        reasons.append("expected_origin_main_unavailable")
    elif current_command.exists() and expected_branch and expected_branch != branch:
        state = "REMOTE_DRIFT"
        next_action = "sync_or_regenerate_command"
        reasons.append("expected_branch_mismatch")
    elif current_command.exists() and expected_head and expected_head != head:
        state = "REMOTE_DRIFT"
        next_action = "sync_or_regenerate_command"
        reasons.append("expected_head_mismatch")
    elif current_command.exists() and expected_origin_main and expected_origin_main != origin_main:
        state = "REMOTE_DRIFT"
        next_action = "sync_or_regenerate_command"
        reasons.append("expected_origin_main_mismatch")
    elif current_command.exists() and last_result.exists():
        if command_id and result_command_id and command_id == result_command_id:
            state = "RESULT_READY"
            next_action = "consume_result"
        else:
            state = "STALE_RESULT"
            next_action = "ignore_or_archive_stale_result"
            reasons.append("outbox_result_does_not_match_active_command")
    elif current_command.exists():
        state = "COMMAND_READY"
        next_action = "run_next_command"
    elif last_result.exists():
        state = "STALE_RESULT"
        next_action = "ignore_or_archive_stale_result"
        reasons.append("outbox_result_without_active_command")
    elif legacy_command.exists():
        state = "NO_COMMAND"
        next_action = "queue_or_migrate_legacy_transfer_command"
        reasons.append("legacy_next_command_present")

    return {
        "schema_version": 1,
        "state": state,
        "next": next_action,
        "reasons": reasons,
        "inbox": {
            "path": ".agentic/transfer/inbox",
            "current_command": {
                "path": ".agentic/transfer/inbox/current.yaml",
                "exists": current_command.exists(),
                "command_id": command_id,
                "expected_branch": expected_branch,
                "expected_head": expected_head,
                "expected_origin_main": expected_origin_main,
            },
            "legacy_next_command": {
                "path": ".agentic/transfer/inbox/next_command.py.txt",
                "exists": legacy_command.exists(),
            },
            "active_files": [str(path.relative_to(project_root)) for path in inbox_files],
            "unexpected_files": unexpected_inbox_files,
        },
        "observed": {
            "branch": branch,
            "head": head,
            "origin_main": origin_main,
        },
        "outbox": {
            "path": ".agentic/transfer/outbox",
            "last_result": {
                "path": ".agentic/transfer/outbox/last_result.txt",
                "exists": last_result.exists(),
                "command_id": result_command_id,
                "result_status": last_result_meta.get("result_status", ""),
            },
            "active_files": [str(path.relative_to(project_root)) for path in outbox_files],
            "unexpected_files": unexpected_outbox_files,
        },
    }


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
    origin_main = _run_git(root, "rev-parse", "--short", "origin/main") or "UNKNOWN"
    dirty = _read_dirty_worktree(root)
    reasons: list[str] = []

    if dirty:
        reasons.append("dirty_worktree")

    rule_snapshot = build_derived_rule_snapshot(root)
    if rule_snapshot.fail_closed:
        reasons.append("rule_snapshot_fail_closed")

    transfer_files = _build_transfer_file_state(
        root,
        branch=branch,
        head=head,
        origin_main=origin_main,
    )
    transfer_file_blocks = {"CONFLICT", "REMOTE_DRIFT", "REMOTE_UNREACHABLE"}
    if transfer_files["state"] in transfer_file_blocks:
        reasons.extend(transfer_files["reasons"])

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
    elif transfer_files["state"] in transfer_file_blocks:
        primary_state = PRIMARY_BLOCKED
        next_action = transfer_files["next"]
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

    transfer_file_blocked = transfer_files["state"] in transfer_file_blocks
    transfer_allowed = has_order and not dirty and rules_confirmed and not transfer_file_blocked
    clean_for_closeout = latest_result is not None and not dirty and rules_confirmed and not transfer_file_blocked

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
        transfer_files=transfer_files,
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


def _archive_transfer_file(project_root: Path, path: Path, archive_root: Path) -> str:
    relative = path.relative_to(project_root)
    target = archive_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = 1
    while target.exists():
        target = archive_root / f"{relative.as_posix()}.{suffix}"
        suffix += 1
    path.replace(target)
    return str(target.relative_to(project_root))


def _ensure_current_command_id(path: Path, *, command_id: str) -> bool:
    if not path.exists():
        return False
    metadata = _read_key_value_metadata(path)
    if metadata.get("command_id") or metadata.get("id"):
        return False
    original = path.read_text(encoding="utf-8")
    path.write_text(f"command_id: {command_id}\n" + original, encoding="utf-8")
    return True


def normalize_transfer_file_lifecycle(
    project_root: Path = Path("."),
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = project_root.resolve()
    before = build_transfer_state(root).transfer_files
    transfer_root = root / ".agentic" / "transfer"
    inbox_dir = transfer_root / "inbox"
    outbox_dir = transfer_root / "outbox"
    archive_root = transfer_root / "archive" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    current_command = inbox_dir / "current.yaml"
    last_result = outbox_dir / "last_result.txt"

    operations: list[dict[str, Any]] = []
    result_status = "PASS"
    reasons: list[str] = []

    if current_command.exists():
        metadata = _read_key_value_metadata(current_command)
        if not metadata.get("command_id") and not metadata.get("id"):
            command_id = "transfer-" + uuid4().hex
            operations.append(
                {
                    "operation": "ensure_command_id",
                    "path": ".agentic/transfer/inbox/current.yaml",
                    "command_id": command_id,
                    "applied": not dry_run,
                }
            )
            if not dry_run:
                _ensure_current_command_id(current_command, command_id=command_id)

    for file_path in before["inbox"]["unexpected_files"]:
        path = root / file_path
        operations.append(
            {
                "operation": "archive_unexpected_inbox_file",
                "path": file_path,
                "applied": not dry_run,
            }
        )
        if not dry_run and path.exists():
            operations[-1]["archive_path"] = _archive_transfer_file(root, path, archive_root)

    for file_path in before["outbox"]["unexpected_files"]:
        path = root / file_path
        operations.append(
            {
                "operation": "archive_unexpected_outbox_file",
                "path": file_path,
                "applied": not dry_run,
            }
        )
        if not dry_run and path.exists():
            operations[-1]["archive_path"] = _archive_transfer_file(root, path, archive_root)

    if before["state"] == "STALE_RESULT" and last_result.exists():
        operations.append(
            {
                "operation": "archive_stale_last_result",
                "path": ".agentic/transfer/outbox/last_result.txt",
                "applied": not dry_run,
            }
        )
        if not dry_run:
            operations[-1]["archive_path"] = _archive_transfer_file(root, last_result, archive_root)

    if before["state"] in {"REMOTE_DRIFT", "REMOTE_UNREACHABLE"}:
        reasons.append("transfer_remote_state_not_auto_recovered")

    after = before if dry_run else build_transfer_state(root).transfer_files
    if after["state"] == "CONFLICT":
        result_status = "BLOCKED"
        reasons.append("transfer_file_conflict_remains_after_normalization")

    return {
        "schema_version": 1,
        "kind": "transfer_file_lifecycle_normalization",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": dry_run,
        "before": before,
        "after": after,
        "operations": operations,
        "reasons": reasons,
        "next_action": "Run transfer state and inspect transfer_files.",
    }


def transfer_state_json(project_root: Path = Path(".")) -> str:
    return json.dumps(build_transfer_state(project_root).as_json_data(), indent=2, sort_keys=True)
