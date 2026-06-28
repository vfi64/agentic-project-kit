from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.access_levels import DEFAULT_ACCESS_LEVEL
from agentic_project_kit.cockpit import (
    BOUNDED,
    DESTRUCTIVE,
    READ_ONLY,
    CockpitAction,
    CockpitActionResult,
)
from agentic_project_kit.gui_viewmodel import cockpit_actions_for_access_level


SAFETY_SORT_ORDER = {READ_ONLY: 0, BOUNDED: 1, DESTRUCTIVE: 2}


@dataclass(frozen=True)
class GuiActionView:
    action_id: str
    label: str
    category: str
    safety: str
    command: tuple[str, ...]
    description: str
    short_description: str
    min_access_level: str
    can_run_by_default: bool
    structured_explanation: str | None = None


@dataclass(frozen=True)
class GuiActionGroupView:
    group_id: str
    label: str
    description: str
    actions: tuple[GuiActionView, ...]


STRUCTURED_ACTION_EXPLANATIONS = {
    "git.status": (
        "PURPOSE: Show local repository dirty state.\n"
        "EFFECT: Reads git status only.\n"
        "WHEN: Use before any mutation or PR closeout.\n"
        "BLOCKED WHEN: Git status cannot run.\n"
        "AFTER PASS: Continue with the next safe action.\n"
        "AFTER FAIL: Diagnose repository access."
    ),
    "workflow.state": (
        "PURPOSE: Show workflow and gatekeeper readiness.\n"
        "EFFECT: Reads workflow state only.\n"
        "WHEN: Use when deciding whether the GUI may proceed.\n"
        "BLOCKED WHEN: Workflow state files are unreadable.\n"
        "AFTER PASS: Continue with the recommended action.\n"
        "AFTER FAIL: Preserve evidence and diagnose workflow state."
    ),
    "dialog.rn": (
        "PURPOSE: Run the next file-transfer work order through the wrapper.\n"
        "EFFECT: Performs bounded local workflow mutation.\n"
        "WHEN: Use only after READY state and valid work order.\n"
        "BLOCKED WHEN: d2 is pending, state is dirty, or work order is invalid.\n"
        "AFTER PASS: Read the generated result/evidence.\n"
        "AFTER FAIL: Inspect the report before retrying."
    ),
    "dialog.rnc": (
        "PURPOSE: Close out the last run through the fixed closeout wrapper.\n"
        "EFFECT: Commits/pushes expected closeout paths when guarded.\n"
        "WHEN: Use after a successful bounded run.\n"
        "BLOCKED WHEN: Required evidence or clean state is missing.\n"
        "AFTER PASS: Continue with handoff or next slice.\n"
        "AFTER FAIL: Diagnose closeout evidence."
    ),
    "rules.communication-refresh": (
        "PURPOSE: Publish the current communication rule capsule.\n"
        "EFFECT: Writes generated rule artifacts and a local d2 pending state.\n"
        "WHEN: Use when the assistant must reload communication rules.\n"
        "BLOCKED WHEN: Local mutation is not safe.\n"
        "AFTER PASS: Send d2 and require machine-readable ACK.\n"
        "AFTER FAIL: Diagnose rule-refresh output."
    ),
}


def build_gui_action_views(
    actions: list[CockpitAction] | None = None,
    *,
    access_level: str = DEFAULT_ACCESS_LEVEL,
) -> list[GuiActionView]:
    selected = cockpit_actions_for_access_level(actions, access_level=access_level)
    return [
        GuiActionView(
            action_id=action.action_id,
            label=action.label,
            category=action.category,
            safety=action.safety,
            command=action.command,
            description=action.description,
            short_description=action.short_description,
            min_access_level=action.min_access_level,
            can_run_by_default=action.safety == READ_ONLY,
            structured_explanation=STRUCTURED_ACTION_EXPLANATIONS.get(action.action_id),
        )
        for action in selected
    ]


SAFETY_EXPLANATIONS = {
    "read_only": "Safe default: this action may be executed from the GUI through the shared cockpit layer.",
    "bounded": "Blocked by default: bounded workflow actions require an explicit non-GUI allow path.",
    "destructive": "Blocked: destructive actions are not executable from the GUI cockpit.",
}


def explain_safety(safety: str) -> str:
    return SAFETY_EXPLANATIONS.get(safety, f"Blocked: unknown safety class {safety}.")


def ordered_action_views(
    actions: list[GuiActionView] | None = None,
    *,
    access_level: str = DEFAULT_ACCESS_LEVEL,
) -> list[GuiActionView]:
    selected = actions if actions is not None else build_gui_action_views(access_level=access_level)
    return sorted(
        selected,
        key=lambda action: (
            SAFETY_SORT_ORDER.get(action.safety, len(SAFETY_SORT_ORDER)),
            action.label.casefold(),
            action.action_id,
        ),
    )


def action_group_for(action: GuiActionView) -> tuple[str, str, str]:
    if action.category in {"git", "workflow"} and action.safety == READ_ONLY:
        return ("routine", "Routine", "Frequent read-only orientation checks.")
    if action.category in {"dialog", "transfer"} or action.action_id == "workflow.go":
        return ("transfer", "Transfer", "File-transfer work-order and closeout actions.")
    if action.category in {"gate", "audit"}:
        return ("diagnostics", "Diagnostics", "Read-only checks for blockers and drift.")
    return ("advanced", "Advanced", "Release, handoff, and rule-refresh controls.")


def grouped_action_views(actions: list[GuiActionView] | tuple[GuiActionView, ...]) -> tuple[GuiActionGroupView, ...]:
    order = ("routine", "transfer", "diagnostics", "advanced")
    labels: dict[str, tuple[str, str]] = {}
    buckets: dict[str, list[GuiActionView]] = {}
    for action in actions:
        group_id, label, description = action_group_for(action)
        labels[group_id] = (label, description)
        buckets.setdefault(group_id, []).append(action)
    groups: list[GuiActionGroupView] = []
    for group_id in order:
        actions_in_group = tuple(buckets.get(group_id, ()))
        if not actions_in_group:
            continue
        label, description = labels[group_id]
        groups.append(GuiActionGroupView(group_id, label, description, actions_in_group))
    return tuple(groups)


def format_action_details(action: GuiActionView) -> str:
    lines = [
        f"action_id={action.action_id}",
        f"label={action.label}",
        f"category={action.category}",
        f"safety={action.safety}",
        f"can_run_by_default={str(action.can_run_by_default).lower()}",
        "command=" + " ".join(action.command),
        f"description={action.description}",
        f"short_description={action.short_description}",
        f"min_access_level={action.min_access_level}",
        f"safety_explanation={explain_safety(action.safety)}",
    ]
    if action.structured_explanation:
        lines.extend(["", "structured_explanation:", action.structured_explanation])
    return "\n".join(lines)


def format_action_result(result: CockpitActionResult) -> str:
    lines = [
        f"action_id={result.action_id}",
        "status=" + ("completed" if result.executed else "blocked"),
        f"allowed={str(result.allowed).lower()}",
        f"executed={str(result.executed).lower()}",
        f"returncode={result.returncode}",
    ]
    if result.message:
        lines.append(result.message)
    if result.stdout:
        lines.extend(["", "stdout:", result.stdout])
    if result.stderr:
        lines.extend(["", "stderr:", result.stderr])
    return "\n".join(lines).rstrip()
