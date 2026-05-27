from pathlib import Path

from agentic_project_kit.gui_button_catalog import all_gui_buttons, toolbar_gui_buttons
from agentic_project_kit.gui_dry_run import render_result, run_gui_dry_run


def test_gui_dry_run_preserves_existing_contract_and_adds_layout_renderer_output():
    output = render_result(run_gui_dry_run(Path.cwd()))
    assert "GUI DRY RUN" in output
    assert "Safety: no window is opened" in output
    assert "window_launch_ready=" in output
    assert "tkinter_note=nonblocking for --dry-run" in output
    assert "action_registry_available=true" in output
    assert "action_specs_available=true" in output
    assert "presenter_available=true" in output
    assert "mode_guard_available=true" in output
    assert "shell_adapters_absent=true" in output
    assert "layout_plan_begin" in output
    assert "GUI LAYOUT PLAN" in output
    assert "layout_plan_end" in output
    assert "tkinter_render_begin" in output
    assert "TKINTER RENDER RESULT" in output
    assert "tkinter_render_end" in output
    assert "menu_count=5" in output
    assert f"toolbar_button_count={len(toolbar_gui_buttons())}" in output
    assert f"action_button_count={len(all_gui_buttons())}" in output
    assert "disabled_commands=" in output
    assert "release-publish" in output
    assert "merge-if-green" in output
    assert "destructive_enabled=false" in output
    assert "real_window_opened=false" in output
    assert "real_window_opened=true" not in output


def test_gui_dry_run_patch_is_additive_not_replacement():
    text = Path("src/agentic_project_kit/gui_dry_run.py").read_text(encoding="utf-8")
    assert "build_no_window_presenter_result" in text
    assert "list_actions()" in text
    assert "shell_adapters_absent" in text
    assert "layout_plan_begin" in text
