from agentic_project_kit.gui_layout_plan import build_layout_plan
from agentic_project_kit.gui_tkinter_renderer import (
    render_layout_to_tkinter,
    render_tkinter_result_summary,
)
from agentic_project_kit.gui_button_catalog import all_gui_buttons, toolbar_gui_buttons
from agentic_project_kit.gui_tkinter_shell import WORK_ORDER_STRIP_COMMAND_IDS


class FakeRoot:
    def __init__(self):
        self.title_value = None
        self.geometry_value = None

    def title(self, value):
        self.title_value = value

    def geometry(self, value):
        self.geometry_value = value


def test_render_layout_to_tkinter_configures_root_without_real_window():
    root = FakeRoot()
    plan = build_layout_plan()
    result = render_layout_to_tkinter(root, plan)
    assert root.title_value == "agentic-project-kit Cockpit"
    assert root.geometry_value == "1000x650"
    assert len(result.widgets) == plan.node_count


def test_render_layout_to_tkinter_preserves_menu_toolbar_actions_and_tooltips():
    result = render_layout_to_tkinter(FakeRoot(), build_layout_plan())
    assert len(result.widgets_by_kind("menu")) == 5
    assert len(result.widgets_by_kind("toolbar_button")) == len(toolbar_gui_buttons())
    assert len(result.widgets_by_kind("action_button")) == len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])
    assert all(widget.tooltip for widget in result.widgets_by_kind("toolbar_button"))
    assert all(widget.tooltip for widget in result.widgets_by_kind("action_button"))
    assert all(widget.category for widget in result.widgets_by_kind("action_button"))
    assert all(widget.implementation_state for widget in result.widgets_by_kind("action_button"))
    assert result.destructive_enabled is False


def test_render_tkinter_result_summary_is_deterministic():
    output = render_tkinter_result_summary(
        render_layout_to_tkinter(FakeRoot(), build_layout_plan())
    )
    assert "TKINTER RENDER RESULT" in output
    assert "menu_count=5" in output
    assert f"toolbar_button_count={len(toolbar_gui_buttons())}" in output
    assert f"action_button_count={len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])}" in output
    assert (
        "action_categories=Diagnostics,Evidence,Git Workflow,Quality Gates,Release,Session,Workflow Automation"
        in output
    )
    assert "disabled_commands=" in output
    assert "release-publish" in output
    assert "merge-if-green" in output
    assert "destructive_enabled=false" in output
