from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from agentic_project_kit.cockpit import action_result_as_json_data, run_cockpit_action

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_PENDING = "PENDING"
RESULT_HARD_FAIL = "HARD-FAIL"

STEP_COMMAND_ARGV = "command_argv"
STEP_COCKPIT_ACTION = "cockpit_action"

@dataclass(frozen=True)
class TypedWorkOrderStep:
    kind: str
    label: str
    argv: tuple[str, ...] = ()
    action_id: str | None = None
    allow_bounded: bool = False

@dataclass(frozen=True)
class TypedWorkOrder:
    work_order_id: str
    title: str
    safety: str
    log_path: str
    steps: tuple[TypedWorkOrderStep, ...]
    block_dirty_worktree: bool = True

@dataclass(frozen=True)
class TypedWorkOrderResult:
    work_order_id: str
    result_status: str
    returncode: int
    safety: str
    dirty_state: str
    terminal_log: str
    command_report: str | None = None
    message: str = ""
    step_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)

CommandRunner = Callable[[tuple[str, ...], Path], subprocess.CompletedProcess[str]]

def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid typed work order field: {key}")
    return value

def _parse_step(data: dict[str, Any]) -> TypedWorkOrderStep:
    kind = _require_string(data, "kind")
    label = str(data.get("label") or kind)
    if kind == STEP_COMMAND_ARGV:
        argv = data.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
            raise ValueError("command_argv step requires a non-empty argv string list")
        return TypedWorkOrderStep(kind=kind, label=label, argv=tuple(argv))
    if kind == STEP_COCKPIT_ACTION:
        action_id = _require_string(data, "action_id")
        allow_bounded = bool(data.get("allow_bounded", False))
        return TypedWorkOrderStep(kind=kind, label=label, action_id=action_id, allow_bounded=allow_bounded)
    raise ValueError(f"unsupported typed work order step kind: {kind}")

def parse_typed_work_order(data: dict[str, Any]) -> TypedWorkOrder:
    steps_data = data.get("steps")
    if not isinstance(steps_data, list) or not steps_data:
        raise ValueError("typed work order requires at least one step")
    steps = tuple(_parse_step(step) for step in steps_data)
    log_path = _require_string(data, "log_path")
    if not log_path.startswith("docs/reports/terminal/"):
        raise ValueError("typed work order log_path must be under docs/reports/terminal/")
    return TypedWorkOrder(
        work_order_id=_require_string(data, "id"),
        title=_require_string(data, "title"),
        safety=_require_string(data, "safety"),
        log_path=log_path,
        steps=steps,
        block_dirty_worktree=bool(data.get("block_dirty_worktree", True)),
    )

def load_typed_work_order(path: Path) -> TypedWorkOrder:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"typed work order must be a mapping: {path}")
    return parse_typed_work_order(data)

def _default_runner(argv: tuple[str, ...], project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

def _git_dirty_state(project_root: Path) -> str:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        return "unknown"
    return "dirty" if result.stdout.strip() else "clean"

def typed_work_order_result_as_json_data(result: TypedWorkOrderResult) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "work_order_id": result.work_order_id,
        "result_status": result.result_status,
        "returncode": result.returncode,
        "safety": result.safety,
        "dirty_state": result.dirty_state,
        "terminal_log": result.terminal_log,
        "command_report": result.command_report,
        "message": result.message,
        "step_results": list(result.step_results),
    }

def _write_result_log(order: TypedWorkOrder, project_root: Path, result: TypedWorkOrderResult) -> None:
    path = project_root / order.log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data = typed_work_order_result_as_json_data(result)
    lines = [
        f"Typed work order: {order.work_order_id}",
        f"Title: {order.title}",
        f"Safety: {order.safety}",
        "",
        "### JSON RESULT ###",
        json.dumps(data, indent=2, sort_keys=True),
        "",
        f"### RESULT: {result.result_status} ###",
        f"Return code: {result.returncode}",
        "Terminal bleibt offen. Kein exit am Blockende.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def run_typed_work_order(order: TypedWorkOrder, project_root: Path = Path("."), runner: CommandRunner | None = None) -> TypedWorkOrderResult:
    root = project_root.resolve()
    dirty_state = _git_dirty_state(root)
    if order.block_dirty_worktree and dirty_state == "dirty":
        result = TypedWorkOrderResult(order.work_order_id, RESULT_PENDING, 96, order.safety, dirty_state, order.log_path, message="Dirty worktree blocks typed work order execution.")
        _write_result_log(order, root, result)
        return result
    command_runner = runner if runner is not None else _default_runner
    step_results: list[dict[str, Any]] = []
    for step in order.steps:
        if step.kind == STEP_COMMAND_ARGV:
            completed = command_runner(step.argv, root)
            step_results.append({"kind": step.kind, "label": step.label, "argv": list(step.argv), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
            if completed.returncode != 0:
                result = TypedWorkOrderResult(order.work_order_id, RESULT_FAIL, completed.returncode, order.safety, dirty_state, order.log_path, message=f"Step failed: {step.label}", step_results=tuple(step_results))
                _write_result_log(order, root, result)
                return result
        elif step.kind == STEP_COCKPIT_ACTION:
            assert step.action_id is not None
            action_result = run_cockpit_action(step.action_id, root, allow_bounded=step.allow_bounded)
            action_data = action_result_as_json_data(action_result)
            step_results.append({"kind": step.kind, "label": step.label, "action_result": action_data})
            if action_result.result_status != RESULT_PASS:
                result = TypedWorkOrderResult(order.work_order_id, action_result.result_status, action_result.returncode or 95, order.safety, dirty_state, order.log_path, message=f"Cockpit action failed: {step.action_id}", step_results=tuple(step_results))
                _write_result_log(order, root, result)
                return result
        else:
            result = TypedWorkOrderResult(order.work_order_id, RESULT_HARD_FAIL, 94, order.safety, dirty_state, order.log_path, message=f"Unsupported step kind: {step.kind}", step_results=tuple(step_results))
            _write_result_log(order, root, result)
            return result
    result = TypedWorkOrderResult(order.work_order_id, RESULT_PASS, 0, order.safety, dirty_state, order.log_path, message="Typed work order executed.", step_results=tuple(step_results))
    _write_result_log(order, root, result)
    return result
