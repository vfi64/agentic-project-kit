from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.typed_work_order_runner import (
    RESULT_FAIL,
    RESULT_PASS,
    RESULT_PENDING,
    TypedWorkOrderResult,
    load_typed_work_order,
    run_typed_work_order,
)

STATUS_NO_COMMAND = "no_command"
STATUS_EXACTLY_ONE_COMMAND = "exactly_one_command"
STATUS_MULTIPLE_COMMANDS = "multiple_commands"
STATUS_ALREADY_EXECUTED = "already_executed"

DEFAULT_TYPED_WORK_ORDER_INBOX = Path(".agentic/typed_work_orders/inbox")
DEFAULT_TYPED_WORK_ORDER_EXECUTED = Path(".agentic/typed_work_orders/executed")


@dataclass(frozen=True)
class TypedWorkOrderQueueStatus:
    inbox_path: Path
    status: str
    pending_paths: tuple[Path, ...]

    @property
    def pending_count(self) -> int:
        return len(self.pending_paths)


@dataclass(frozen=True)
class TypedNextResult:
    queue_status: str
    result_status: str
    returncode: int
    source_path: str | None
    executed_path: str | None
    terminal_log: str | None
    message: str
    work_order_result: TypedWorkOrderResult | None = None
    expected_closeout_paths: tuple[str, ...] = ()


def inspect_typed_work_order_queue(inbox_path: Path = DEFAULT_TYPED_WORK_ORDER_INBOX) -> TypedWorkOrderQueueStatus:
    inbox = inbox_path
    if not inbox.exists():
        return TypedWorkOrderQueueStatus(inbox, STATUS_NO_COMMAND, ())
    if not inbox.is_dir():
        raise ValueError(f"typed work order inbox is not a directory: {inbox}")
    pending = tuple(sorted(path for path in inbox.glob("*.yaml") if path.is_file()))
    if len(pending) == 0:
        status = STATUS_NO_COMMAND
    elif len(pending) == 1:
        status = STATUS_EXACTLY_ONE_COMMAND
    else:
        status = STATUS_MULTIPLE_COMMANDS
    return TypedWorkOrderQueueStatus(inbox, status, pending)


def typed_work_order_queue_status_as_json_data(status: TypedWorkOrderQueueStatus) -> dict[str, object]:
    return {
        "schema_version": 1,
        "inbox_path": str(status.inbox_path),
        "status": status.status,
        "pending_count": status.pending_count,
        "pending_paths": [str(path) for path in status.pending_paths],
    }


def typed_next_result_as_json_data(result: TypedNextResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "queue_status": result.queue_status,
        "result_status": result.result_status,
        "returncode": result.returncode,
        "source_path": result.source_path,
        "executed_path": result.executed_path,
        "terminal_log": result.terminal_log,
        "message": result.message,
        "expected_closeout_paths": list(result.expected_closeout_paths),
    }


def render_typed_work_order_queue_status(status: TypedWorkOrderQueueStatus) -> str:
    lines = [
        "Typed work order queue status",
        f"inbox_path={status.inbox_path}",
        f"status={status.status}",
        f"pending_count={status.pending_count}",
    ]
    for path in status.pending_paths:
        lines.append(f"pending={path}")
    return "\n".join(lines)


def _expected_closeout_paths(*paths: str | None) -> tuple[str, ...]:
    return tuple(path for path in paths if path)


def run_typed_next(
    project_root: Path = Path("."),
    inbox_path: Path = DEFAULT_TYPED_WORK_ORDER_INBOX,
    executed_dir: Path = DEFAULT_TYPED_WORK_ORDER_EXECUTED,
) -> TypedNextResult:
    root = project_root.resolve()
    status = inspect_typed_work_order_queue(root / inbox_path)
    if status.status == STATUS_NO_COMMAND:
        return TypedNextResult(status.status, RESULT_PENDING, 2, None, None, None, "No typed work order queued.")
    if status.status == STATUS_MULTIPLE_COMMANDS:
        return TypedNextResult(
            status.status,
            RESULT_FAIL,
            2,
            None,
            None,
            None,
            "Multiple typed work orders queued; refusing ambiguous execution.",
        )
    source = status.pending_paths[0]
    source_rel = str(source.relative_to(root))
    target_dir = root / executed_dir
    target = target_dir / source.name
    target_rel = str(target.relative_to(root))
    if target.exists():
        return TypedNextResult(
            STATUS_ALREADY_EXECUTED,
            RESULT_PENDING,
            2,
            source_rel,
            target_rel,
            None,
            "Typed work order was already executed; refusing duplicate execution.",
            expected_closeout_paths=_expected_closeout_paths(source_rel, target_rel),
        )
    order = load_typed_work_order(source)
    result = run_typed_work_order(order, root)
    if result.result_status == RESULT_PASS:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        return TypedNextResult(
            status.status,
            result.result_status,
            result.returncode,
            source_rel,
            target_rel,
            result.terminal_log,
            "Typed work order executed and moved to executed queue.",
            result,
            _expected_closeout_paths(source_rel, target_rel, result.terminal_log),
        )
    return TypedNextResult(
        status.status,
        result.result_status,
        result.returncode,
        source_rel,
        None,
        result.terminal_log,
        result.message,
        result,
        _expected_closeout_paths(result.terminal_log),
    )
