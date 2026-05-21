from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_presenter import build_no_window_presenter_result


@dataclass(frozen=True)
class DummyAction:
    name: str
    safety_class: str
    description: str = ""


def test_no_window_presenter_renders_controller_view_model():
    result = build_no_window_presenter_result((
        DummyAction("status", "read_only", "Show status"),
        DummyAction("publish", "destructive", "Publish release"),
    ))
    assert result.ok is True
    assert result.action_count == 2
    assert result.message == "GUI no-window presenter passed."
    assert "agentic-project-kit Cockpit" in result.rendered
    assert "status=dry-run-ready" in result.rendered
    assert "01. status [read_only; enabled; no-confirm] - Show status" in result.rendered
    assert "02. publish [destructive; disabled; confirm] - Publish release" in result.rendered


def test_no_window_presenter_can_explicitly_enable_destructive_actions():
    result = build_no_window_presenter_result(
        (DummyAction("publish", "destructive", "Publish release"),),
        destructive_actions_enabled=True,
    )
    assert "01. publish [destructive; enabled; confirm] - Publish release" in result.rendered
