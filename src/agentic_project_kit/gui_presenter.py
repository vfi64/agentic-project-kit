from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from agentic_project_kit.gui_action_renderer import (
    render_basic_cockpit_view_model,
    render_controller_view_model,
)
from agentic_project_kit.gui_gatekeeper_status import GuiGatekeeperStatus
from agentic_project_kit.gui_viewmodel import (
    build_basic_cockpit_view_model,
    build_gui_controller_view_model,
)


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


def build_basic_no_window_presenter_result(
    *,
    gatekeeper_status: GuiGatekeeperStatus | None = None,
    communication_mode: str = "file_transfer",
) -> GuiPresenterResult:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=gatekeeper_status,
        communication_mode=communication_mode,
    )
    rendered = render_basic_cockpit_view_model(view_model)
    return GuiPresenterResult(
        ok=True,
        action_count=view_model.button_count,
        rendered=rendered,
        message="Basic cockpit no-window presenter passed.",
    )
