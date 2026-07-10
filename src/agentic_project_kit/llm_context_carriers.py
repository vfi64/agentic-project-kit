from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_project_kit.transfer_safety_context import build_local_to_llm_payload
from agentic_project_kit.transfer_safety_context import write_transfer_outbox
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

LATEST_HANDOFF_REPORT_NAME = "latest-transfer-handoff-report.json"
LATEST_HANDOFF_LOG_NAME = "latest-transfer-handoff-report.log"
LATEST_HANDOFF_REPORT = Path(LEGACY_DEFAULTS.transfer_handoff_reports_root) / LATEST_HANDOFF_REPORT_NAME
LATEST_HANDOFF_LOG = Path(LEGACY_DEFAULTS.transfer_handoff_reports_root) / LATEST_HANDOFF_LOG_NAME


def refresh_llm_context_carriers(root: Path | str = ".", *, label: str = "llm-context-carriers-refresh") -> dict[str, Any]:
    """Refresh both canonical LLM-context carriers used by running and successor chats."""
    root_path = Path(root)
    last_result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "llm_context_carriers_refresh",
        "action": "refresh-llm-context-carriers",
        "label": label,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": "PASS",
        "final_signal": "d",
        "next_action": "LLM context carriers refreshed.",
    }

    outbox_path = write_transfer_outbox(root_path, last_result)
    payload = build_local_to_llm_payload(root_path, last_result)
    workspace = load_workspace(root_path)

    latest_path = workspace.transfer_handoff_report_file(LATEST_HANDOFF_REPORT_NAME)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    latest_log = workspace.transfer_handoff_report_file(LATEST_HANDOFF_LOG_NAME)
    latest_log.parent.mkdir(parents=True, exist_ok=True)
    latest_log.write_text(
        "\n".join(
            [
                "TRANSFER_REFRESH_LLM_CONTEXT_CARRIERS",
                "STATE=PASS",
                f"OUTBOX={outbox_path}",
                f"LATEST={latest_path}",
                "CHAT_REPLY=d | NEXT=LLM context carriers refreshed.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "schema_version": 1,
        "kind": "llm_context_carriers_refresh_result",
        "action": "refresh-llm-context-carriers",
        "result_status": "PASS",
        "final_signal": "d",
        "next_action": "LLM context carriers refreshed.",
        "outbox_path": str(outbox_path),
        "latest_handoff_report_path": str(latest_path),
        "latest_handoff_log_path": str(latest_log),
    }
