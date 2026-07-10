from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

WrapperPhase = Literal[
    "starting",
    "creating_pr",
    "waiting_ci",
    "merging",
    "post_merge",
    "done",
    "blocked",
]

WRAPPER_STATUS_FILE = "current-wrapper-status.json"
WRAPPER_STATUS_RELATIVE_PATH = Path(LEGACY_DEFAULTS.tmp_root) / WRAPPER_STATUS_FILE

WRAPPER_PHASES: tuple[WrapperPhase, ...] = (
    "starting",
    "creating_pr",
    "waiting_ci",
    "merging",
    "post_merge",
    "done",
    "blocked",
)

_DEFAULT_SAFE_TO_INTERRUPT: dict[WrapperPhase, bool] = {
    "starting": False,
    "creating_pr": False,
    "waiting_ci": True,
    "merging": False,
    "post_merge": False,
    "done": False,
    "blocked": False,
}


def wrapper_status_path(root: Path = Path(".")) -> Path:
    return load_workspace(root).wrapper_status_path()


def default_safe_to_interrupt(phase: WrapperPhase) -> bool:
    return _DEFAULT_SAFE_TO_INTERRUPT[phase]


def write_wrapper_live_status(
    root: Path = Path("."),
    *,
    wrapper: str,
    phase: WrapperPhase,
    result_status: str = "RUNNING",
    safe_to_interrupt: bool | None = None,
    base: str = "",
    head: str = "",
    expected_head_sha: str = "",
    pr_number: int | None = None,
    blockers: Iterable[str] = (),
    step: str = "",
    message: str = "",
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if phase not in WRAPPER_PHASES:
        raise ValueError(f"unknown wrapper phase: {phase}")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "wrapper_live_status",
        "wrapper": wrapper,
        "status_path": load_workspace(root).path_text(wrapper_status_path(root)),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "result_status": result_status,
        "safe_to_interrupt": (
            default_safe_to_interrupt(phase)
            if safe_to_interrupt is None
            else bool(safe_to_interrupt)
        ),
        "base": base,
        "head": head,
        "expected_head_sha": expected_head_sha,
        "pr_number": pr_number,
        "blockers": list(blockers),
        "current_step": step,
        "message": message,
        "known_phases": list(WRAPPER_PHASES),
    }
    if extra:
        payload["extra"] = dict(extra)

    path = wrapper_status_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_wrapper_live_status(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads(wrapper_status_path(root).read_text(encoding="utf-8"))
