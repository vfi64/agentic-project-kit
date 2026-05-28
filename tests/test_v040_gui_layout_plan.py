from agentic_project_kit.gui_layout_plan import build_layout_plan, render_layout_plan
from agentic_project_kit.gui_button_catalog import all_gui_buttons, toolbar_gui_buttons


def test_layout_plan_contains_windows_style_shell_regions():
    plan = build_layout_plan()
    kinds = {node.kind for node in plan.nodes}
    assert {
        "window",
        "menu_bar",
        "toolbar",
        "main_area",
        "action_panel",
        "details_panel",
        "output_panel",
        "summary_bar",
    } <= kinds
    assert plan.geometry == "1000x650"


def test_layout_plan_preserves_buttons_tooltips_and_disabled_destructive_action():
    plan = build_layout_plan()
    toolbar_buttons = plan.nodes_by_kind("toolbar_button")
    action_buttons = plan.nodes_by_kind("action_button")
    assert len(toolbar_buttons) == len(toolbar_gui_buttons())
    assert len(action_buttons) == len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])
    assert all(button.tooltip for button in toolbar_buttons)
    assert all(button.tooltip for button in action_buttons)
    assert all(button.category for button in action_buttons)
    assert all(button.implementation_state for button in action_buttons)
    assert any(
        button.command_id == "release-publish" and not button.enabled for button in action_buttons
    )


def test_render_layout_plan_is_deterministic():
    output = render_layout_plan(build_layout_plan())
    assert "GUI LAYOUT PLAN" in output
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
