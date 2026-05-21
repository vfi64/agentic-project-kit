from __future__ import annotations

from agentic_project_kit.gui_action_renderer import render_action_row
from agentic_project_kit.gui_action_renderer import render_action_rows
from agentic_project_kit.gui_action_renderer import render_controller_view_model
from agentic_project_kit.gui_viewmodel import GuiActionViewModel
from agentic_project_kit.gui_viewmodel import GuiControllerViewModel


def test_render_action_row_marks_enabled_read_only_action():
    row = render_action_row(
        GuiActionViewModel(
            name="status",
            safety_class="read_only",
            description="Show status",
            enabled=True,
            requires_confirmation=False,
        ),
        1,
    )
    assert row == "01. status [read_only; enabled; no-confirm] - Show status"


def test_render_action_row_marks_disabled_destructive_action():
    row = render_action_row(
        GuiActionViewModel(
            name="publish",
            safety_class="destructive",
            description="Publish release",
            enabled=False,
            requires_confirmation=True,
        ),
        2,
    )
    assert row == "02. publish [destructive; disabled; confirm] - Publish release"


def test_render_action_rows_is_deterministic():
    rows = render_action_rows((
        GuiActionViewModel("a", "read_only", "", True, False),
        GuiActionViewModel("b", "bounded", "Run bounded task", True, False),
    ))
    assert rows == (
        "01. a [read_only; enabled; no-confirm] - no description",
        "02. b [bounded; enabled; no-confirm] - Run bounded task",
    )


def test_render_controller_view_model_includes_summary_and_actions():
    vm = GuiControllerViewModel(
        title="Test Cockpit",
        status="ready",
        destructive_actions_enabled=False,
        actions=(
            GuiActionViewModel("status", "read_only", "Show status", True, False),
            GuiActionViewModel("publish", "destructive", "Publish release", False, True),
        ),
    )
    text = render_controller_view_model(vm)
    assert "Test Cockpit" in text
    assert "status=ready" in text
    assert "action_count=2" in text
    assert "destructive_actions_enabled=false" in text
    assert "01. status [read_only; enabled; no-confirm] - Show status" in text
    assert "02. publish [destructive; disabled; confirm] - Publish release" in text
