from __future__ import annotations

from collections.abc import Iterable

from agentic_project_kit.access_levels import AccessLevel, meets_min_access
from agentic_project_kit.cockpit import CockpitAction


def can_show_action(action: CockpitAction, level: AccessLevel) -> bool:
    return meets_min_access(level, action.min_access_level)


def visible_actions(actions: Iterable[CockpitAction], level: AccessLevel) -> list[CockpitAction]:
    return [action for action in actions if can_show_action(action, level)]
