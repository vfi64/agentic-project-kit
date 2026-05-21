from agentic_project_kit.gui_layout_plan import build_layout_plan
from agentic_project_kit.gui_tkinter_renderer import render_layout_to_tkinter, render_tkinter_result_summary

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
    result = render_layout_to_tkinter(root, build_layout_plan())
    assert root.title_value == "agentic-project-kit Cockpit"
    assert root.geometry_value == "1000x650"
    assert len(result.widgets) == 32

def test_render_layout_to_tkinter_preserves_menu_toolbar_actions_and_tooltips():
    result = render_layout_to_tkinter(FakeRoot(), build_layout_plan())
    assert len(result.widgets_by_kind("menu")) == 4
    assert len(result.widgets_by_kind("toolbar_button")) == 4
    assert len(result.widgets_by_kind("action_button")) == 6
    assert all(widget.tooltip for widget in result.widgets_by_kind("toolbar_button"))
    assert all(widget.tooltip for widget in result.widgets_by_kind("action_button"))
    assert result.destructive_enabled is False

def test_render_tkinter_result_summary_is_deterministic():
    output = render_tkinter_result_summary(render_layout_to_tkinter(FakeRoot(), build_layout_plan()))
    assert "TKINTER RENDER RESULT" in output
    assert "menu_count=4" in output
    assert "toolbar_button_count=4" in output
    assert "action_button_count=6" in output
    assert "disabled_commands=release-publish" in output
    assert "destructive_enabled=false" in output
