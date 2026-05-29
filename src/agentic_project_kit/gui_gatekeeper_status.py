"""Deterministic GUI gatekeeper status model.

This module is intentionally read-only. It builds a stable status snapshot that
GUI surfaces can render before allowing action execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Sequence
import yaml

from agentic_project_kit.action_registry import ACTIONS, SafetyClass


@dataclass(frozen=True)
class GuiGatekeeperActionStatus:
    action_id: str
    safety_class: str
    mutation_scope: str
    enabled: bool
    reason: str


@dataclass(frozen=True)
class GuiGatekeeperStatus:
    branch: str
    git_dirty: bool
    workflow_state: str
    current_work_present: bool
    current_work_state: str | None
    ready_for_read_only_actions: bool
    ready_for_mutating_actions: bool
    action_statuses: tuple[GuiGatekeeperActionStatus, ...]
    blockers: tuple[str, ...]


def build_gui_gatekeeper_status(
    project_root: Path | str = ".",
    *,
    actions: Sequence[object] | None = None,
) -> GuiGatekeeperStatus:
    """Build a deterministic, read-only GUI gatekeeper snapshot."""

    root = Path(project_root)
    branch = _git_branch(root)
    git_dirty = _git_dirty(root)
    workflow_state = _read_text(root / ".agentic" / "workflow_state", "missing").strip() or "missing"
    current_work_path = root / ".agentic" / "current_work.yaml"
    current_work_present = current_work_path.exists()
    current_work_state = _read_current_work_state(current_work_path) if current_work_present else None

    blockers: list[str] = []
    if branch == "unknown":
        blockers.append("git branch could not be determined")
    if git_dirty:
        blockers.append("working tree is dirty")
    if workflow_state not in {"IDLE", "READY"}:
        blockers.append(f"workflow_state is {workflow_state}")

    ready_for_read_only_actions = not git_dirty
    ready_for_mutating_actions = (
        not git_dirty
        and branch != "unknown"
        and workflow_state in {"IDLE", "READY"}
    )

    action_statuses = tuple(
        classify_gui_gatekeeper_action(
            action,
            git_dirty=git_dirty,
            local_only_allowed=ready_for_mutating_actions,
        )
        for action in (actions if actions is not None else ACTIONS)
    )

    return GuiGatekeeperStatus(
        branch=branch,
        git_dirty=git_dirty,
        workflow_state=workflow_state,
        current_work_present=current_work_present,
        current_work_state=current_work_state,
        ready_for_read_only_actions=ready_for_read_only_actions,
        ready_for_mutating_actions=ready_for_mutating_actions,
        action_statuses=action_statuses,
        blockers=tuple(blockers),
    )


def classify_gui_gatekeeper_action(
    action: object,
    *,
    git_dirty: bool,
    local_only_allowed: bool = False,
) -> GuiGatekeeperActionStatus:
    action_id = str(getattr(action, "name", getattr(action, "action_id", "<unknown>")))
    safety_class = _safety_value(getattr(action, "safety_class", getattr(action, "safety", "unknown")))
    mutation_scope = str(getattr(action, "mutation_scope", "unknown"))

    if safety_class == SafetyClass.READ_ONLY.value and not git_dirty:
        return GuiGatekeeperActionStatus(
            action_id=action_id,
            safety_class=safety_class,
            mutation_scope=mutation_scope,
            enabled=True,
            reason="read-only action allowed in clean GUI gatekeeper state",
        )

    if safety_class == SafetyClass.READ_ONLY.value and git_dirty:
        return GuiGatekeeperActionStatus(
            action_id=action_id,
            safety_class=safety_class,
            mutation_scope=mutation_scope,
            enabled=False,
            reason="read-only action blocked because working tree is dirty",
        )

    if safety_class == SafetyClass.LOCAL_ONLY.value and local_only_allowed:
        return GuiGatekeeperActionStatus(
            action_id=action_id,
            safety_class=safety_class,
            mutation_scope=mutation_scope,
            enabled=True,
            reason="local-only action allowed in clean GUI gatekeeper state",
        )

    if safety_class == SafetyClass.LOCAL_ONLY.value:
        return GuiGatekeeperActionStatus(
            action_id=action_id,
            safety_class=safety_class,
            mutation_scope=mutation_scope,
            enabled=False,
            reason="local-only action blocked because GUI gatekeeper is not clean",
        )

    return GuiGatekeeperActionStatus(
        action_id=action_id,
        safety_class=safety_class,
        mutation_scope=mutation_scope,
        enabled=False,
        reason="GUI gatekeeper blocks remote mutation actions",
    )


def render_gui_gatekeeper_status(status: GuiGatekeeperStatus) -> str:
    lines = [
        "GUI_GATEKEEPER_STATUS",
        f"branch={status.branch}",
        f"git_dirty={str(status.git_dirty).lower()}",
        f"workflow_state={status.workflow_state}",
        f"current_work_present={str(status.current_work_present).lower()}",
        f"current_work_state={status.current_work_state or '<none>'}",
        f"ready_for_read_only_actions={str(status.ready_for_read_only_actions).lower()}",
        f"ready_for_mutating_actions={str(status.ready_for_mutating_actions).lower()}",
        "blockers=" + (",".join(status.blockers) if status.blockers else "<none>"),
    ]
    for action in status.action_statuses:
        lines.append(
            "action="
            + action.action_id
            + ";safety="
            + action.safety_class
            + ";enabled="
            + str(action.enabled).lower()
            + ";reason="
            + action.reason
        )
    return "\n".join(lines)


def gui_gatekeeper_status_as_json_data(status: GuiGatekeeperStatus) -> dict[str, object]:
    return {
        "schema_version": 1,
        "branch": status.branch,
        "git_dirty": status.git_dirty,
        "workflow_state": status.workflow_state,
        "current_work_present": status.current_work_present,
        "current_work_state": status.current_work_state,
        "ready_for_read_only_actions": status.ready_for_read_only_actions,
        "ready_for_mutating_actions": status.ready_for_mutating_actions,
        "blockers": list(status.blockers),
        "actions": [
            {
                "action_id": action.action_id,
                "safety_class": action.safety_class,
                "mutation_scope": action.mutation_scope,
                "enabled": action.enabled,
                "reason": action.reason,
            }
            for action in status.action_statuses
        ],
    }


def _safety_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower().replace("_", "-")


def _git_branch(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_dirty(root: Path) -> bool:
    try:
        return bool(
            subprocess.check_output(
                ["git", "-C", str(root), "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return True


def _read_text(path: Path, default: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


def _read_current_work_state(path: Path) -> str | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    state = data.get("state")
    return str(state) if state is not None else None
