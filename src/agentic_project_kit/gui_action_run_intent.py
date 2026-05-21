from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class GuiActionLike(Protocol):
    name: str
    safety_class: object
    description: str


@dataclass(frozen=True)
class GuiActionRunIntent:
    action_name: str
    known: bool
    safety_class: str
    enabled: bool
    requires_confirmation: bool
    confirmation_token: str
    blocked_reason: str
    output_target: str
    terminal_log: str
    would_execute: bool = False


def _safety_name(value: object) -> str:
    name = getattr(value, "value", value)
    return str(name).replace("-", "_")


def _confirmation_token(action_name: str, safety_class: str) -> str:
    if safety_class in {"remote_mutation", "destructive"}:
        return "confirm-" + action_name
    return ""


def build_gui_action_run_intent(
    actions: list[GuiActionLike],
    action_name: str,
    *, confirmation: str = "",
    allow_remote_mutation: bool = False,
    allow_destructive: bool = False,
    terminal_log: str = "NONE",
) -> GuiActionRunIntent:
    action_by_name = {action.name: action for action in actions}
    action = action_by_name.get(action_name)
    if action is None:
        return GuiActionRunIntent(
            action_name=action_name,
            known=False,
            safety_class="unknown",
            enabled=False,
            requires_confirmation=False,
            confirmation_token="",
            blocked_reason="unknown action",
            output_target="output-status-panel",
            terminal_log=terminal_log,
        )
    safety = _safety_name(action.safety_class)
    token = _confirmation_token(action.name, safety)
    needs_confirmation = bool(token)
    blocked = ""
    if safety == "remote_mutation" and not allow_remote_mutation:
        blocked = "remote mutation disabled in GUI safe mode"
    if safety == "destructive" and not allow_destructive:
        blocked = "destructive action disabled in GUI safe mode"
    if not blocked and needs_confirmation and confirmation != token:
        blocked = "missing confirmation token"
    enabled = blocked == ""
    return GuiActionRunIntent(
        action_name=action.name,
        known=True,
        safety_class=safety,
        enabled=enabled,
        requires_confirmation=needs_confirmation,
        confirmation_token=token,
        blocked_reason=blocked,
        output_target="output-status-panel",
        terminal_log=terminal_log,
    )


def render_gui_action_run_intent(intent: GuiActionRunIntent) -> str:
    lines = [
        "GUI ACTION RUN INTENT",
        "action_name=" + intent.action_name,
        "known=" + str(intent.known).lower(),
        "safety_class=" + intent.safety_class,
        "enabled=" + str(intent.enabled).lower(),
        "requires_confirmation=" + str(intent.requires_confirmation).lower(),
        "confirmation_token=" + (intent.confirmation_token or "NONE"),
        "blocked_reason=" + (intent.blocked_reason or "NONE"),
        "output_target=" + intent.output_target,
        "terminal_log=" + intent.terminal_log,
        "would_execute=" + str(intent.would_execute).lower(),
    ]
    return "\n".join(lines)
