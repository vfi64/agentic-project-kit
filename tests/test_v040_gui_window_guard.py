from pathlib import Path

from agentic_project_kit.gui_dry_run import render_result, run_gui_dry_run
from agentic_project_kit.gui_window_guard import WindowGuardResult, render_window_guard_result


def test_window_guard_renderer_reports_native_tkinter_state_without_inner_result_marker():
    text = render_window_guard_result(WindowGuardResult(False, True, False, "native _tkinter import failed"))
    assert "GUI WINDOW GUARD" in text
    assert "window_launch_ready=false" in text
    assert "tkinter_importable=true" in text
    assert "native_tkinter_importable=false" in text
    assert "window_guard_status=BLOCKED" in text
    assert "### RESULT: FAIL ###" not in text
    assert "### RESULT: PASS ###" not in text


def test_window_guard_renderer_reports_ready_without_inner_result_marker():
    text = render_window_guard_result(WindowGuardResult(True, True, True, "window launch guard passed"))
    assert "window_launch_ready=true" in text
    assert "window_guard_status=READY" in text
    assert "### RESULT: FAIL ###" not in text
    assert "### RESULT: PASS ###" not in text


def test_gui_dry_run_exposes_window_guard_without_opening_window():
    output = render_result(run_gui_dry_run(Path.cwd()))
    assert "window_guard_begin" in output
    assert "GUI WINDOW GUARD" in output
    assert "native_tkinter_importable=" in output
    assert "window_guard_status=" in output
    assert "window_guard_end" in output
    assert "real_window_opened=false" in output
    assert "real_window_opened=true" not in output


def test_gui_dry_run_does_not_embed_inner_result_markers_for_expected_blocked_guard():
    output = render_result(run_gui_dry_run(Path.cwd()))
    guard_block = output.split("window_guard_begin", 1)[1].split("window_guard_end", 1)[0]
    assert "GUI WINDOW GUARD" in guard_block
    assert "window_guard_status=" in guard_block
    assert "### RESULT: FAIL ###" not in guard_block
    assert "### RESULT: PASS ###" not in guard_block
