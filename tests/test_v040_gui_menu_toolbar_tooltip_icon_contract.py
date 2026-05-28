from agentic_project_kit.gui_button_catalog import all_gui_buttons, toolbar_gui_buttons
from agentic_project_kit.gui_layout_plan import build_layout_plan
from agentic_project_kit.gui_tkinter_renderer import render_layout_to_tkinter
from agentic_project_kit.gui_tkinter_shell import WORK_ORDER_STRIP_COMMAND_IDS, build_tkinter_shell_spec


class DummyRoot:
    def __init__(self):
        self.title_value = ""
        self.geometry_value = ""

    def title(self, value: str) -> None:
        self.title_value = value

    def geometry(self, value: str) -> None:
        self.geometry_value = value


def test_shell_spec_has_windows_style_menu_toolbar_and_action_buttons():
    spec = build_tkinter_shell_spec()
    assert [menu.label for menu in spec.design.menu_bar] == [
        "File",
        "Communication",
        "Gates",
        "View",
        "Help",
    ]
    assert len(spec.design.toolbar) == len(toolbar_gui_buttons())
    assert len(spec.design.action_buttons) == len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])
    assert all(button.tooltip for button in spec.design.toolbar)
    assert all(button.icon_id for button in spec.design.toolbar)
    assert all(button.tooltip for button in spec.design.action_buttons)
    assert all(button.icon_id for button in spec.design.action_buttons)


def test_layout_plan_preserves_tooltips_icons_and_disabled_destructive_release_publish():
    plan = build_layout_plan()
    toolbar = plan.nodes_by_kind("toolbar_button")
    actions = plan.nodes_by_kind("action_button")
    assert toolbar
    assert actions
    assert all(node.tooltip for node in toolbar + actions)
    assert all(node.icon_id for node in toolbar + actions)
    release_nodes = [node for node in actions if node.command_id == "release-publish"]
    assert len(release_nodes) == 1
    assert release_nodes[0].enabled is False
    assert release_nodes[0].safety_class == "destructive"
    assert release_nodes[0].icon_id == "lock"


def test_tkinter_renderer_preserves_button_tooltip_and_icon_metadata():
    result = render_layout_to_tkinter(DummyRoot())
    widgets = result.widgets_by_kind("toolbar_button") + result.widgets_by_kind("action_button")
    assert widgets
    assert all(widget.tooltip for widget in widgets)
    assert all(widget.icon_id for widget in widgets)
    assert result.destructive_enabled is False
