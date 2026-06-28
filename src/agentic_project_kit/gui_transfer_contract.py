from __future__ import annotations

from pathlib import Path

from agentic_project_kit.transfer_runner import DEFAULT_INBOX
from agentic_project_kit.transfer_safety_context import OUTBOX_LAST_RESULT


GUI_TRANSFER_TASK_REF = "gui-transfer-tasks"
CURRENT_USER_TASK_PATH = DEFAULT_INBOX
CANONICAL_TRANSFER_INBOX_PATH = DEFAULT_INBOX
CANONICAL_TRANSFER_PAYLOAD_PATH = Path(".agentic/transfer/inbox/next_command.py.txt")
CANONICAL_TRANSFER_OUTBOX_PATH = OUTBOX_LAST_RESULT
CANONICAL_REMOTE_TRANSFER_REPORT_PATH = Path(
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
)
LEGACY_GUI_TRANSFER_TASK_PATH = Path("docs/reports/transfer_tasks/current_user_task.json")


def gui_transfer_refspec() -> str:
    return f"{GUI_TRANSFER_TASK_REF}:refs/remotes/origin/{GUI_TRANSFER_TASK_REF}"


def fetch_gui_transfer_ref_args() -> tuple[str, str, str]:
    return ("fetch", "origin", gui_transfer_refspec())


def remote_gui_task_spec(task_path: Path = CURRENT_USER_TASK_PATH) -> str:
    return f"origin/{GUI_TRANSFER_TASK_REF}:{task_path.as_posix()}"
