from agentic_project_kit.gui_layout_plan import build_layout_plan, render_layout_plan

def test_layout_plan_contains_windows_style_shell_regions():
    plan = build_layout_plan()
    kinds = {node.kind for node in plan.nodes}
    assert {"window", "menu_bar", "toolbar", "main_area", "action_panel", "details_panel", "output_panel", "summary_bar"} <= kinds
    assert plan.geometry == "1000x650"

def test_layout_plan_preserves_buttons_tooltips_and_disabled_destructive_action():
    plan = build_layout_plan()
    toolbar_buttons = plan.nodes_by_kind("toolbar_button")
    action_buttons = plan.nodes_by_kind("action_button")
    assert len(toolbar_buttons) >= 4
    assert len(action_buttons) >= 6
    assert all(button.tooltip for button in toolbar_buttons)
    assert all(button.tooltip for button in action_buttons)
    assert any(button.command_id == "release-publish" and not button.enabled for button in action_buttons)

def test_render_layout_plan_is_deterministic():
    output = render_layout_plan(build_layout_plan())
    assert "GUI LAYOUT PLAN" in output
    assert "menu_count=4" in output
    assert "toolbar_button_count=4" in output
    assert "action_button_count=6" in output
    assert "disabled_commands=release-publish" in output
