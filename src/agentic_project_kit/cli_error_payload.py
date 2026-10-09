"""Structured diagnostics for CLI failures before an orchestrator result exists."""
from __future__ import annotations


def command_error_payload(action: str, error: Exception, *, returncode: int,
                          next_action: str = "Inspect the error and retry the command.") -> dict[str, object]:
    return {"schema_version": 1, "action": action, "result_status": "BLOCKED",
            "returncode": returncode, "error": str(error), "next_action": next_action}
