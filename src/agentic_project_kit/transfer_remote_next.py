from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.transfer_local_runner import TransferLocalRun, run_local_transfer
from agentic_project_kit.transfer_runner import DEFAULT_INBOX
from agentic_project_kit.transfer_safety_context import build_local_to_llm_payload
from agentic_project_kit.workspace import LEGACY_DEFAULTS, Workspace, load_workspace

REMOTE_NEXT_LATEST_JSON_NAME = "latest-remote-next-report.json"
REMOTE_NEXT_LATEST_LOG_NAME = "latest-remote-next-report.log"
PUBLISHED_LATEST_JSON_NAME = "latest-transfer-handoff-report.json"
PUBLISHED_LATEST_LOG_NAME = "latest-transfer-handoff-report.log"

REMOTE_NEXT_REPORT_DIR = Path(LEGACY_DEFAULTS.transfer_runs_root)
REMOTE_NEXT_LATEST_JSON = REMOTE_NEXT_REPORT_DIR / "latest-remote-next-report.json"
REMOTE_NEXT_LATEST_LOG = REMOTE_NEXT_REPORT_DIR / "latest-remote-next-report.log"
PUBLISHED_REPORT_DIR = Path(LEGACY_DEFAULTS.transfer_handoff_reports_root)
PUBLISHED_LATEST_JSON = PUBLISHED_REPORT_DIR / "latest-transfer-handoff-report.json"
PUBLISHED_LATEST_LOG = PUBLISHED_REPORT_DIR / "latest-transfer-handoff-report.log"
COMMAND_RUN_LATEST = Path(LEGACY_DEFAULTS.command_runs_root) / "LATEST_COMMAND_RUN.txt"
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
    post_report_actions: dict[str, object] = field(default_factory=dict)

    def as_json_data(self) -> dict[str, object]:
        primary_state = _remote_next_primary_state(self.result_status, self.reasons)
        command_id = self.local_run.transfer_id
        return {
            "schema_version": 1,
            "artifact_type": "transfer_remote_next_execution_report",
            "command_id": command_id,
            "transfer_id": command_id,
            "branch": self.branch,
            "head": self.head,
            "result_status": self.result_status,
            "primary_state": primary_state,
            "state": primary_state,
            "returncode": self.returncode,
            "next_action": self.next_action,
            "next": self.next_action,
            "chat_reply": "g",
            "report_path": self.report_path,
            "published_report_path": self.published_report_path,
            "reasons": list(self.reasons),
            "blocked_message": self.blocked_message,
            "preflight": self.preflight,
            "rule_ack": self.rule_ack.as_json_data() if self.rule_ack else None,
            "post_report_actions": self.post_report_actions,
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


def _remote_next_primary_state(result_status: str, reasons: tuple[str, ...]) -> str:
    if "no_current_transfer_order" in reasons:
        return "NEW_ORDER_REQUIRED"
    if "order_consumed" in reasons:
        return "ORDER_CONSUMED"
    if any(
        reason in reasons
        for reason in (
            "stale_transfer_order_status",
            "stale_transfer_order_branch_mismatch",
            "stale_order_missing_freshness_anchor",
            "stale_transfer_order_head_mismatch",
        )
    ):
        return "STALE_ORDER"
    if result_status == "BLOCKED":
        return "BLOCKED"
    return result_status


def _remote_next_next_action(reasons: tuple[str, ...]) -> str:
    if "no_current_transfer_order" in reasons:
        return "Create or queue a fresh remote-next transfer order, then rerun the canonical command."
    if "order_consumed" in reasons:
        return "Queue a fresh remote-next transfer order; the previous order has already been consumed."
    if any(
        reason in reasons
        for reason in (
            "stale_transfer_order_status",
            "stale_transfer_order_branch_mismatch",
            "stale_order_missing_freshness_anchor",
            "stale_transfer_order_head_mismatch",
        )
    ):
        return "Supersede the stale remote-next transfer order with a fresh head-anchored order."
    return "Inspect the published remote-next diagnostic report before retrying."


class RemoteNextBlocked(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        reasons: tuple[str, ...],
        branch: str | None = None,
        preflight: dict[str, object] | None = None,
    ):
        super().__init__(message)
        self.reasons = reasons
        self.branch = branch
        self.preflight = preflight or {}


def _command(argv: list[str], cwd: Path) -> _CommandResult:
    try:
        process = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        return _CommandResult(tuple(argv), 127, "", str(exc))
    return _CommandResult(tuple(argv), process.returncode, process.stdout.strip(), process.stderr.strip())


def _run(argv: list[str], cwd: Path) -> str:
    result = _command(argv, cwd)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(argv)}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result.stdout.strip()


def _status_path(line: str) -> str:
    if len(line) <= 3:
        return ""
    if line.startswith("?? "):
        return line[3:]
    if len(line) > 2 and line[2] == " ":
        return line[3:]
    return line[2:].strip()


def _status_paths(status_short: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    for line in status_short.splitlines():
        if not line:
            continue
        status = line[:2]
        path = _status_path(line)
        if status == "??":
            untracked.append(path)
            continue
        if status[0] != " ":
            staged.append(path)
        if status[1] != " ":
            unstaged.append(path)
    return tuple(staged), tuple(unstaged), tuple(untracked)


def _git_snapshot(project_root: Path) -> GitSnapshot:
    status = _command(["git", "status", "--porcelain=v1"], project_root).stdout
    staged, unstaged, untracked = _status_paths(status)
    return GitSnapshot(
        current_branch=_command(["git", "branch", "--show-current"], project_root).stdout or "UNKNOWN",
        head=_command(["git", "rev-parse", "--short", "HEAD"], project_root).stdout or "UNKNOWN",
        remote_tracking=_command(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], project_root
        ).stdout,
        status_short=status,
        staged_changes=staged,
        unstaged_changes=unstaged,
        untracked_files=untracked,
    )


def _full_head(project_root: Path) -> str:
    return _command(["git", "rev-parse", "HEAD"], project_root).stdout.strip()


def _head_matches(expected: str, *, short_head: str, full_head: str) -> bool:
    value = expected.strip()
    if not value:
        return True
    return short_head.startswith(value) or full_head.startswith(value) or value.startswith(short_head)


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
    return RuleAckSnapshot(True, not reasons, head=ack_head, blocking_reasons=tuple(reasons))


def _refresh_rule_ack(root: Path) -> _CommandResult:
    result = _command(["./.venv/bin/agentic-kit", "rules", "acknowledge"], root)
    if result.returncode == 127:
        return _command(["agentic-kit", "rules", "acknowledge"], root)
    return result


def _current_transfer_report_path(root: Path) -> str:
    workspace = load_workspace(root)
    try:
        data = yaml.safe_load((root / DEFAULT_INBOX).read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return ""
    if not isinstance(data, dict):
        return ""
    report_path = data.get("report_path")
    if not isinstance(report_path, str):
        return ""
    value = report_path.strip()
    if not value.startswith(workspace.path_text(workspace.command_runs_dir()) + "/"):
        return ""
    if ".." in Path(value).parts:
        return ""
    return value


def _remote_next_latest_json(workspace: Workspace) -> Path:
    return workspace.transfer_run_file(REMOTE_NEXT_LATEST_JSON_NAME)


def _remote_next_latest_log(workspace: Workspace) -> Path:
    return workspace.transfer_run_file(REMOTE_NEXT_LATEST_LOG_NAME)


def _published_latest_json(workspace: Workspace) -> Path:
    return workspace.transfer_handoff_report_file(PUBLISHED_LATEST_JSON_NAME)


def _published_latest_log(workspace: Workspace) -> Path:
    return workspace.transfer_handoff_report_file(PUBLISHED_LATEST_LOG_NAME)


def _is_owned_remote_next_report_path(path: str, *, workspace: Workspace, current_order_report: str = "") -> bool:
    value = path.strip()
    if value in {
        workspace.path_text(_remote_next_latest_json(workspace)),
        workspace.path_text(_remote_next_latest_log(workspace)),
        workspace.path_text(_published_latest_json(workspace)),
        workspace.path_text(_published_latest_log(workspace)),
        workspace.path_text(workspace.latest_command_run_pointer()),
        current_order_report,
    }:
        return True
    transfer_runs_prefix = workspace.path_text(workspace.transfer_runs_dir()) + "/"
    published_prefix = workspace.path_text(workspace.transfer_handoff_reports_dir()) + "/"
    if value.startswith(transfer_runs_prefix) and value.endswith(("-remote-next.json", "-remote-next.log")):
        return True
    return value.startswith(published_prefix) and value.endswith(("-remote-next.json", "-remote-next.log"))


def _recover_owned_report_artifacts(root: Path) -> dict[str, object]:
    snapshot = _git_snapshot(root)
    workspace = load_workspace(root)
    current_order_report = _current_transfer_report_path(root)
    dirty_paths = tuple(dict.fromkeys((*snapshot.staged_changes, *snapshot.unstaged_changes, *snapshot.untracked_files)))
    owned = tuple(
        path
        for path in dirty_paths
        if _is_owned_remote_next_report_path(path, workspace=workspace, current_order_report=current_order_report)
    )
    foreign = tuple(path for path in dirty_paths if path not in owned)
    actions: list[dict[str, object]] = []
    result: dict[str, object] = {
        "schema_version": 1,
        "attempted": bool(owned),
        "current_order_report": current_order_report,
        "owned_report_artifacts": list(owned),
        "foreign_dirty_paths": list(foreign),
        "actions": actions,
    }
    if foreign or not owned:
        return result
    tracked_owned = tuple(path for path in owned if path not in snapshot.untracked_files)
    untracked_owned = tuple(path for path in owned if path in snapshot.untracked_files)
    if tracked_owned:
        restore = _command(["git", "restore", "--staged", "--worktree", "--", *tracked_owned], root)
        actions.append({"name": "restore_tracked_owned_report_artifacts", **restore.as_json_data()})
        if restore.returncode != 0:
            result["blocked_reason"] = "restore_owned_report_artifacts_failed"
            return result
    for relative in untracked_owned:
        target = root / relative
        try:
            target.unlink(missing_ok=True)
            actions.append({"name": "remove_untracked_owned_report_artifact", "path": relative, "returncode": 0})
        except OSError as exc:
            actions.append({"name": "remove_untracked_owned_report_artifact", "path": relative, "returncode": 1, "stderr": str(exc)})
            result["blocked_reason"] = "remove_owned_report_artifacts_failed"
            return result
    result["final_status_short"] = _command(["git", "status", "--porcelain=v1"], root).stdout
    return result


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


def _order_identity(data: dict[str, Any]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": data.get("id", ""),
        "status": data.get("status", ""),
        "branch": data.get("branch", ""),
        "expected_current_branch": data.get("expected_current_branch", ""),
        "expected_current_head": data.get("expected_current_head", ""),
        "expected_head": data.get("expected_head", ""),
        "created_for_head": data.get("created_for_head", ""),
    }


def _freshness_anchor(data: dict[str, Any]) -> str:
    for key in ("expected_current_head", "expected_head", "created_for_head"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _block_inactive_transfer_order_before_branch_resolution(root: Path, *, branch: str | None = None) -> None:
    data = _read_transfer_order_data(root / DEFAULT_INBOX)
    status = str(data.get("status") or "active").strip().lower()
    if status in {"inactive", "none", "no-current-order", "no_current_order", "consumed", "superseded", "stale"}:
        _ensure_transfer_order_is_fresh(root, branch=branch)


def _ensure_transfer_order_is_fresh(root: Path, *, branch: str | None = None) -> dict[str, object]:
    data = _read_transfer_order_data(root / DEFAULT_INBOX)
    snapshot = _git_snapshot(root)
    full_head = _full_head(root)
    order = _order_identity(data)
    preflight = {
        "schema_version": 1,
        "transfer_order_guard": {
            **order,
            "current_branch": snapshot.current_branch,
            "current_head": snapshot.head,
            "current_full_head": full_head,
        },
    }
    status = str(data.get("status") or "active").strip().lower()
    if status in {"inactive", "none", "no-current-order", "no_current_order"}:
        raise RemoteNextBlocked(
            f"remote-next transfer order is not active: {status}",
            reasons=("no_current_transfer_order",),
            branch=branch,
            preflight=preflight,
        )
    if status == "consumed":
        raise RemoteNextBlocked(
            "remote-next transfer order has already been consumed",
            reasons=("order_consumed",),
            branch=branch,
            preflight=preflight,
        )
    if status in {"superseded", "stale"}:
        raise RemoteNextBlocked(
            f"remote-next transfer order is stale: {status}",
            reasons=("stale_transfer_order_status",),
            branch=branch,
            preflight=preflight,
        )
    if status not in {"active", "pending", "ready"}:
        raise RemoteNextBlocked(
            f"remote-next transfer order has unsupported status: {status}",
            reasons=("invalid_transfer_order_status",),
            branch=branch,
            preflight=preflight,
        )
    expected_branch = data.get("expected_current_branch")
    if isinstance(expected_branch, str) and expected_branch.strip() and expected_branch.strip() != snapshot.current_branch:
        raise RemoteNextBlocked(
            "remote-next transfer order expected a different current branch",
            reasons=("stale_transfer_order_branch_mismatch",),
            branch=branch,
            preflight=preflight,
        )
    anchor = _freshness_anchor(data)
    if not anchor:
        raise RemoteNextBlocked(
            "remote-next transfer order is missing a freshness head anchor",
            reasons=("stale_order_missing_freshness_anchor",),
            branch=branch,
            preflight=preflight,
        )
    if not _head_matches(anchor, short_head=snapshot.head, full_head=full_head):
        raise RemoteNextBlocked(
            "remote-next transfer order freshness anchor does not match current HEAD",
            reasons=("stale_transfer_order_head_mismatch",),
            branch=branch,
            preflight=preflight,
        )
    return preflight["transfer_order_guard"]


def resolve_remote_next_branch(project_root: Path, branch: str | None = None, path: Path = DEFAULT_INBOX) -> str:
    if branch is not None and branch.strip():
        return _validate_branch_name(branch)
    root = project_root.resolve()
    order_path = path if path.is_absolute() else root / path
    data = _read_transfer_order_data(order_path)
    order_branch = data.get("branch")
    if not isinstance(order_branch, str) or not order_branch.strip():
        raise ValueError(f"transfer order must define a non-empty branch: {path}")
    return _validate_branch_name(order_branch)


def _sync_current_branch_before_order(root: Path) -> dict[str, object]:
    snapshot = _git_snapshot(root)
    steps: list[dict[str, object]] = []
    result: dict[str, object] = {
        "schema_version": 1,
        "attempted": False,
        "current_branch": snapshot.current_branch,
        "head": snapshot.head,
        "steps": steps,
    }
    if not snapshot.clean:
        result["skipped_reason"] = "dirty_worktree_before_order_sync"
        return result
    if not snapshot.current_branch or snapshot.current_branch == "UNKNOWN":
        result["skipped_reason"] = "unknown_current_branch"
        return result
    result["attempted"] = True
    fetch = _command(["git", "fetch", "origin", snapshot.current_branch], root)
    steps.append({"name": "git_fetch_current_branch", **fetch.as_json_data()})
    if fetch.returncode != 0:
        result["blocked_reason"] = "fetch_current_branch_failed"
        return result
    pull = _command(["git", "pull", "--ff-only", "origin", snapshot.current_branch], root)
    steps.append({"name": "git_pull_current_branch", **pull.as_json_data()})
    if pull.returncode != 0:
        result["blocked_reason"] = "pull_current_branch_failed"
    result["final_head"] = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout
    return result


def _blocked_local_run(message: str, reasons: tuple[str, ...], snapshot: GitSnapshot) -> TransferLocalRun:
    next_action = _remote_next_next_action(reasons)
    state = {
        "schema_version": 1,
        "primary_state": _remote_next_primary_state("BLOCKED", reasons),
        "reasons": list(reasons),
        "next_action": next_action,
        "branch": snapshot.current_branch,
        "head": snapshot.head,
        "dirty_state": snapshot.as_json_data()["dirty_state"],
    }
    inspect = {"schema_version": 1, "result_status": "BLOCKED", "returncode": 2, "message": message, "reasons": list(reasons)}
    return TransferLocalRun(
        schema_version=1,
        transfer_id="remote-next-blocked",
        inspect=inspect,
        apply=None,
        state=state,
        result_status="BLOCKED",
        returncode=2,
        next_action=_remote_next_next_action(reasons),
    )


def _remote_next_payload(root: Path, data: dict[str, object]) -> dict[str, object]:
    payload = build_local_to_llm_payload(root, data, kind="local_to_llm_remote_next_report")
    payload["remote_next_report"] = data
    return payload


def _report_paths(workspace: Workspace) -> tuple[str, ...]:
    return (
        workspace.path_text(_remote_next_latest_json(workspace)),
        workspace.path_text(_remote_next_latest_log(workspace)),
        workspace.path_text(_published_latest_json(workspace)),
        workspace.path_text(_published_latest_log(workspace)),
    )


def _build_log_text(data: dict[str, object], payload_text: str) -> str:
    return "\n".join(
        (
            "TRANSFER_REMOTE_NEXT_REPORT",
            f"COMMAND_ID={data.get('command_id') or data.get('transfer_id') or ''}",
            f"STATE={data.get('primary_state') or data['result_status']}",
            f"RESULT_STATUS={data['result_status']}",
            f"RETURNCODE={data['returncode']}",
            f"BRANCH={data.get('branch') or ''}",
            f"HEAD={data.get('head') or ''}",
            f"REMOTE_REPORT={data['published_report_path']}",
            "CHAT_REPLY=g",
            f"NEXT={data['next_action']}",
            "",
            "### JSON RESULT ###",
            payload_text.rstrip(),
            "",
        )
    )


def _write_payload_files(root: Path, paths_and_content: tuple[tuple[Path, str], ...]) -> None:
    for path, content in paths_and_content:
        target = path if path.is_absolute() else root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _write_report_payloads(root: Path, data: dict[str, object]) -> None:
    workspace = load_workspace(root)
    payload = _remote_next_payload(root, data)
    payload_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    log_text = _build_log_text(data, payload_text)
    _write_payload_files(
        root,
        (
            (_remote_next_latest_json(workspace), payload_text),
            (_remote_next_latest_log(workspace), log_text),
            (_published_latest_json(workspace), payload_text),
            (_published_latest_log(workspace), log_text),
        ),
    )


def _attempt_report_commit_ack_push(root: Path, *, branch: str | None, paths: tuple[str, ...]) -> dict[str, object]:
    steps: list[dict[str, object]] = []
    actions: dict[str, object] = {
        "schema_version": 1,
        "attempted": True,
        "branch": branch,
        "paths": list(paths),
        "steps": steps,
        "committed": False,
        "rule_ack_refreshed_after_commit": False,
        "pushed": False,
    }
    add = _command(["git", "add", "-f", *paths], root)
    steps.append({"name": "git_add_force_report_paths", **add.as_json_data()})
    if add.returncode != 0:
        actions["blocked_reason"] = "git_add_failed"
        return actions
    staged = _command(["git", "diff", "--cached", "--quiet"], root)
    if staged.returncode == 0:
        actions["skipped_reason"] = "no_report_changes_to_commit"
    else:
        commit = _command(["git", "commit", "-m", "Publish remote-next transfer report"], root)
        steps.append({"name": "git_commit_report_paths", **commit.as_json_data()})
        if commit.returncode != 0:
            actions["blocked_reason"] = "git_commit_failed"
            return actions
        actions["committed"] = True
        actions["commit_head"] = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout
        ack = _refresh_rule_ack(root)
        steps.append({"name": "rules_acknowledge_after_report_commit", **ack.as_json_data()})
        actions["rule_ack_refreshed_after_commit"] = ack.returncode == 0
        post_ack_head = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout
        actions["rule_ack_after_report_commit"] = _rule_ack_snapshot(root, repo_head=post_ack_head).as_json_data()
    push = _command(["git", "push", "origin", branch], root) if branch else _command(["git", "push"], root)
    steps.append({"name": "git_push_report_commit", **push.as_json_data()})
    actions["pushed"] = push.returncode == 0
    if push.returncode != 0:
        actions["blocked_reason"] = "git_push_failed"
    actions["final_head"] = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout
    actions["final_status_short"] = _command(["git", "status", "--porcelain=v1"], root).stdout
    return actions


def _attempt_final_report_projection_commit_push(
    root: Path,
    *,
    branch: str | None,
    paths: tuple[str, ...],
) -> dict[str, object]:
    steps: list[dict[str, object]] = []
    actions: dict[str, object] = {
        "schema_version": 1,
        "attempted": True,
        "branch": branch,
        "paths": list(paths),
        "steps": steps,
        "committed": False,
        "pushed": False,
    }
    add = _command(["git", "add", "-f", *paths], root)
    steps.append({"name": "git_add_force_final_report_projection", **add.as_json_data()})
    if add.returncode != 0:
        actions["blocked_reason"] = "git_add_failed"
        return actions

    staged = _command(["git", "diff", "--cached", "--quiet"], root)
    if staged.returncode == 0:
        actions["skipped_reason"] = "no_final_projection_changes_to_commit"
    else:
        commit = _command(["git", "commit", "-m", "Publish final remote-next report projection"], root)
        steps.append({"name": "git_commit_final_report_projection", **commit.as_json_data()})
        if commit.returncode != 0:
            actions["blocked_reason"] = "git_commit_failed"
            return actions
        actions["committed"] = True
        actions["commit_head"] = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout

    push = _command(["git", "push", "origin", branch], root) if branch else _command(["git", "push"], root)
    steps.append({"name": "git_push_final_report_projection", **push.as_json_data()})
    actions["pushed"] = push.returncode == 0
    if push.returncode != 0:
        actions["blocked_reason"] = "git_push_failed"
    actions["final_head"] = _command(["git", "rev-parse", "--short", "HEAD"], root).stdout
    actions["final_status_short"] = _command(["git", "status", "--porcelain=v1"], root).stdout
    return actions


def _write_remote_next_report(root: Path, result: TransferRemoteNextRun) -> TransferRemoteNextRun:
    workspace = load_workspace(root)
    latest_report = workspace.path_text(_remote_next_latest_json(workspace))
    latest_published_report = workspace.path_text(_published_latest_json(workspace))
    paths = _report_paths(workspace)
    provisional_data = result.as_json_data()
    provisional_data.update(
        {
            "report_path": latest_report,
            "published_report_path": latest_published_report,
            "latest_report_path": latest_report,
            "latest_published_report_path": latest_published_report,
            "post_report_actions": {"schema_version": 1, "attempted": True, "status": "pending_until_report_files_are_written"},
        }
    )
    _write_report_payloads(root, provisional_data)
    post_report_actions = _attempt_report_commit_ack_push(root, branch=result.branch, paths=paths)

    final_result = TransferRemoteNextRun(
        branch=result.branch,
        local_run=result.local_run,
        head=result.head,
        result_status=result.result_status,
        returncode=result.returncode,
        next_action=result.next_action,
        report_path=latest_report,
        published_report_path=latest_published_report,
        reasons=result.reasons,
        preflight=result.preflight,
        rule_ack=result.rule_ack,
        blocked_message=result.blocked_message,
        post_report_actions=post_report_actions,
    )

    final_data = final_result.as_json_data()
    final_data.update(
        {
            "report_path": latest_report,
            "published_report_path": latest_published_report,
            "latest_report_path": latest_report,
            "latest_published_report_path": latest_published_report,
        }
    )
    _write_report_payloads(root, final_data)
    final_projection = _attempt_final_report_projection_commit_push(root, branch=result.branch, paths=paths)
    post_report_actions["final_projection"] = final_projection
    if final_projection.get("commit_head"):
        post_report_actions["final_projection_commit_head"] = final_projection["commit_head"]
        post_report_actions["final_head"] = final_projection.get("final_head", final_projection["commit_head"])
    if final_projection.get("blocked_reason"):
        post_report_actions["final_projection_blocked_reason"] = final_projection["blocked_reason"]
        post_report_actions["pushed"] = False
    elif final_projection.get("pushed") is False:
        post_report_actions["pushed"] = False

    return TransferRemoteNextRun(
        branch=result.branch,
        local_run=result.local_run,
        head=result.head,
        result_status=result.result_status,
        returncode=result.returncode,
        next_action=result.next_action,
        report_path=latest_report,
        published_report_path=latest_published_report,
        reasons=result.reasons,
        preflight=result.preflight,
        rule_ack=result.rule_ack,
        blocked_message=result.blocked_message,
        post_report_actions=post_report_actions,
    )


def _blocked_result(root: Path, exc: Exception, *, branch: str | None = None) -> TransferRemoteNextRun:
    snapshot = _git_snapshot(root)
    ack = _rule_ack_snapshot(root, repo_head=snapshot.head)
    extra_preflight: dict[str, object] = {}
    if isinstance(exc, RemoteNextBlocked):
        reasons = exc.reasons
        branch = exc.branch or branch
        extra_preflight = exc.preflight
    elif isinstance(exc, FileNotFoundError):
        reasons = ("missing_transfer_order",)
    elif isinstance(exc, ValueError):
        reasons = ("invalid_transfer_order",)
    else:
        reasons = ("remote_next_blocked",)
    preflight = snapshot.as_json_data()
    preflight.update(extra_preflight)
    return _write_remote_next_report(
        root,
        TransferRemoteNextRun(
            branch=branch,
            local_run=_blocked_local_run(str(exc), reasons, snapshot),
            head=snapshot.head,
            result_status="BLOCKED",
            returncode=2,
            next_action=_remote_next_next_action(reasons),
            report_path="",
            published_report_path="",
            reasons=reasons,
            preflight=preflight,
            rule_ack=ack,
            blocked_message=str(exc),
        ),
    )


def run_remote_next_transfer(project_root: Path, branch: str | None = None) -> TransferRemoteNextRun:
    root = project_root.resolve()
    try:
        cleanup = _recover_owned_report_artifacts(root)
        order_sync = _sync_current_branch_before_order(root)
        if branch is None:
            _block_inactive_transfer_order_before_branch_resolution(root)
        safe_branch = resolve_remote_next_branch(root, branch)
        if branch is None:
            order_guard = _ensure_transfer_order_is_fresh(root, branch=safe_branch)
        else:
            order_guard = {
                "schema_version": 1,
                "skipped_reason": "explicit_branch_argument",
                "branch": safe_branch,
            }
        _ensure_clean(root, branch=safe_branch)
        _run(["git", "fetch", "origin", safe_branch], root)
        _run(["git", "switch", safe_branch], root)
        _run(["git", "pull", "--ff-only", "origin", safe_branch], root)
        head = _run(["git", "rev-parse", "--short", "HEAD"], root)
        ack_before = _rule_ack_snapshot(root, repo_head=head)
        ack_refresh: dict[str, object] | None = None
        if not ack_before.confirmed:
            ack_result = _refresh_rule_ack(root)
            ack_refresh = ack_result.as_json_data()
        preflight = _git_snapshot(root).as_json_data()
        preflight["owned_report_artifact_recovery"] = cleanup
        preflight["order_sync"] = order_sync
        preflight["transfer_order_guard"] = order_guard
        if ack_refresh is not None:
            preflight["rule_ack_refresh_before_transfer"] = ack_refresh
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
            preflight=preflight,
            rule_ack=_rule_ack_snapshot(root, repo_head=head),
        )
        return _write_remote_next_report(root, result)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        return _blocked_result(root, exc, branch=branch)
