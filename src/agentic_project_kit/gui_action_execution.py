from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass


BLOCKED_SAFETY_CLASSES = frozenset({
    "destructive",
    "local-only",
    "mutation",
    "release",
    "remote",
    "remote-mutation",
})


@dataclass(frozen=True)
class GuiActionExecutionResult:
    action_name: str
    safety_class: str
    allowed: bool
    executed: bool
    returncode: int
    message: str
    output: str = ""


def _field(action: object, *names: str, default: object = "") -> object:
    for name in names:
        if hasattr(action, name):
            return getattr(action, name)
    return default


def _value(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def normalize_safety_class(value: object) -> str:
    return _value(value).strip().lower().replace("_", "-")


def action_identity(action: object) -> str:
    return _value(_field(action, "name", "action_id", "id"))


def action_safety_class(action: object) -> str:
    return normalize_safety_class(_field(action, "safety_class", "safety", default="unknown"))


def is_bounded_read_only_action(action: object) -> bool:
    return action_safety_class(action) == "read-only"


def find_action(actions: Iterable[object], action_name: str) -> object | None:
    for action in actions:
        if action_identity(action) == action_name:
            return action
    return None


def run_bounded_read_only_action(
    actions: Iterable[object],
    action_name: str,
    *,
    executor: Callable[[object], tuple[int, str]] | None = None,
) -> GuiActionExecutionResult:
    action = find_action(actions, action_name)
    if action is None:
        return GuiActionExecutionResult(action_name, "unknown", False, False, 2, "Action not found.")

    name = action_identity(action)
    safety = action_safety_class(action)
    if safety in BLOCKED_SAFETY_CLASSES or safety != "read-only":
        return GuiActionExecutionResult(
            name,
            safety,
            False,
            False,
            2,
            "Action blocked: GUI MVP execution is limited to read-only actions.",
        )

    if executor is None:
        return GuiActionExecutionResult(
            name,
            safety,
            True,
            False,
            0,
            "Action allowed but not executed: no executor was provided.",
        )

    returncode, output = executor(action)
    return GuiActionExecutionResult(
        name,
        safety,
        True,
        True,
        int(returncode),
        "Action executed through bounded read-only executor.",
        output,
    )
