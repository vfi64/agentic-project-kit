from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentic_project_kit.gui_dry_run import render_result, run_gui_dry_run


def test_gui_dry_run_module_reports_required_checks() -> None:
    result = run_gui_dry_run(Path.cwd())
    output = render_result(result)
    assert "GUI DRY RUN" in output
    assert "no window is opened" in output
    assert "tkinter_available=" in output
    assert "window_launch_ready=" in output
    assert "tkinter_note=nonblocking for --dry-run" in output
    assert "action_registry_available=true" in output
    assert "action_specs_available=true" in output
    assert "presenter_available=true" in output
    assert "presenter_action_count=" in output
    assert "presenter_preview_begin" in output
    assert "presenter_preview_end" in output
    assert "real_window_opened=false" in output


def test_legacy_ns_gui_dry_run_route_is_removed() -> None:
    assert not Path("ns").exists()


def test_gui_dry_run_executes_without_shell_adapter() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.gui_dry_run"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode in {0, 1}
    output = result.stdout + result.stderr
    assert "GUI DRY RUN" in output
    assert "ns_gui_dry_run" not in output
    assert ".sh" not in output
