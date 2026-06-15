from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)
from agentic_project_kit.transfer_state import build_transfer_state


@dataclass(frozen=True)
class TransferLocalRun:
    schema_version: int
    transfer_id: str
    inspect: dict[str, Any]
    apply: dict[str, Any] | None
    state: dict[str, Any]
    result_status: str
    returncode: int
    next_action: str

    def as_json_data(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "transfer_id": self.transfer_id,
            "command_id": self.transfer_id,
            "inspect": self.inspect,
            "apply": self.apply,
            "state": self.state,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "next_action": self.next_action,
            "next": self.next_action,
        }


def run_local_transfer(
    project_root: Path = Path("."), path: Path = DEFAULT_INBOX
) -> TransferLocalRun:
    root = project_root.resolve()
    order = load_transfer_order(path)
    inspect_result = inspect_transfer_order(order, root)
    inspect_data = transfer_result_as_json_data(inspect_result)

    apply_data: dict[str, Any] | None = None
    result_status = inspect_result.result_status
    returncode = inspect_result.returncode
    next_action = "Fix transfer inspection errors before applying."

    state_before_apply = build_transfer_state(root)
    if inspect_result.returncode == 0 and not state_before_apply.capabilities.get(
        "run_next_command", False
    ):
        state_data = state_before_apply.as_json_data()
        return TransferLocalRun(
            schema_version=1,
            transfer_id=order.transfer_id,
            inspect=inspect_data,
            apply=None,
            state=state_data,
            result_status="BLOCKED",
            returncode=2,
            next_action="Transfer blocked because run_next_command is false.",
        )

    if inspect_result.returncode == 0:
        apply_result = apply_transfer_order(order, root)
        apply_data = transfer_result_as_json_data(apply_result)
        result_status = apply_result.result_status
        returncode = apply_result.returncode
        next_action = (
            "Review transfer state and evidence report before continuing."
            if returncode == 0
            else "Fix transfer apply errors before continuing."
        )

    state_data = build_transfer_state(root).as_json_data()

    return TransferLocalRun(
        schema_version=1,
        transfer_id=order.transfer_id,
        inspect=inspect_data,
        apply=apply_data,
        state=state_data,
        result_status=result_status,
        returncode=returncode,
        next_action=next_action,
    )


def run_local_transfer_json(project_root: Path = Path("."), path: Path = DEFAULT_INBOX) -> str:
    return json.dumps(
        run_local_transfer(project_root, path).as_json_data(), indent=2, sort_keys=True
    )
