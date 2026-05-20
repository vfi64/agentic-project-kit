from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

STATUS_NO_COMMAND = "no_command"
STATUS_EXACTLY_ONE_COMMAND = "exactly_one_command"
STATUS_MULTIPLE_COMMANDS = "multiple_commands"

DEFAULT_TYPED_WORK_ORDER_INBOX = Path(".agentic/typed_work_orders/inbox")


@dataclass(frozen=True)
class TypedWorkOrderQueueStatus:
    inbox_path: Path
    status: str
    pending_paths: tuple[Path, ...]

    @property
    def pending_count(self) -> int:
        return len(self.pending_paths)


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
