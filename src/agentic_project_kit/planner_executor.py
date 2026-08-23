from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from agentic_project_kit.cockpit import (
    BOUNDED,
    DESTRUCTIVE,
    READ_ONLY,
    action_by_id,
    action_result_as_json_data,
    cockpit_actions,
    run_cockpit_action,
)
from agentic_project_kit.command_manifest import load_manifest

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_PENDING = "PENDING"
RESULT_HARD_FAIL = "HARD-FAIL"

ADAPTER_HERMES = "hermes"
ADAPTER_KIT_LOCAL = "kit-local"
SUPPORTED_ADAPTERS = frozenset({ADAPTER_HERMES, ADAPTER_KIT_LOCAL})

STEP_COCKPIT_ACTION = "cockpit_action"
STEP_COMMAND = "command"
SUPPORTED_STEP_KINDS = frozenset({STEP_COCKPIT_ACTION, STEP_COMMAND})

SAFETY_READ_ONLY = "READ_ONLY"
SAFETY_BOUNDED = "BOUNDED"
SAFETY_DESTRUCTIVE = "DESTRUCTIVE"


@dataclass(frozen=True)
class PlannerExecutorStep:
    step_id: str
    kind: str
    label: str
    action_id: str = ""
    argv: tuple[str, ...] = ()
    allow_bounded: bool = False


@dataclass(frozen=True)
class PlannerExecutorIntent:
    intent_id: str
    title: str
    executor_adapter: str
    steps: tuple[PlannerExecutorStep, ...]
    block_dirty_worktree: bool = True
    evidence_path: str = ""


@dataclass(frozen=True)
class ResolvedPlannerExecutorStep:
    step_id: str
    kind: str
    label: str
    authority: str
    safety: str
    command: tuple[str, ...]
    allowed_in_plan: bool
    executable_by_default: bool
    allow_bounded: bool = False
    blocker: str = ""


@dataclass(frozen=True)
class PlannerExecutorPlan:
    intent_id: str
    title: str
    executor_adapter: str
    result_status: str
    dirty_state: str
    steps: tuple[ResolvedPlannerExecutorStep, ...]
    blockers: tuple[str, ...] = ()
    evidence_path: str = ""


@dataclass(frozen=True)
class PlannerExecutorRunResult:
    intent_id: str
    executor_adapter: str
    result_status: str
    returncode: int
    dirty_state: str
    executed: bool
    evidence_path: str
    message: str
    step_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    blockers: tuple[str, ...] = ()


CommandRunner = Callable[[tuple[str, ...], Path], subprocess.CompletedProcess[str]]


def load_planner_executor_intent(path: Path) -> PlannerExecutorIntent:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"planner-executor intent must be a mapping: {path}")
    return parse_planner_executor_intent(data)


def parse_planner_executor_intent(data: dict[str, Any]) -> PlannerExecutorIntent:
    schema_version = data.get("schema_version")
    if schema_version != 1:
        raise ValueError("planner-executor intent requires schema_version: 1")
    intent_id = _required_string(data, "id")
    title = _required_string(data, "title")
    executor_adapter = _required_string(data, "executor_adapter")
    if executor_adapter not in SUPPORTED_ADAPTERS:
        known = ", ".join(sorted(SUPPORTED_ADAPTERS))
        raise ValueError(f"unsupported executor_adapter: {executor_adapter}; known: {known}")
    steps_data = data.get("steps")
    if not isinstance(steps_data, list) or not steps_data:
        raise ValueError("planner-executor intent requires at least one step")
    steps = tuple(_parse_step(step) for step in steps_data)
    evidence_path = str(data.get("evidence_path") or "")
    if evidence_path and not _safe_evidence_path(evidence_path):
        raise ValueError("planner-executor evidence_path must be under docs/reports/ or tmp/")
    return PlannerExecutorIntent(
        intent_id=intent_id,
        title=title,
        executor_adapter=executor_adapter,
        steps=steps,
        block_dirty_worktree=bool(data.get("block_dirty_worktree", True)),
        evidence_path=evidence_path,
    )


def build_planner_executor_plan(
    intent: PlannerExecutorIntent,
    project_root: Path = Path("."),
    *,
    manifest: dict[str, object] | None = None,
) -> PlannerExecutorPlan:
    root = project_root.resolve()
    reference = manifest if manifest is not None else _load_manifest_or_current(root)
    actions = cockpit_actions()
    dirty_state = _git_dirty_state(root)
    resolved: list[ResolvedPlannerExecutorStep] = []
    blockers: list[str] = []
    for step in intent.steps:
        resolved_step = _resolve_step(step, actions=actions, manifest=reference)
        resolved.append(resolved_step)
        if resolved_step.blocker:
            blockers.append(f"{step.step_id}: {resolved_step.blocker}")
        elif resolved_step.safety == SAFETY_DESTRUCTIVE:
            blockers.append(f"{step.step_id}: destructive steps are never executor-runnable")
    if intent.block_dirty_worktree and dirty_state == "dirty":
        blockers.append("dirty worktree blocks executor run")
    status = RESULT_PASS if not blockers else RESULT_PENDING
    return PlannerExecutorPlan(
        intent_id=intent.intent_id,
        title=intent.title,
        executor_adapter=intent.executor_adapter,
        result_status=status,
        dirty_state=dirty_state,
        steps=tuple(resolved),
        blockers=tuple(blockers),
        evidence_path=intent.evidence_path,
    )


def run_planner_executor_intent(
    intent: PlannerExecutorIntent,
    project_root: Path = Path("."),
    *,
    execute: bool = False,
    allow_bounded: bool = False,
    runner: CommandRunner | None = None,
    report_path: Path | None = None,
) -> PlannerExecutorRunResult:
    root = project_root.resolve()
    plan = build_planner_executor_plan(intent, root)
    evidence_path = _select_evidence_path(intent, report_path)
    if plan.blockers:
        result = PlannerExecutorRunResult(
            intent.intent_id,
            intent.executor_adapter,
            RESULT_PENDING,
            96,
            plan.dirty_state,
            False,
            evidence_path,
            "Planner-executor run is blocked by preconditions.",
            blockers=plan.blockers,
        )
        _maybe_write_report(result, evidence_path, root)
        return result
    if not execute:
        result = PlannerExecutorRunResult(
            intent.intent_id,
            intent.executor_adapter,
            RESULT_PENDING,
            0,
            plan.dirty_state,
            False,
            evidence_path,
            "Dry-run only. Re-run with --execute to execute allowed steps.",
        )
        _maybe_write_report(result, evidence_path, root)
        return result

    command_runner = runner if runner is not None else _default_runner
    step_results: list[dict[str, Any]] = []
    for step in plan.steps:
        if step.safety == SAFETY_DESTRUCTIVE:
            result = PlannerExecutorRunResult(
                intent.intent_id,
                intent.executor_adapter,
                RESULT_HARD_FAIL,
                95,
                plan.dirty_state,
                False,
                evidence_path,
                f"Destructive executor step blocked: {step.step_id}",
                tuple(step_results),
                (f"{step.step_id}: destructive step blocked",),
            )
            _maybe_write_report(result, evidence_path, root)
            return result
        if step.safety == SAFETY_BOUNDED and not (allow_bounded and step.allow_bounded):
            result = PlannerExecutorRunResult(
                intent.intent_id,
                intent.executor_adapter,
                RESULT_PENDING,
                94,
                plan.dirty_state,
                False,
                evidence_path,
                f"Bounded executor step requires intent allow_bounded and CLI --allow-bounded: {step.step_id}",
                tuple(step_results),
                (f"{step.step_id}: bounded step not explicitly allowed",),
            )
            _maybe_write_report(result, evidence_path, root)
            return result
        if step.kind == STEP_COCKPIT_ACTION:
            action_result = run_cockpit_action(
                _action_id_from_step(intent, step.step_id),
                root,
                allow_bounded=allow_bounded and step.allow_bounded,
            )
            action_data = action_result_as_json_data(action_result)
            step_results.append(
                {
                    "step_id": step.step_id,
                    "kind": step.kind,
                    "authority": step.authority,
                    "action_result": action_data,
                }
            )
            if action_result.result_status != RESULT_PASS:
                result = PlannerExecutorRunResult(
                    intent.intent_id,
                    intent.executor_adapter,
                    action_result.result_status,
                    action_result.returncode or 93,
                    plan.dirty_state,
                    True,
                    evidence_path,
                    f"Cockpit action failed: {step.step_id}",
                    tuple(step_results),
                )
                _maybe_write_report(result, evidence_path, root)
                return result
            continue
        if step.kind == STEP_COMMAND:
            if step.safety != SAFETY_READ_ONLY:
                result = PlannerExecutorRunResult(
                    intent.intent_id,
                    intent.executor_adapter,
                    RESULT_PENDING,
                    92,
                    plan.dirty_state,
                    False,
                    evidence_path,
                    f"Direct command execution is limited to READ_ONLY manifest commands: {step.step_id}",
                    tuple(step_results),
                    (f"{step.step_id}: non-read-only direct command blocked",),
                )
                _maybe_write_report(result, evidence_path, root)
                return result
            completed = command_runner(_resolve_local_agentic_command(step.command, root), root)
            step_results.append(
                {
                    "step_id": step.step_id,
                    "kind": step.kind,
                    "authority": step.authority,
                    "argv": list(step.command),
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            )
            if completed.returncode != 0:
                result = PlannerExecutorRunResult(
                    intent.intent_id,
                    intent.executor_adapter,
                    RESULT_FAIL,
                    completed.returncode,
                    plan.dirty_state,
                    True,
                    evidence_path,
                    f"Command step failed: {step.step_id}",
                    tuple(step_results),
                )
                _maybe_write_report(result, evidence_path, root)
                return result
            continue
        result = PlannerExecutorRunResult(
            intent.intent_id,
            intent.executor_adapter,
            RESULT_HARD_FAIL,
            91,
            plan.dirty_state,
            False,
            evidence_path,
            f"Unsupported resolved executor step kind: {step.kind}",
            tuple(step_results),
        )
        _maybe_write_report(result, evidence_path, root)
        return result

    result = PlannerExecutorRunResult(
        intent.intent_id,
        intent.executor_adapter,
        RESULT_PASS,
        0,
        plan.dirty_state,
        True,
        evidence_path,
        "Planner-executor run completed.",
        tuple(step_results),
    )
    _maybe_write_report(result, evidence_path, root)
    return result


def planner_executor_plan_as_json_data(plan: PlannerExecutorPlan) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "planner_executor_plan",
        "intent_id": plan.intent_id,
        "title": plan.title,
        "executor_adapter": plan.executor_adapter,
        "result_status": plan.result_status,
        "dirty_state": plan.dirty_state,
        "evidence_path": plan.evidence_path,
        "blockers": list(plan.blockers),
        "steps": [
            {
                "step_id": step.step_id,
                "kind": step.kind,
                "label": step.label,
                "authority": step.authority,
                "safety": step.safety,
                "command": list(step.command),
                "allowed_in_plan": step.allowed_in_plan,
                "executable_by_default": step.executable_by_default,
                "allow_bounded": step.allow_bounded,
                "blocker": step.blocker,
            }
            for step in plan.steps
        ],
    }


def planner_executor_result_as_json_data(result: PlannerExecutorRunResult) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "planner_executor_run_result",
        "intent_id": result.intent_id,
        "executor_adapter": result.executor_adapter,
        "result_status": result.result_status,
        "returncode": result.returncode,
        "dirty_state": result.dirty_state,
        "executed": result.executed,
        "evidence_path": result.evidence_path,
        "message": result.message,
        "blockers": list(result.blockers),
        "step_results": list(result.step_results),
    }


def render_planner_executor_plan(plan: PlannerExecutorPlan) -> str:
    lines = [
        "Planner-Kit-Executor plan",
        f"intent_id={plan.intent_id}",
        f"executor_adapter={plan.executor_adapter}",
        f"result_status={plan.result_status}",
        f"dirty_state={plan.dirty_state}",
    ]
    if plan.evidence_path:
        lines.append(f"evidence_path={plan.evidence_path}")
    lines.extend(["", "Steps:"])
    for step in plan.steps:
        command = " ".join(step.command)
        lines.append(
            f"- {step.step_id} [{step.authority}/{step.safety}] "
            f"default_executable={str(step.executable_by_default).lower()} {command}"
        )
        if step.blocker:
            lines.append(f"  blocker: {step.blocker}")
    lines.extend(["", "Blockers:"])
    lines.extend(f"- {blocker}" for blocker in plan.blockers)
    if not plan.blockers:
        lines.append("- none")
    return "\n".join(lines)


def render_planner_executor_result(result: PlannerExecutorRunResult) -> str:
    lines = [
        "Planner-Kit-Executor run",
        f"intent_id={result.intent_id}",
        f"executor_adapter={result.executor_adapter}",
        f"result_status={result.result_status}",
        f"returncode={result.returncode}",
        f"dirty_state={result.dirty_state}",
        f"executed={str(result.executed).lower()}",
        result.message,
    ]
    if result.evidence_path:
        lines.append(f"evidence_path={result.evidence_path}")
    if result.blockers:
        lines.extend(["", "Blockers:"])
        lines.extend(f"- {blocker}" for blocker in result.blockers)
    return "\n".join(lines)


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid planner-executor field: {key}")
    return value.strip()


def _parse_step(data: Any) -> PlannerExecutorStep:
    if not isinstance(data, dict):
        raise ValueError("planner-executor step must be a mapping")
    step_id = _required_string(data, "id")
    kind = _required_string(data, "kind")
    if kind not in SUPPORTED_STEP_KINDS:
        known = ", ".join(sorted(SUPPORTED_STEP_KINDS))
        raise ValueError(f"unsupported planner-executor step kind: {kind}; known: {known}")
    label = str(data.get("label") or step_id)
    if kind == STEP_COCKPIT_ACTION:
        return PlannerExecutorStep(
            step_id=step_id,
            kind=kind,
            label=label,
            action_id=_required_string(data, "action_id"),
            allow_bounded=bool(data.get("allow_bounded", False)),
        )
    argv = data.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise ValueError("planner-executor command step requires a non-empty argv string list")
    if argv[0] != "agentic-kit":
        raise ValueError("planner-executor command steps must start with agentic-kit")
    return PlannerExecutorStep(
        step_id=step_id,
        kind=kind,
        label=label,
        argv=tuple(argv),
        allow_bounded=bool(data.get("allow_bounded", False)),
    )


def _resolve_step(
    step: PlannerExecutorStep,
    *,
    actions: list[Any],
    manifest: dict[str, object],
) -> ResolvedPlannerExecutorStep:
    if step.kind == STEP_COCKPIT_ACTION:
        action = action_by_id(step.action_id, actions)
        if action is None:
            return ResolvedPlannerExecutorStep(
                step.step_id,
                step.kind,
                step.label,
                "cockpit",
                "unknown",
                (),
                False,
                False,
                step.allow_bounded,
                f"unknown cockpit action: {step.action_id}",
            )
        safety = _cockpit_safety(str(action.safety))
        return ResolvedPlannerExecutorStep(
            step.step_id,
            step.kind,
            step.label,
            "cockpit",
            safety,
            tuple(action.command),
            safety in {SAFETY_READ_ONLY, SAFETY_BOUNDED},
            safety == SAFETY_READ_ONLY,
            step.allow_bounded,
        )
    command = _manifest_command(step.argv, manifest)
    if command is None:
        return ResolvedPlannerExecutorStep(
            step.step_id,
            step.kind,
            step.label,
            "command_manifest",
            "unknown",
            step.argv,
            False,
            False,
            step.allow_bounded,
            "command not found in generated command manifest",
        )
    safety = str(command.get("safety") or "unknown")
    return ResolvedPlannerExecutorStep(
        step.step_id,
        step.kind,
        step.label,
        "command_manifest",
        safety,
        step.argv,
        safety in {SAFETY_READ_ONLY, SAFETY_BOUNDED},
        safety == SAFETY_READ_ONLY,
        step.allow_bounded,
    )


def _manifest_command(argv: tuple[str, ...], manifest: dict[str, object]) -> dict[str, object] | None:
    qualified = " ".join(argv)
    # Match exact argv first. If options are supplied, match the command prefix.
    candidates = manifest.get("commands") or []
    if not isinstance(candidates, list):
        return None
    best: dict[str, object] | None = None
    best_len = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        path = candidate.get("path")
        if not isinstance(path, list):
            continue
        base = ("agentic-kit", *tuple(str(part) for part in path))
        if tuple(argv[: len(base)]) == base and len(base) > best_len:
            best = candidate
            best_len = len(base)
        elif str(candidate.get("qualified_name") or "") == qualified:
            return candidate
    return best


def _cockpit_safety(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized == READ_ONLY:
        return SAFETY_READ_ONLY
    if normalized == BOUNDED:
        return SAFETY_BOUNDED
    if normalized == DESTRUCTIVE:
        return SAFETY_DESTRUCTIVE
    return "unknown"


def _action_id_from_step(intent: PlannerExecutorIntent, step_id: str) -> str:
    for step in intent.steps:
        if step.step_id == step_id:
            return step.action_id
    return ""


def _git_dirty_state(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return "unknown"
    return "dirty" if result.stdout.strip() else "clean"


def _default_runner(argv: tuple[str, ...], project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _load_manifest_or_current(root: Path) -> dict[str, object]:
    try:
        return load_manifest(root)
    except Exception:
        from agentic_project_kit.command_manifest import build_current_reference

        return build_current_reference()


def _resolve_local_agentic_command(argv: tuple[str, ...], root: Path) -> tuple[str, ...]:
    if not argv or argv[0] != "agentic-kit":
        return argv
    local = root / ".venv" / "bin" / "agentic-kit"
    if local.exists():
        return (str(local), *argv[1:])
    return argv


def _safe_evidence_path(value: str) -> bool:
    normalized = Path(value)
    if normalized.is_absolute() or ".." in normalized.parts:
        return False
    return value.startswith("docs/reports/") or value.startswith("tmp/")


def _select_evidence_path(intent: PlannerExecutorIntent, report_path: Path | None) -> str:
    if report_path is not None:
        return report_path.as_posix()
    if intent.evidence_path:
        return intent.evidence_path
    digest = hashlib.sha256(intent.intent_id.encode("utf-8")).hexdigest()[:12]
    return f"tmp/planner-executor-{digest}.json"


def _maybe_write_report(result: PlannerExecutorRunResult, evidence_path: str, root: Path) -> None:
    if not evidence_path:
        return
    if not _safe_evidence_path(evidence_path):
        raise ValueError("planner-executor report path must be under docs/reports/ or tmp/")
    path = root / evidence_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(planner_executor_result_as_json_data(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
