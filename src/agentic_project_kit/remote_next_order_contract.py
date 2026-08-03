from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import (
    command_manifest_ack_line,
    lint_instruction_text,
    strip_command_manifest_ack_header,
)
from agentic_project_kit.safe_push import SafePushResult, safe_push, validate_branch_name
from agentic_project_kit.transfer_remote_next import EXECUTABLE_TRANSFER_ORDER_KIND
from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)

ACTIVE_REMOTE_NEXT_STATUSES = frozenset({"active", "pending", "ready"})
DEFAULT_SAFETY = "bounded-remote-next-transfer"


@dataclass(frozen=True)
class RemoteNextOrderResult:
    result_status: str
    returncode: int
    path: str
    next_action: str
    order: dict[str, Any] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    written: bool = False
    preview_text: str = ""
    safe_push_target: dict[str, Any] | None = None
    transfer_inspect: dict[str, Any] | None = None
    instruction_lint: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.blockers

    def as_json_data(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema_version"] = 1
        data["kind"] = "remote_next_order_contract_result"
        data["valid"] = self.ok
        return data


def _git_text(root: Path, argv: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        argv,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _current_branch(root: Path) -> str:
    return _git_text(root, ["git", "branch", "--show-current"])[1]


def _current_full_head(root: Path) -> str:
    return _git_text(root, ["git", "rev-parse", "HEAD"])[1]


def _safe_repo_relative_path(path_text: str, *, field_name: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        raise ValueError(f"{field_name} must be repo-relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field_name} must not contain empty/current/parent segments")
    blocked_roots = {".git", ".venv", "venv", "__pycache__"}
    if path.parts and path.parts[0] in blocked_roots:
        raise ValueError(f"{field_name} uses blocked root: {path.parts[0]}")
    return path


def _slug(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {"-", "_", ".", "/"}:
            safe.append("-")
    text = "".join(safe).strip("-")
    while "--" in text:
        text = text.replace("--", "-")
    return text or "remote-next"


def _head_matches(expected: str, *, full_head: str) -> bool:
    value = expected.strip()
    short_head = full_head[:7]
    return bool(value) and (
        short_head.startswith(value) or full_head.startswith(value) or value.startswith(short_head)
    )


def _safe_push_preflight(root: Path, branch: str) -> SafePushResult:
    return safe_push(
        root,
        target_branch=branch,
        purpose="remote-next transfer order target validation",
        expected_current_branch="",
        dry_run=True,
    )


def _parse_write_action(root: Path, spec: str) -> dict[str, Any]:
    if "=" not in spec:
        raise ValueError("--write-action must use target_path=payload_path")
    target_text, payload_text = (part.strip() for part in spec.split("=", 1))
    target = _safe_repo_relative_path(target_text, field_name="target_path")
    payload = _safe_repo_relative_path(payload_text, field_name="payload_path")
    payload_path = root / payload
    if not payload_path.exists():
        raise ValueError(f"payload_path does not exist: {payload.as_posix()}")
    digest = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    return {
        "type": "write_text_file",
        "target_path": target.as_posix(),
        "payload_path": payload.as_posix(),
        "sha256": digest,
    }


def render_remote_next_order_text(root: Path, order: dict[str, Any]) -> str:
    ack = command_manifest_ack_line(load_manifest(root))
    return ack + "\n" + yaml.safe_dump(order, sort_keys=False)


def create_remote_next_order(
    root: Path | str = Path("."),
    *,
    branch: str,
    write_actions: tuple[str, ...],
    path: Path = DEFAULT_INBOX,
    order_id: str = "",
    title: str = "",
    safety: str = DEFAULT_SAFETY,
    report_path: str = "",
    status: str = "active",
    execute: bool = False,
    allow_overwrite: bool = False,
) -> RemoteNextOrderResult:
    root_path = Path(root).resolve()
    blockers: list[str] = []
    try:
        target_branch = validate_branch_name(branch)
    except ValueError as exc:
        target_branch = branch
        blockers.append(str(exc))

    safe_target = _safe_push_preflight(root_path, target_branch) if not blockers else None
    if safe_target is not None and not safe_target.ok:
        blockers.extend(safe_target.reasons)

    if not write_actions:
        blockers.append("at_least_one_write_action_required")

    actions: list[dict[str, Any]] = []
    for spec in write_actions:
        try:
            actions.append(_parse_write_action(root_path, spec))
        except ValueError as exc:
            blockers.append(str(exc))

    normalized_status = status.strip().lower()
    if normalized_status not in ACTIVE_REMOTE_NEXT_STATUSES:
        blockers.append(f"unsupported_status:{normalized_status}")

    full_head = _current_full_head(root_path)
    current_branch = _current_branch(root_path)
    transfer_id = order_id.strip() or f"remote-next-{_slug(target_branch)}-{full_head[:8]}"
    try:
        validate_branch_name(transfer_id.replace("/", "-"))
    except ValueError:
        blockers.append(f"unsafe_order_id:{transfer_id}")

    report = report_path.strip() or f"docs/reports/command_runs/{_slug(transfer_id)}.md"
    try:
        report = _safe_repo_relative_path(report, field_name="report_path").as_posix()
    except ValueError as exc:
        blockers.append(str(exc))
    if not report.startswith("docs/reports/command_runs/"):
        blockers.append("report_path must be under docs/reports/command_runs/")

    order = {
        "schema_version": 1,
        "kind": EXECUTABLE_TRANSFER_ORDER_KIND,
        "id": transfer_id,
        "status": normalized_status,
        "branch": target_branch,
        "expected_current_branch": current_branch,
        "expected_current_head": full_head,
        "title": title.strip() or f"Remote-next transfer for {target_branch}",
        "safety": safety.strip() or DEFAULT_SAFETY,
        "report_path": report,
        "actions": actions,
    }
    preview = render_remote_next_order_text(root_path, order)
    target_path = path if path.is_absolute() else root_path / path
    if execute and target_path.exists() and not allow_overwrite:
        blockers.append(f"target_exists:{target_path.relative_to(root_path).as_posix()}")

    if blockers:
        return RemoteNextOrderResult(
            "BLOCKED",
            2,
            str(path),
            "Fix remote-next order blockers before writing the transfer order.",
            order=order,
            blockers=tuple(blockers),
            preview_text=preview,
            safe_push_target=safe_target.as_json_data() if safe_target else None,
        )

    if execute:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(preview, encoding="utf-8")

    return RemoteNextOrderResult(
        "PASS",
        0,
        str(path),
        (
            "Run agentic-kit transfer order-validate before agentic-kit transfer remote-next."
            if execute
            else "Review preview, then rerun with --execute to write the transfer order."
        ),
        order=order,
        written=execute,
        preview_text=preview,
        safe_push_target=safe_target.as_json_data() if safe_target else None,
    )


def _load_order_mapping(path: Path) -> tuple[str, dict[str, Any]]:
    raw_text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(strip_command_manifest_ack_header(raw_text)) or {}
    if not isinstance(data, dict):
        raise ValueError("remote-next transfer order must be a mapping")
    return raw_text, data


def validate_remote_next_order(
    root: Path | str = Path("."),
    *,
    path: Path = DEFAULT_INBOX,
) -> RemoteNextOrderResult:
    root_path = Path(root).resolve()
    order_path = path if path.is_absolute() else root_path / path
    blockers: list[str] = []
    warnings: list[str] = []
    raw_text = ""
    data: dict[str, Any] = {}
    lint_data: dict[str, Any] | None = None
    safe_target: dict[str, Any] | None = None
    inspect_data: dict[str, Any] | None = None

    try:
        raw_text, data = _load_order_mapping(order_path)
    except (OSError, ValueError) as exc:
        return RemoteNextOrderResult(
            "BLOCKED",
            2,
            str(path),
            "Create a remote-next transfer order with agentic-kit transfer order-create.",
            blockers=(str(exc),),
        )

    try:
        lint_result = lint_instruction_text(
            raw_text,
            manifest=load_manifest(root_path),
            checked_path=str(path),
            require_ack=True,
            strict_unknown=False,
            include_structured_commands=True,
        )
        lint_data = lint_result.to_dict()
        if lint_result.returncode == 2:
            blockers.append("instruction_lint_blocked")
    except Exception as exc:  # pragma: no cover - defensive report payload path
        blockers.append(f"instruction_lint_error:{exc}")

    if data.get("kind") != EXECUTABLE_TRANSFER_ORDER_KIND:
        blockers.append("invalid_transfer_order_kind")
    status = str(data.get("status") or "").strip().lower()
    if status not in ACTIVE_REMOTE_NEXT_STATUSES:
        blockers.append(f"unsupported_status:{status or 'missing'}")
    branch = str(data.get("branch") or "").strip()
    try:
        branch = validate_branch_name(branch)
    except ValueError as exc:
        blockers.append(str(exc))
    if branch:
        push_result = _safe_push_preflight(root_path, branch)
        safe_target = push_result.as_json_data()
        if not push_result.ok:
            blockers.extend(push_result.reasons)

    current_branch = _current_branch(root_path)
    expected_branch = str(data.get("expected_current_branch") or "").strip()
    if not expected_branch:
        blockers.append("missing_expected_current_branch")
    elif expected_branch != current_branch:
        blockers.append(f"expected_current_branch_mismatch:{expected_branch}!={current_branch}")

    full_head = _current_full_head(root_path)
    expected_head = str(data.get("expected_current_head") or data.get("expected_head") or data.get("created_for_head") or "").strip()
    if not expected_head:
        blockers.append("missing_expected_current_head")
    elif not _head_matches(expected_head, full_head=full_head):
        blockers.append("expected_current_head_mismatch")

    try:
        transfer_order = load_transfer_order(order_path)
        inspect_result = inspect_transfer_order(transfer_order, root_path)
        inspect_data = transfer_result_as_json_data(inspect_result)
        if inspect_result.returncode != 0:
            blockers.append("transfer_order_inspect_failed")
    except Exception as exc:
        blockers.append(f"transfer_order_schema_invalid:{exc}")

    if data.get("report_path") and not str(data["report_path"]).startswith("docs/reports/command_runs/"):
        blockers.append("report_path_outside_command_runs")
    if data.get("schema_version") != 1:
        warnings.append("schema_version_should_be_1")

    if blockers:
        return RemoteNextOrderResult(
            "BLOCKED",
            2,
            str(path),
            "Fix remote-next transfer order blockers before running transfer remote-next.",
            order=data,
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(warnings),
            safe_push_target=safe_target,
            transfer_inspect=inspect_data,
            instruction_lint=lint_data,
        )

    return RemoteNextOrderResult(
        "PASS",
        0,
        str(path),
        "Run agentic-kit transfer remote-next to execute this validated order.",
        order=data,
        warnings=tuple(warnings),
        safe_push_target=safe_target,
        transfer_inspect=inspect_data,
        instruction_lint=lint_data,
    )


def render_remote_next_order_result(result: RemoteNextOrderResult) -> str:
    lines = [
        "REMOTE_NEXT_ORDER_CONTRACT",
        f"STATUS={result.result_status}",
        f"VALID={str(result.ok).lower()}",
        f"PATH={result.path}",
        f"WRITTEN={str(result.written).lower()}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for blocker in result.blockers:
        lines.append(f"BLOCKER={blocker}")
    for warning in result.warnings:
        lines.append(f"WARNING={warning}")
    lines.append(f"NEXT={result.next_action}")
    if result.preview_text and not result.written:
        lines.extend(("", "### PREVIEW ###", result.preview_text.rstrip()))
    lines.append("")
    return "\n".join(lines)


def remote_next_order_result_json(result: RemoteNextOrderResult) -> str:
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
