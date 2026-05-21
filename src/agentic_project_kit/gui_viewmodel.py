from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


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


def action_to_view_model(action: object, *, destructive_actions_enabled: bool = False) -> GuiActionViewModel:
    name = _value(_field(action, "name", "action_id", "id"))
    safety_class = _value(_field(action, "safety_class", "safety", default="unknown"))
    description = _value(_field(action, "description", "summary", default=""))
    destructive = safety_class.lower() in {"destructive", "release", "remote", "mutation"}
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
