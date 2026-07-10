from __future__ import annotations

import json
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

LOCAL_COMMAND_STACK_STATE_FILE = "local-command-stack-state.json"
LOCAL_COMMAND_STACK_STATE = Path(LEGACY_DEFAULTS.tmp_root) / LOCAL_COMMAND_STACK_STATE_FILE
DEFAULT_MAX_AGE_SECONDS = 6 * 60 * 60


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _state_path(project_root: Path) -> Path:
    return load_workspace(project_root).local_command_stack_state_path()


def read_local_command_stack(project_root: Path = Path(".")) -> dict[str, Any]:
    path = _state_path(project_root)
    if not path.exists():
        return {
            "schema_version": 1,
            "kind": "local_command_stack_state",
            "active": False,
            "command_stack_id": "",
            "started_at_utc": "",
            "updated_at_utc": "",
            "reason": "missing_state_file",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "schema_version": 1,
            "kind": "local_command_stack_state",
            "active": False,
            "command_stack_id": "",
            "started_at_utc": "",
            "updated_at_utc": "",
            "reason": "invalid_state_file",
        }
    if not isinstance(data, dict):
        return {
            "schema_version": 1,
            "kind": "local_command_stack_state",
            "active": False,
            "command_stack_id": "",
            "started_at_utc": "",
            "updated_at_utc": "",
            "reason": "invalid_state_shape",
        }
    data.setdefault("schema_version", 1)
    data.setdefault("kind", "local_command_stack_state")
    data.setdefault("active", False)
    data.setdefault("command_stack_id", "")
    data.setdefault("started_at_utc", "")
    data.setdefault("updated_at_utc", "")
    return data


def write_local_command_stack(project_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    path = _state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def begin_local_command_stack(project_root: Path = Path("."), *, reason: str = "explicit_begin") -> dict[str, Any]:
    now = _iso(_utc_now())
    state = {
        "schema_version": 1,
        "kind": "local_command_stack_state",
        "active": True,
        "command_stack_id": f"local-{uuid.uuid4().hex}",
        "started_at_utc": now,
        "updated_at_utc": now,
        "reason": reason,
    }
    return write_local_command_stack(project_root, state)


def end_local_command_stack(project_root: Path = Path("."), *, reason: str = "explicit_end") -> dict[str, Any]:
    state = read_local_command_stack(project_root)
    state["active"] = False
    state["updated_at_utc"] = _iso(_utc_now())
    state["reason"] = reason
    return write_local_command_stack(project_root, state)


def current_or_begin_local_command_stack(
    project_root: Path = Path("."),
    *,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    state = read_local_command_stack(project_root)
    stack_id = str(state.get("command_stack_id", "")).strip()
    active = bool(state.get("active"))
    started = _parse_iso(state.get("started_at_utc"))
    now = _utc_now()

    if active and stack_id and started is not None:
        age_seconds = int((now - started).total_seconds())
        if 0 <= age_seconds <= max_age_seconds:
            state["updated_at_utc"] = _iso(now)
            state["reason"] = "active_reused"
            return write_local_command_stack(project_root, state)

    return begin_local_command_stack(project_root, reason="implicit_begin")


def current_or_begin_local_command_stack_id(project_root: Path = Path(".")) -> str:
    state = current_or_begin_local_command_stack(project_root)
    return str(state["command_stack_id"])
