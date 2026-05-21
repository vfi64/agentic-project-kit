from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from agentic_project_kit.gui_action_renderer import render_controller_view_model
from agentic_project_kit.gui_viewmodel import build_gui_controller_view_model


@dataclass(frozen=True)
class GuiPresenterResult:
    ok: bool
    action_count: int
    rendered: str
    message: str


def build_no_window_presenter_result(
    actions: Iterable[object],
    *,
    title: str = "agentic-project-kit Cockpit",
    status: str = "dry-run-ready",
    destructive_actions_enabled: bool = False,
) -> GuiPresenterResult:
    view_model = build_gui_controller_view_model(
        actions,
        title=title,
        status=status,
        destructive_actions_enabled=destructive_actions_enabled,
    )
    rendered = render_controller_view_model(view_model)
    return GuiPresenterResult(
        ok=True,
        action_count=view_model.action_count,
        rendered=rendered,
        message="GUI no-window presenter passed.",
    )
