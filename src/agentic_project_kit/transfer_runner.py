from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import (
    InstructionLintResult,
    lint_instruction_text,
    strip_command_manifest_ack_header,
)
from agentic_project_kit.workspace import load_workspace

DEFAULT_INBOX = Path(".agentic/transfer/inbox/current.yaml")
RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_PENDING = "PENDING"
ACTION_WRITE_TEXT_FILE = "write_text_file"
ACTION_RUN_COMMAND = "run_command"
BLOCKED_COMMAND_TOKENS = {";", "&&", "||", "|", ">", "<", "`", "$", "$(", "\n"}


@dataclass(frozen=True)
class TransferAction:
    kind: str
    target_path: str = ""
    payload_path: str = ""
    sha256: str | None = None
    command: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransferOrder:
    transfer_id: str
    title: str
    safety: str
    report_path: str
    actions: tuple[TransferAction, ...]
    raw_text: str | None = None
    checked_path: str = ""


@dataclass(frozen=True)
class TransferResult:
    transfer_id: str
    result_status: str
    returncode: int
    safety: str
    report_path: str
    message: str = ""
    action_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    instruction_lint: InstructionLintResult | None = None


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid transfer field: {key}")
    return value


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


def _parse_command(data: dict[str, Any]) -> tuple[str, ...]:
    command = data.get("command")
    if not isinstance(command, list) or not command:
        raise ValueError("run_command action requires non-empty command list")
    parsed: list[str] = []
    for item in command:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("run_command command items must be non-empty strings")
        if item in BLOCKED_COMMAND_TOKENS or any(token in item for token in ("\n", "\r")):
            raise ValueError("run_command command items must not contain shell control tokens")
        parsed.append(item)
    if parsed[0] in {"sh", "bash", "zsh", "fish", "python", "python3"}:
        raise ValueError("run_command must not invoke a shell or ambiguous interpreter directly")
    return tuple(parsed)


def _parse_action(data: dict[str, Any]) -> TransferAction:
    kind = _require_string(data, "type")
    if kind == ACTION_WRITE_TEXT_FILE:
        target_path = str(
            _safe_repo_relative_path(_require_string(data, "target_path"), field_name="target_path")
        )
        payload_path = str(
            _safe_repo_relative_path(
                _require_string(data, "payload_path"), field_name="payload_path"
            )
        )
        sha = data.get("sha256")
        if sha is not None and (not isinstance(sha, str) or len(sha) != 64):
            raise ValueError("sha256 must be a 64 character hex string when provided")
        return TransferAction(kind, target_path=target_path, payload_path=payload_path, sha256=sha)
    if kind == ACTION_RUN_COMMAND:
        return TransferAction(kind, command=_parse_command(data))
    raise ValueError(f"unsupported transfer action type: {kind}")


def parse_transfer_order(data: dict[str, Any]) -> TransferOrder:
    actions_data = data.get("actions")
    if not isinstance(actions_data, list) or not actions_data:
        raise ValueError("transfer order requires at least one action")
    report_path = str(
        _safe_repo_relative_path(_require_string(data, "report_path"), field_name="report_path")
    )
    if not report_path.startswith("docs/reports/command_runs/"):
        raise ValueError("report_path must be under docs/reports/command_runs/")
    actions = tuple(_parse_action(action) for action in actions_data)
    return TransferOrder(
        transfer_id=_require_string(data, "id"),
        title=_require_string(data, "title"),
        safety=_require_string(data, "safety"),
        report_path=report_path,
        actions=actions,
    )


def load_transfer_order(path: Path = DEFAULT_INBOX) -> TransferOrder:
    raw_text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(strip_command_manifest_ack_header(raw_text)) or {}
    if not isinstance(data, dict):
        raise ValueError(f"transfer order must be a mapping: {path}")
    order = parse_transfer_order(data)
    return replace(order, raw_text=raw_text, checked_path=str(path))


def transfer_result_next_action(result: TransferResult) -> str:
    if result.result_status == RESULT_PASS:
        return "review_transfer_state_and_evidence"
    if result.result_status == RESULT_PENDING:
        return "apply_transfer_order_or_inspect"
    return "fix_transfer_errors_before_continuing"


def transfer_result_as_json_data(result: TransferResult) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "transfer_id": result.transfer_id,
        "command_id": result.transfer_id,
        "state": result.result_status,
        "result_status": result.result_status,
        "returncode": result.returncode,
        "next_action": transfer_result_next_action(result),
        "next": transfer_result_next_action(result),
        "safety": result.safety,
        "report_path": result.report_path,
        "message": result.message,
        "action_results": list(result.action_results),
        "instruction_lint": (
            result.instruction_lint.to_dict() if result.instruction_lint is not None else None
        ),
    }


def inspect_transfer_order(order: TransferOrder, project_root: Path = Path(".")) -> TransferResult:
    root = project_root.resolve()
    action_results: list[dict[str, Any]] = []
    for action in order.actions:
        if action.kind == ACTION_RUN_COMMAND:
            action_results.append(
                {"type": action.kind, "command": list(action.command), "would_run": True}
            )
            continue
        payload = root / action.payload_path
        target = root / action.target_path
        if not payload.exists():
            return TransferResult(
                order.transfer_id,
                RESULT_FAIL,
                2,
                order.safety,
                order.report_path,
                message=f"missing payload: {action.payload_path}",
                action_results=tuple(action_results),
            )
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        if action.sha256 and digest != action.sha256:
            return TransferResult(
                order.transfer_id,
                RESULT_FAIL,
                3,
                order.safety,
                order.report_path,
                message=f"sha256 mismatch: {action.payload_path}",
                action_results=tuple(action_results),
            )
        action_results.append(
            {
                "type": action.kind,
                "target_path": action.target_path,
                "payload_path": action.payload_path,
                "sha256": digest,
                "would_write": str(target.relative_to(root)),
            }
        )
    return TransferResult(
        order.transfer_id,
        RESULT_PENDING,
        0,
        order.safety,
        order.report_path,
        message="Transfer order inspected. Re-run apply to write files or run commands.",
        action_results=tuple(action_results),
    )


def _write_report(project_root: Path, result: TransferResult) -> None:
    path = project_root / result.report_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data = transfer_result_as_json_data(result)
    lines = [
        f"Transfer: {result.transfer_id}",
        f"COMMAND_ID={result.transfer_id}",
        f"STATE={result.result_status}",
        f"NEXT={transfer_result_next_action(result)}",
        f"Safety: {result.safety}",
        "",
        "### JSON RESULT ###",
        json.dumps(data, indent=2, sort_keys=True),
        "",
        f"### RESULT: {result.result_status} ###",
        f"Return code: {result.returncode}",
        "Terminal bleibt offen. Kein exit am Blockende.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest = load_workspace(project_root).latest_command_run_pointer()
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(result.report_path + "\n", encoding="utf-8")


def _run_command_action(root: Path, action: TransferAction) -> dict[str, Any]:
    completed = subprocess.run(
        list(action.command),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "type": action.kind,
        "command": list(action.command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def apply_transfer_order(order: TransferOrder, project_root: Path = Path(".")) -> TransferResult:
    root = project_root.resolve()
    if order.raw_text is None:
        result = TransferResult(
            order.transfer_id,
            RESULT_FAIL,
            2,
            order.safety,
            order.report_path,
            message="Instruction lint context missing; transfer apply refused.",
        )
        _write_report(root, result)
        return result
    lint_result = lint_instruction_text(
        order.raw_text,
        manifest=load_manifest(root),
        checked_path=order.checked_path or "<transfer-order>",
        require_ack=True,
        strict_unknown=False,
        include_structured_commands=True,
    )
    if lint_result.returncode == 2:
        rejection = lint_result.rejection_block()
        message = "Instruction lint refused transfer apply."
        if rejection:
            message = message + "\n" + rejection
        result = TransferResult(
            order.transfer_id,
            RESULT_FAIL,
            2,
            order.safety,
            order.report_path,
            message=message,
            instruction_lint=lint_result,
        )
        _write_report(root, result)
        return result
    inspected = inspect_transfer_order(order, root)
    if inspected.result_status == RESULT_FAIL:
        _write_report(root, inspected)
        return inspected
    action_results: list[dict[str, Any]] = []
    result_status = RESULT_PASS
    returncode = 0
    message = "Transfer order applied."
    for action in order.actions:
        if action.kind == ACTION_RUN_COMMAND:
            command_result = _run_command_action(root, action)
            action_results.append(command_result)
            if int(command_result["returncode"]) != 0:
                result_status = RESULT_FAIL
                returncode = int(command_result["returncode"])
                message = "Transfer command action failed."
                break
            continue
        payload_path = root / action.payload_path
        target_path = root / action.target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        text = payload_path.read_text(encoding="utf-8")
        target_path.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        action_results.append(
            {
                "type": action.kind,
                "target_path": action.target_path,
                "payload_path": action.payload_path,
                "sha256": digest,
                "written": True,
            }
        )
    result = TransferResult(
        order.transfer_id,
        result_status,
        returncode,
        order.safety,
        order.report_path,
        message=message,
        action_results=tuple(action_results),
        instruction_lint=lint_result,
    )
    _write_report(root, result)
    return result
