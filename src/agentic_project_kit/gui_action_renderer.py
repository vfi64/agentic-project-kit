from __future__ import annotations

from collections.abc import Iterable

from agentic_project_kit.gui_viewmodel import (
    BasicCockpitViewModel,
    GuiActionViewModel,
    GuiControllerViewModel,
)


def render_action_row(action: GuiActionViewModel, index: int) -> str:
    state = "enabled" if action.enabled else "disabled"
    confirmation = "confirm" if action.requires_confirmation else "no-confirm"
    description = action.description.strip() or "no description"
    return (
        f"{index:02d}. {action.name} "
        f"[{action.safety_class}; {state}; {confirmation}] - {description}"
    )


def render_action_rows(actions: Iterable[GuiActionViewModel]) -> tuple[str, ...]:
    return tuple(render_action_row(action, index) for index, action in enumerate(actions, start=1))


def render_controller_view_model(view_model: GuiControllerViewModel) -> str:
    lines = [
        view_model.title,
        f"status={view_model.status}",
        f"action_count={view_model.action_count}",
        f"destructive_actions_enabled={str(view_model.destructive_actions_enabled).lower()}",
        "actions:",
    ]
    rows = render_action_rows(view_model.actions)
    if rows:
        lines.extend(rows)
    else:
        lines.append("none")
    return "\n".join(lines)


def render_basic_cockpit_view_model(view_model: BasicCockpitViewModel) -> str:
    lines = [
        view_model.title,
        f"traffic_light_state={view_model.traffic_light_state}",
        f"traffic_light_color={view_model.traffic_light_color}",
        f"communication_mode={view_model.communication_mode}",
        f"mutation_allowed={str(view_model.mutation_allowed).lower()}",
        f"state_source={view_model.state_source}",
        f"reason={view_model.reason}",
        f"next_safe_action={view_model.next_safe_action}",
        f"recommended_action={view_model.recommended_action.label}",
        f"recommended_action_kind={view_model.recommended_action.kind}",
        f"evidence={view_model.evidence}",
        f"last_result={view_model.last_result}",
        "communication_modes:",
    ]
    for mode in view_model.communication_modes:
        selected = "selected" if mode.selected else "available"
        default = "default" if mode.is_default else "non-default"
        lines.append(f"- {mode.mode_id} [{mode.role}; {selected}; {default}] {mode.safety_note}")
    lines.append("buttons:")
    for button in view_model.buttons:
        state = "enabled" if button.enabled else "disabled"
        command = " ".join(button.wrapper_command) if button.wrapper_command else "<no-wrapper>"
        reason = button.disabled_reason or button.why
        lines.append(
            f"- {button.command_id} [{button.safety_class}; {state}] "
            f"label={button.label}; tooltip={button.tooltip}; wrapper={command}; "
            f"source={button.source}; why={reason}"
        )
    if view_model.button_groups:
        lines.append("button_groups:")
        for group in view_model.button_groups:
            lines.append(
                f"- {group.group_id}: {group.label}; buttons={','.join(group.button_ids)}"
            )
    if view_model.recovery_hint:
        lines.append(f"recovery_hint={view_model.recovery_hint}")
    lines.append(f"explanation={view_model.explanation}")
    return "\n".join(lines)
