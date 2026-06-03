from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from agentic_project_kit.transfer_local_runner import TransferLocalRun, run_local_transfer
from agentic_project_kit.transfer_runner import DEFAULT_INBOX
from agentic_project_kit.transfer_safety_context import build_local_to_llm_payload

REMOTE_NEXT_REPORT_DIR = Path("docs/reports/transfer_runs")
REMOTE_NEXT_LATEST_JSON = REMOTE_NEXT_REPORT_DIR / "latest-remote-next-report.json"
REMOTE_NEXT_LATEST_LOG = REMOTE_NEXT_REPORT_DIR / "latest-remote-next-report.log"
PUBLISHED_REPORT_DIR = Path("docs/reports/terminal/transfer_handoff_reports")
PUBLISHED_LATEST_JSON = PUBLISHED_REPORT_DIR / "latest-transfer-handoff-report.json"
PUBLISHED_LATEST_LOG = PUBLISHED_REPORT_DIR / "latest-transfer-handoff-report.log"
RULE_ACK_PATH = Path(".agentic/rule_ack/current.json")


@dataclass(frozen=True)
class GitSnapshot:
    current_branch: str
    head: str
    remote_tracking: str
    status_short: str
    staged_changes: tuple[str, ...] = field(default_factory=tuple)
    unstaged_changes: tuple[str, ...] = field(default_factory=tuple)
    untracked_files: tuple[str, ...] = field(default_factory=tuple)

    @property
    def clean(self) -> bool:
        return not self.status_short.strip()

    def as_json_data(self) -> dict[str, object]:
        return {
            "current_branch": self.current_branch,
            "head": self.head,
            "remote_tracking": self.remote_tracking,
            "dirty_state": {
                "clean": self.clean,
                "status_short": self.status_short,
                "staged_changes": list(self.staged_changes),
                "unstaged_changes": list(self.unstaged_changes),
                "untracked_files": list(self.untracked_files),
            },
        }


@dataclass(frozen=True)
class RuleAckSnapshot:
    present: bool
    confirmed: bool
    path: str = str(RULE_ACK_PATH)
    head: str = ""
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_json_data(self) -> dict[str, object]:
        return {
            "path": self.path,
            "present": self.present,
            "confirmed": self.confirmed,
            "head": self.head,
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass(frozen=True)
class TransferRemoteNextRun:
    branch: str | None
    local_run: TransferLocalRun
    head: str
    result_status: str
    returncode: int
    next_action: str
    report_path: str
    published_report_path: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    preflight: dict[str, object] = field(default_factory=dict)
    rule_ack: RuleAckSnapshot | None = None
    blocked_message: str = ""

    def as_json_data(self) -> dict[str, object]:
        primary_state = "BLOCKED" if self.result_status == "BLOCKED" else self.result_status
        return {
            "schema_version": 1,
            "artifact_type": "transfer_remote_next_execution_report",
            "branch": self.branch,
            "head": self.head,
            "result_status": self.result_status,
            "primary_state": primary_state,
            "returncode": self.returncode,
            "next_action": self.next_action,
            "chat_reply": "g",
            "report_path": self.report_path,
            "published_report_path": self.published_report_path,
            "reasons": list(self.reasons),
            "blocked_message": self.blocked_message,
            "preflight": self.preflight,
            "rule_ack": self.rule_ack.as_json_data() if self.rule_ack else None,
            "local_run": self.local_run.as_json_data(),
        }


@dataclass(frozen=True)
class _CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


class RemoteNextBlocked(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        reasons: tuple[str, ...],
        branch: str | None = None,
    ):
        super().__init__(message)
        self.reasons = reasons
        self.branch = branch


def _command(argv: list[str], cwd: Path) -> _CommandResult:
    process = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return _CommandResult(
        tuple(argv),
        process.returncode,
        process.stdout.strip(),
        process.stderr.strip(),
    )


def _run(argv: list[str], cwd: Path) -> str:
    result = _command(argv, cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(argv)}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result.stdout.strip()


def _status_paths(
    status_short: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    for line in status_short.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if status == "??":
            untracked.append(path)
            continue
        if status[0] != " ":
            staged.append(path)
        if status[1] != " ":
            unstaged.append(path)
    return tuple(staged), tuple(unstaged), tuple(untracked)


def _git_snapshot(project_root: Path) -> GitSnapshot:
    status = _command(["git", "status", "--short"], project_root).stdout
    staged, unstaged, untracked = _status_paths(status)
    return GitSnapshot(
        current_branch=(
            _command(["git", "branch", "--show-current"], project_root).stdout or "UNKNOWN"
        ),
        head=_command(["git", "rev-parse", "--short", "HEAD"], project_root).stdout or "UNKNOWN",
        remote_tracking=_command(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            project_root,
        ).stdout,
        status_short=status,
        staged_changes=staged,
        unstaged_changes=unstaged,
        untracked_files=untracked,
    )


def _rule_ack_snapshot(project_root: Path, *, repo_head: str) -> RuleAckSnapshot:
    path = project_root / RULE_ACK_PATH
    if not path.exists():
        return RuleAckSnapshot(False, False, blocking_reasons=("missing_rule_ack",))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return RuleAckSnapshot(True, False, blocking_reasons=("invalid_rule_ack_json",))
    if not isinstance(data, dict):
        return RuleAckSnapshot(True, False, blocking_reasons=("invalid_rule_ack_shape",))

    ack_head = str(data.get("repo_head") or data.get("head") or "")
    reasons: list[str] = []
    if ack_head and ack_head != repo_head:
        reasons.append("stale_rule_ack")
    confirmed = not reasons
    return RuleAckSnapshot(True, confirmed, head=ack_head, blocking_reasons=tuple(reasons))


def _ensure_clean(project_root: Path, *, branch: str | None) -> None:
    snapshot = _git_snapshot(project_root)
    if snapshot.status_short:
        raise RemoteNextBlocked(
            f"worktree must be clean before transfer remote-next:\n{snapshot.status_short}",
            reasons=("dirty_worktree",),
            branch=branch,
        )


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


def _read_transfer_order_data(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"transfer order not found: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"transfer order must be a mapping: {path}")
    return data


def resolve_remote_next_branch(
    project_root: Path,
    branch: str | None = None,
    path: Path = DEFAULT_INBOX,
) -> str:
    if branch is not None and branch.strip():
        return _validate_branch_name(branch)
    root = project_root.resolve()
    order_path = path if path.is_absolute() else root / path
    data = _read_transfer_order_data(order_path)
    order_branch = data.get("branch")
    if not isinstance(order_branch, str) or not order_branch.strip():
        raise ValueError(f"transfer order must define a non-empty branch: {path}")
    return _validate_branch_name(order_branch)


def _blocked_local_run(
    message: str,
    reasons: tuple[str, ...],
    snapshot: GitSnapshot,
) -> TransferLocalRun:
    state = {
        "schema_version": 1,
        "primary_state": "BLOCKED",
        "reasons": list(reasons),
        "next_action": "Inspect the published remote-next diagnostic report before retrying.",
        "branch": snapshot.current_branch,
        "head": snapshot.head,
        "dirty_state": snapshot.as_json_data()["dirty_state"],
    }
    inspect = {
        "schema_version": 1,
        "result_status": "BLOCKED",
        "returncode": 2,
        "message": message,
        "reasons": list(reasons),
    }
    return TransferLocalRun(
        schema_version=1,
        transfer_id="remote-next-blocked",
        inspect=inspect,
        apply=None,
        state=state,
        result_status="BLOCKED",
        returncode=2,
        next_action="Inspect the published remote-next diagnostic report before retrying.",
    )


def _remote_next_payload(root: Path, data: dict[str, object]) -> dict[str, object]:
    payload = build_local_to_llm_payload(
        root,
        data,
        kind="local_to_llm_remote_next_report",
    )
    payload["remote_next_report"] = data
    return payload


def _write_remote_next_report(root: Path, result: TransferRemoteNextRun) -> TransferRemoteNextRun:
    data = result.as_json_data()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{run_id}-{uuid4().hex[:8]}"
    label = "remote-next"
    timestamped_json = REMOTE_NEXT_REPORT_DIR / f"{run_id}-{label}.json"
    timestamped_log = REMOTE_NEXT_REPORT_DIR / f"{run_id}-{label}.log"
    published_json = PUBLISHED_REPORT_DIR / f"{run_id}-{label}.json"
    published_log = PUBLISHED_REPORT_DIR / f"{run_id}-{label}.log"

    data.update(
        {
            "report_path": str(timestamped_json),
            "published_report_path": str(published_json),
            "latest_report_path": str(REMOTE_NEXT_LATEST_JSON),
            "latest_published_report_path": str(PUBLISHED_LATEST_JSON),
        }
    )
    payload = _remote_next_payload(root, data)
    log_text = "\n".join(
        (
            "TRANSFER_REMOTE_NEXT_REPORT",
            f"RESULT_STATUS={data['result_status']}",
            f"RETURNCODE={data['returncode']}",
            f"BRANCH={data.get('branch') or ''}",
            f"HEAD={data.get('head') or ''}",
            f"REMOTE_REPORT={published_json}",
            "CHAT_REPLY=g",
            f"NEXT={data['next_action']}",
            "",
            "### JSON RESULT ###",
            json.dumps(payload, indent=2, sort_keys=True),
            "",
        )
    )

    for relative_path, content in (
        (REMOTE_NEXT_LATEST_JSON, json.dumps(payload, indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(payload, indent=2, sort_keys=True) + "\n"),
        (REMOTE_NEXT_LATEST_LOG, log_text),
        (timestamped_log, log_text),
        (PUBLISHED_LATEST_JSON, json.dumps(payload, indent=2, sort_keys=True) + "\n"),
        (published_json, json.dumps(payload, indent=2, sort_keys=True) + "\n"),
        (PUBLISHED_LATEST_LOG, log_text),
        (published_log, log_text),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return TransferRemoteNextRun(
        branch=result.branch,
        local_run=result.local_run,
        head=result.head,
        result_status=result.result_status,
        returncode=result.returncode,
        next_action=result.next_action,
        report_path=str(timestamped_json),
        published_report_path=str(published_json),
        reasons=result.reasons,
        preflight=result.preflight,
        rule_ack=result.rule_ack,
        blocked_message=result.blocked_message,
    )


def _blocked_result(root: Path, exc: Exception, *, branch: str | None = None) -> TransferRemoteNextRun:
    snapshot = _git_snapshot(root)
    ack = _rule_ack_snapshot(root, repo_head=snapshot.head)
    reasons: tuple[str, ...]
    if isinstance(exc, RemoteNextBlocked):
        reasons = exc.reasons
        branch = exc.branch or branch
    elif isinstance(exc, FileNotFoundError):
        reasons = ("missing_transfer_order",)
    elif isinstance(exc, ValueError):
        reasons = ("invalid_transfer_order",)
    else:
        reasons = ("remote_next_blocked",)
    return _write_remote_next_report(
        root,
        TransferRemoteNextRun(
            branch=branch,
            local_run=_blocked_local_run(str(exc), reasons, snapshot),
            head=snapshot.head,
            result_status="BLOCKED",
            returncode=2,
            next_action="Inspect the published remote-next diagnostic report before retrying.",
            report_path="",
            published_report_path="",
            reasons=reasons,
            preflight=snapshot.as_json_data(),
            rule_ack=ack,
            blocked_message=str(exc),
        ),
    )


def run_remote_next_transfer(project_root: Path, branch: str | None = None) -> TransferRemoteNextRun:
    root = project_root.resolve()
    try:
        safe_branch = resolve_remote_next_branch(root, branch)
        _ensure_clean(root, branch=safe_branch)
        _run(["git", "fetch", "origin", safe_branch], root)
        _run(["git", "switch", safe_branch], root)
        _run(["git", "pull", "--ff-only", "origin", safe_branch], root)

        preflight = _git_snapshot(root)
        local_run = run_local_transfer(root)
        head = _run(["git", "rev-parse", "--short", "HEAD"], root)
        result = TransferRemoteNextRun(
            branch=safe_branch,
            local_run=local_run,
            head=head,
            result_status=local_run.result_status,
            returncode=local_run.returncode,
            next_action=local_run.next_action,
            report_path="",
            published_report_path="",
            preflight=preflight.as_json_data(),
            rule_ack=_rule_ack_snapshot(root, repo_head=head),
        )
        return _write_remote_next_report(root, result)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        return _blocked_result(root, exc, branch=branch)
