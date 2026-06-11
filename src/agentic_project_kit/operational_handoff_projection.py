from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_OPERATIONAL_HANDOFF_STATE = Path(".agentic/operational_handoff_state.yaml")

GENERATED_BLOCK_BEGIN = "<!-- agentic:generated operational-handoff-state begin -->"
GENERATED_BLOCK_END = "<!-- agentic:generated operational-handoff-state end -->"


def load_operational_handoff_state(
    root: Path | str = ".",
    *,
    path: Path | str = DEFAULT_OPERATIONAL_HANDOFF_STATE,
) -> dict[str, Any]:
    state_path = Path(root) / path
    data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("operational handoff state must be a YAML mapping")
    if data.get("schema_version") != 1:
        raise ValueError("operational handoff state schema_version must be 1")
    return data


def _commit_line(label: str, section: dict[str, Any]) -> str:
    full = str(section.get("full", "")).strip()
    short = str(section.get("short", "")).strip() or full[:8]
    subject = str(section.get("subject", "")).strip()
    if not full or not subject:
        raise ValueError(f"{label} requires full commit and subject")
    return f"{label} is `{full}` (`{short}`), after `{subject}`."


def render_current_operational_handoff_state(
    root: Path | str = ".",
    *,
    path: Path | str = DEFAULT_OPERATIONAL_HANDOFF_STATE,
) -> tuple[str, ...]:
    data = load_operational_handoff_state(root, path=path)
    current_head = data.get("current_head")
    safe_state = data.get("last_substantive_work_state")
    if not isinstance(current_head, dict):
        raise ValueError("current_head must be a mapping")
    if not isinstance(safe_state, dict):
        raise ValueError("last_substantive_work_state must be a mapping")

    lines = [
        GENERATED_BLOCK_BEGIN,
        "## Current Operational Handoff State",
        "",
        _commit_line("Current verified main/admin HEAD", current_head),
        _commit_line("Last substantive work state", safe_state),
        "",
    ]

    administrative_context = data.get("administrative_context", [])
    if not isinstance(administrative_context, list):
        raise ValueError("administrative_context must be a list")
    lines.extend(str(item) for item in administrative_context)
    if administrative_context:
        lines.append("")

    freshness_policy = data.get("freshness_policy", {})
    if isinstance(freshness_policy, dict) and freshness_policy.get("text"):
        lines.append(str(freshness_policy["text"]))

    next_slice = data.get("next_safe_substantive_slice", {})
    if isinstance(next_slice, dict) and next_slice.get("text"):
        lines.append(str(next_slice["text"]))

    lines.extend(["", GENERATED_BLOCK_END, ""])
    return tuple(lines)
