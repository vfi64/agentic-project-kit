from __future__ import annotations

from collections.abc import Iterable

from agentic_project_kit.gui_viewmodel import GuiActionViewModel
from agentic_project_kit.gui_viewmodel import GuiControllerViewModel


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
