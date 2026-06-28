from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from agentic_project_kit.access_level_policy import visible_actions
from agentic_project_kit.access_levels import (
    ACCESS_LEVEL_ORDER,
    DEFAULT_ACCESS_LEVEL,
    AccessLevel,
    normalize_access_level,
)
from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.cockpit import CockpitAction, cockpit_actions
from agentic_project_kit.gui_button_catalog import GuiButtonDefinition, basic_gui_buttons
from agentic_project_kit.gui_communication_modes import (
    DEFAULT_COMMUNICATION_MODE,
    communication_mode_definitions,
    communication_mode_ids,
)
from agentic_project_kit.gui_gatekeeper_status import GuiGatekeeperStatus, build_gui_gatekeeper_status


@dataclass(frozen=True)
class GuiActionViewModel:
    name: str
    safety_class: str
    description: str
    enabled: bool
    requires_confirmation: bool


@dataclass(frozen=True)
class GuiControllerViewModel:
    title: str
    status: str
    actions: tuple[GuiActionViewModel, ...]
    destructive_actions_enabled: bool = False

    @property
    def action_count(self) -> int:
        return len(self.actions)


@dataclass(frozen=True)
class CommunicationModeViewModel:
    mode_id: str
    label: str
    role: str
    selected: bool
    is_default: bool
    safety_note: str


@dataclass(frozen=True)
class BasicCockpitButtonViewModel:
    command_id: str
    label: str
    tooltip: str
    safety_class: str
    enabled: bool
    disabled_reason: str
    wrapper_command: tuple[str, ...]
    source: str
    why: str
    structured_explanation: str | None = None


@dataclass(frozen=True)
class BasicCockpitRecommendedAction:
    label: str
    description: str
    tooltip: str
    kind: str
    command_id: str = ""
    cockpit_action_id: str = ""
    enabled: bool = False


@dataclass(frozen=True)
class BasicCockpitButtonGroupViewModel:
    group_id: str
    label: str
    description: str
    button_ids: tuple[str, ...]


@dataclass(frozen=True)
class BasicCockpitViewModel:
    title: str
    traffic_light_state: str
    traffic_light_color: str
    reason: str
    next_safe_action: str
    evidence: str
    mutation_allowed: bool
    state_source: str
    communication_mode: str
    communication_context_fresh: bool
    communication_context_reason: str
    required_next_reply: str | None
    access_level: str
    access_level_options: tuple[str, ...]
    access_level_explanation: str
    communication_modes: tuple[CommunicationModeViewModel, ...]
    buttons: tuple[BasicCockpitButtonViewModel, ...]
    last_result: str
    explanation: str
    recommended_action: BasicCockpitRecommendedAction = field(
        default_factory=lambda: BasicCockpitRecommendedAction(
            label="Inspect state",
            description="Refresh status before choosing a next action.",
            tooltip="Refresh the GUI gatekeeper status before any mutation.",
            kind="run_button",
            command_id="status-refresh",
            enabled=True,
        )
    )
    button_groups: tuple[BasicCockpitButtonGroupViewModel, ...] = ()
    recovery_hint: str = ""
    last_transfer_message: str = "No transfer task has been sent in this GUI session."

    @property
    def button_count(self) -> int:
        return len(self.buttons)


def _value(value: object, default: str = "") -> str:
    if value is None:
        return default
    raw = getattr(value, "value", value)
    return str(raw)


def _field(action: object, *names: str, default: object = "") -> object:
    for name in names:
        if hasattr(action, name):
            return getattr(action, name)
        if isinstance(action, dict) and name in action:
            return action[name]
    return default


def _normalize_state(value: object) -> str:
    return str(value or "").strip().upper().replace("-", "_")


def _traffic_light_from_gatekeeper_status(status: GuiGatekeeperStatus) -> tuple[str, str, str, str]:
    workflow_state = _normalize_state(status.workflow_state)
    current_work_state = _normalize_state(status.current_work_state)
    combined = {workflow_state, current_work_state}
    if status.required_next_reply == "d2" and not status.communication_context_fresh:
        return (
            "WAIT_FOR_D2",
            "yellow",
            status.communication_context_reason,
            "Send d2 only after the remote rule capsule is readable, then validate RULE_REFRESH_ACK.",
        )
    if combined & {"FAILED", "FAIL", "ERROR"}:
        return (
            "FAILED",
            "red",
            "The last known workflow state is failed.",
            "Open diagnostics and preserve evidence before any mutation.",
        )
    if status.blockers:
        return (
            "BLOCKED",
            "red",
            "; ".join(status.blockers),
            "Resolve deterministic blockers before running mutating actions.",
        )
    if combined & {"WAIT", "WAITING", "PENDING", "RUNNING", "REQUESTED", "UPLOADED"}:
        return (
            "WAIT",
            "yellow",
            f"Waiting workflow state: {status.current_work_state or status.workflow_state}.",
            "Wait for CI, remote state, transfer files, or wrapper completion.",
        )
    return (
        "READY",
        "green",
        "Gatekeeper state allows the next safe action.",
        "Use File Transfer as the default path or run a read-only diagnostic.",
    )


def _communication_modes(selected_mode: str) -> tuple[CommunicationModeViewModel, ...]:
    selected = selected_mode if selected_mode in communication_mode_ids() else DEFAULT_COMMUNICATION_MODE
    return tuple(
        CommunicationModeViewModel(
            definition.mode_id,
            definition.label,
            definition.role,
            selected == definition.mode_id,
            definition.is_default,
            definition.safety_note,
        )
        for definition in communication_mode_definitions()
    )


def access_level_explanation(access_level: str) -> str:
    selected = normalize_access_level(access_level)
    if selected == "basic":
        return "Basic shows status, routine work-order actions, and safe dirty-state recovery."
    if selected == "advanced":
        return "Advanced adds release, rules, and handoff workflow actions."
    return "Maintainer adds deep governance and drift audits."


def cockpit_actions_for_access_level(
    actions: Iterable[CockpitAction] | None = None,
    *,
    access_level: str = DEFAULT_ACCESS_LEVEL,
) -> tuple[CockpitAction, ...]:
    selected_level = normalize_access_level(access_level)
    selected_actions = list(actions) if actions is not None else cockpit_actions()
    return tuple(visible_actions(selected_actions, selected_level))


def _button_is_mutating(button: GuiButtonDefinition) -> bool:
    return button.safety_class in {
        "bounded-local-mutation",
        "bounded-mutation",
        "local-only",
        "remote-mutation",
        "destructive",
    }


def _restore_volatile_allowed(status: GuiGatekeeperStatus, traffic_state: str) -> bool:
    current_work_state = _normalize_state(status.current_work_state)
    workflow_state = _normalize_state(status.workflow_state)
    if current_work_state in {"FAILED", "FAIL", "ERROR"} or workflow_state in {"FAILED", "FAIL", "ERROR"}:
        return False
    if status.required_next_reply == "d2" and not status.communication_context_fresh:
        return False
    return traffic_state == "READY" or (
        status.git_dirty
        and status.communication_context_fresh
        and workflow_state in {"", "IDLE", "READY", "MISSING"}
    )


def _button_enabled_for_basic(button: GuiButtonDefinition, status: GuiGatekeeperStatus, traffic_state: str) -> tuple[bool, str, str]:
    if button.command_id == "restore-volatile":
        if not button.enabled:
            return (
                False,
                button.disabled_reason or "known volatile restore is disabled by policy",
                "Restore Volatile is the only dirty-state recovery button and remains wrapper-backed.",
            )
        if _restore_volatile_allowed(status, traffic_state):
            return (
                True,
                "",
                "known volatile restore is allowed as bounded recovery; product changes remain blocked",
            )
        return (
            False,
            "restore volatile is blocked while failed workflow evidence or d2 acknowledgement is pending",
            "Preserve failed workflow evidence and communication-rule state before cleanup.",
        )
    if button.safety_class in {"remote-mutation", "destructive"}:
        return False, "remote/destructive actions are blocked in Basic Mode", "Basic Mode exposes readiness only for this action class."
    if "release" in button.command_id or "publish" in button.command_id:
        return False, "release publish/destructive actions are blocked in Basic Mode", "Release controls stay readiness-only until a guarded maintainer flow exists."
    if not _button_is_mutating(button):
        return True, "", "read-only diagnostic or status action is allowed"
    if not button.enabled:
        return (
            False,
            button.disabled_reason or "mutating Basic action has no guarded dispatcher yet",
            "Basic Mode may show this capability, but execution stays disabled until the catalog marks it safe.",
        )
    if traffic_state == "READY" and status.ready_for_mutating_actions:
        return True, "", "mutating local/fixed-path action is allowed only after gatekeeper revalidation"
    reason = "mutating action requires READY state and clean gatekeeper revalidation"
    if status.git_dirty:
        reason = "mutating action blocked because working tree is dirty"
    elif traffic_state != "READY":
        reason = f"mutating action blocked while traffic light is {traffic_state}"
    return False, reason, "Basic Mode keeps mutation disabled until deterministic state is READY."


def _basic_button_view_models(
    status: GuiGatekeeperStatus,
    *,
    traffic_state: str,
    buttons: Iterable[GuiButtonDefinition] | None = None,
) -> tuple[BasicCockpitButtonViewModel, ...]:
    selected = tuple(buttons) if buttons is not None else basic_gui_buttons()
    items: list[BasicCockpitButtonViewModel] = []
    for button in selected:
        enabled, disabled_reason, why = _button_enabled_for_basic(button, status, traffic_state)
        if not disabled_reason and not button.enabled and not _button_is_mutating(button):
            disabled_reason = button.disabled_reason
            enabled = False
        items.append(
            BasicCockpitButtonViewModel(
                command_id=button.command_id,
                label=button.label,
                tooltip=button.tooltip,
                safety_class=button.safety_class,
                enabled=enabled,
                disabled_reason=disabled_reason,
                wrapper_command=button.wrapper_command,
                source="gui_button_catalog",
                why=why,
                structured_explanation=button.structured_explanation,
            )
        )
    return tuple(items)


def _recommended_action_for_state(
    status: GuiGatekeeperStatus,
    *,
    traffic_state: str,
    next_action: str,
    mutation_allowed: bool,
) -> BasicCockpitRecommendedAction:
    if status.required_next_reply == "d2" and not status.communication_context_fresh:
        return BasicCockpitRecommendedAction(
            label="Complete d2 acknowledgement",
            description=next_action,
            tooltip="Send d2 in chat and wait for RULE_REFRESH_ACK before any mutation.",
            kind="show_hint",
            enabled=False,
        )
    if traffic_state in {"FAILED", "BLOCKED"}:
        return BasicCockpitRecommendedAction(
            label="Open diagnostics",
            description="Load Doctor so the blocker can be inspected without running it or mutating the repository.",
            tooltip="Select the read-only Doctor action. It does not repair or mutate by itself.",
            kind="select_action",
            cockpit_action_id="gate.doctor",
            enabled=True,
        )
    if traffic_state == "WAIT":
        return BasicCockpitRecommendedAction(
            label="Show state and next step",
            description=next_action,
            tooltip="Select the read-only workflow state action while the workflow is waiting.",
            kind="select_action",
            cockpit_action_id="workflow.state",
            enabled=True,
        )
    if mutation_allowed:
        return BasicCockpitRecommendedAction(
            label="Run next work order",
            description=next_action,
            tooltip="Run the registered Basic action for the next guarded file-transfer work order.",
            kind="run_button",
            command_id="run-next-work-order",
            cockpit_action_id="dialog.rn",
            enabled=True,
        )
    return BasicCockpitRecommendedAction(
        label="Refresh status",
        description=next_action,
        tooltip="Refresh gatekeeper state before choosing a mutating action.",
        kind="run_button",
        command_id="status-refresh",
        cockpit_action_id="workflow.state",
        enabled=True,
    )


def _button_group_for(button: BasicCockpitButtonViewModel) -> tuple[str, str, str]:
    command_id = button.command_id
    if command_id in {"status-refresh", "run-next-work-order", "close-out-last-run"}:
        return ("routine", "Routine", "Normal next-step and closeout controls.")
    if command_id in {"communication-rules-refresh", "handoff-rules-refresh"}:
        return ("transfer", "Transfer", "Communication, transfer, and handoff controls.")
    if command_id in {"diagnose", "doctor", "check-docs"} or "diagnose" in command_id:
        return ("diagnostics", "Diagnostics", "Read-only checks for blockers and drift.")
    return ("advanced", "Advanced", "Less common controls that stay behind policy gates.")


def _group_basic_buttons(
    buttons: tuple[BasicCockpitButtonViewModel, ...],
) -> tuple[BasicCockpitButtonGroupViewModel, ...]:
    order = ("routine", "transfer", "diagnostics", "advanced")
    metadata: dict[str, tuple[str, str]] = {}
    grouped: dict[str, list[str]] = {}
    for button in buttons:
        group_id, label, description = _button_group_for(button)
        metadata[group_id] = (label, description)
        grouped.setdefault(group_id, []).append(button.command_id)
    result: list[BasicCockpitButtonGroupViewModel] = []
    for group_id in order:
        button_ids = tuple(grouped.get(group_id, ()))
        if not button_ids:
            continue
        label, description = metadata[group_id]
        result.append(
            BasicCockpitButtonGroupViewModel(
                group_id=group_id,
                label=label,
                description=description,
                button_ids=button_ids,
            )
        )
    return tuple(result)


def _recovery_hint(status: GuiGatekeeperStatus, traffic_state: str) -> str:
    if status.required_next_reply == "d2" and not status.communication_context_fresh:
        return "Recovery: send d2 in chat and require RULE_REFRESH_ACK before running or sending tasks."
    if traffic_state == "FAILED":
        return "Recovery: preserve evidence, inspect diagnostics, and do not clean up until the failure is classified."
    if traffic_state == "BLOCKED":
        return "Recovery: resolve deterministic blockers first; read-only diagnostics remain safe."
    if traffic_state == "WAIT":
        return "Recovery: wait for the external workflow, CI, or transfer state to settle before retrying."
    return ""


def build_basic_cockpit_view_model(
    project_root: Path | str = ".",
    *,
    gatekeeper_status: GuiGatekeeperStatus | None = None,
    communication_mode: str = "file_transfer",
    access_level: str = DEFAULT_ACCESS_LEVEL,
    buttons: Iterable[GuiButtonDefinition] | None = None,
) -> BasicCockpitViewModel:
    status = gatekeeper_status or build_gui_gatekeeper_status(project_root)
    traffic_state, color, reason, next_action = _traffic_light_from_gatekeeper_status(status)
    modes = _communication_modes(communication_mode)
    selected_mode = next((mode.mode_id for mode in modes if mode.selected), "file_transfer")
    selected_access_level: AccessLevel = normalize_access_level(access_level)
    mutation_allowed = traffic_state == "READY" and status.ready_for_mutating_actions
    button_models = _basic_button_view_models(status, traffic_state=traffic_state, buttons=buttons)
    evidence = (
        f"branch={status.branch}; workflow_state={status.workflow_state}; "
        f"current_work_state={status.current_work_state or '<none>'}"
    )
    return BasicCockpitViewModel(
        title="agentic-project-kit Cockpit - Basic",
        traffic_light_state=traffic_state,
        traffic_light_color=color,
        reason=reason,
        next_safe_action=next_action,
        evidence=evidence,
        mutation_allowed=mutation_allowed,
        state_source="gui_gatekeeper_status",
        communication_mode=selected_mode,
        communication_context_fresh=status.communication_context_fresh,
        communication_context_reason=status.communication_context_reason,
        required_next_reply=status.required_next_reply,
        access_level=selected_access_level,
        access_level_options=tuple(ACCESS_LEVEL_ORDER),
        access_level_explanation=access_level_explanation(selected_access_level),
        communication_modes=modes,
        buttons=button_models,
        last_result="No action has run in this GUI session.",
        explanation="Basic Mode is a thin control surface over registered wrappers, gatekeeper state, typed work orders, evidence, and readiness reports.",
        recommended_action=_recommended_action_for_state(
            status,
            traffic_state=traffic_state,
            next_action=next_action,
            mutation_allowed=mutation_allowed,
        ),
        button_groups=_group_basic_buttons(button_models),
        recovery_hint=_recovery_hint(status, traffic_state),
    )


def action_to_view_model(action: object, *, destructive_actions_enabled: bool = False) -> GuiActionViewModel:
    name = _value(_field(action, "name", "action_id", "id"))
    safety_class = _value(_field(action, "safety_class", "safety", default="unknown"))
    description = _value(_field(action, "description", "summary", default=""))
    normalized_safety_class = safety_class.lower().replace("_", "-")
    destructive = normalized_safety_class in {"destructive", "release", "remote", "mutation", "remote-mutation"}
    return GuiActionViewModel(
        name=name,
        safety_class=safety_class,
        description=description,
        enabled=not destructive or destructive_actions_enabled,
        requires_confirmation=destructive,
    )


def build_gui_controller_view_model(
    actions: Iterable[object],
    *,
    title: str = "agentic-project-kit Cockpit",
    status: str = "ready",
    destructive_actions_enabled: bool = False,
) -> GuiControllerViewModel:
    view_actions = tuple(
        action_to_view_model(action, destructive_actions_enabled=destructive_actions_enabled)
        for action in actions
    )
    return GuiControllerViewModel(
        title=title,
        status=status,
        actions=view_actions,
        destructive_actions_enabled=destructive_actions_enabled,
    )



@dataclass(frozen=True)
class GuiActionDetail:
    name: str
    label: str
    description: str
    safety_class: str
    enabled: bool
    requires_confirmation: bool
    disabled_reason: str
    tooltip: str
    icon_id: str
    evidence_hint: str
    parameter_hint: str


@dataclass(frozen=True)
class GuiActionDetailPanel:
    title: str
    selected_action_name: str
    actions: tuple[GuiActionDetail, ...]
    disabled_action_names: tuple[str, ...]
    status_message: str


def _gui_detail_value(value: object) -> str:
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    return str(value)


def _gui_detail_label(name: str) -> str:
    return name.replace("-", " ").title()


def _gui_detail_confirmation_required(safety_class: str, enabled: bool) -> bool:
    lowered = safety_class.lower()
    return enabled and any(token in lowered for token in ("remote", "mutation", "destructive", "release"))


def _gui_detail_evidence_hint(safety_class: str, enabled: bool) -> str:
    lowered = safety_class.lower()
    if not enabled:
        return "disabled action; no execution evidence expected"
    if "read" in lowered:
        return "local transcript is sufficient unless promoted to a workflow evidence slice"
    if "local" in lowered:
        return "local terminal log is required; remote evidence only after commit and push"
    return "remote committed evidence is required before claiming no-copy completion"


def _gui_detail_parameter_hint(action: object | None) -> str:
    parameters = getattr(action, "parameters", None)
    if parameters:
        return ", ".join(str(parameter) for parameter in parameters)
    return "no structured parameters registered"


def _gui_detail_button_metadata() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for action in list_actions():
        name = str(getattr(action, "name", ""))
        if name:
            result[name] = (f"Run {name} through the governed GUI action layer.", name.replace("-", "_"))
    result["release-publish"] = ("Publishing is disabled in the GUI until explicit release confirmation is implemented.", "release_publish_disabled")
    return result


def build_gui_action_detail_panel(selected_action_name: str = "") -> GuiActionDetailPanel:
    disabled = {"release-publish"}
    button_metadata = _gui_detail_button_metadata()
    items: list[GuiActionDetail] = []
    for action in list_actions():
        name = str(getattr(action, "name", ""))
        if not name:
            continue
        tooltip, icon_id = button_metadata.get(name, ("No toolbar/action button assigned yet.", "none"))
        enabled = name not in disabled
        safety_class = _gui_detail_value(getattr(action, "safety_class", "unknown"))
        description = str(getattr(action, "description", ""))
        disabled_reason = "disabled by GUI safety policy" if not enabled else ""
        items.append(
            GuiActionDetail(
                name=name,
                label=_gui_detail_label(name),
                description=description,
                safety_class=safety_class,
                enabled=enabled,
                requires_confirmation=_gui_detail_confirmation_required(safety_class, enabled),
                disabled_reason=disabled_reason,
                tooltip=tooltip,
                icon_id=icon_id,
                evidence_hint=_gui_detail_evidence_hint(safety_class, enabled),
                parameter_hint=_gui_detail_parameter_hint(action),
            )
        )
    existing_names = {item.name for item in items}
    if "release-publish" not in existing_names:
        tooltip, icon_id = button_metadata.get(
            "release-publish",
            ("Publishing is disabled in the GUI until explicit release confirmation is implemented.", "release_publish_disabled"),
        )
        items.append(
            GuiActionDetail(
                name="release-publish",
                label=_gui_detail_label("release-publish"),
                description="Publishes a release; disabled in the GUI until explicit confirmation support exists.",
                safety_class="destructive",
                enabled=False,
                requires_confirmation=False,
                disabled_reason="disabled by GUI safety policy",
                tooltip=tooltip,
                icon_id=icon_id,
                evidence_hint="disabled action; no execution evidence expected",
                parameter_hint="disabled GUI-only release action",
            )
        )
    items_tuple = tuple(sorted(items, key=lambda item: item.name))
    selected = selected_action_name if any(item.name == selected_action_name for item in items_tuple) else ""
    return GuiActionDetailPanel(
        title="Action details",
        selected_action_name=selected,
        actions=items_tuple,
        disabled_action_names=tuple(sorted(disabled)),
        status_message="ready" if items_tuple else "no actions registered",
    )
