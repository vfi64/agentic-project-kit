from __future__ import annotations

import os
import subprocess
import sys


def run_gui_dry_run() -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.gui_dry_run"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    return completed.stdout


def test_gui_dry_run_exposes_output_status_panel_sections():
    output = run_gui_dry_run()
    assert "output_status_panel_begin" in output
    assert "GUI OUTPUT STATUS PANEL" in output
    assert "latest_output_begin" in output
    assert "summary_begin" in output
    assert "output_status_panel_end" in output


def test_gui_dry_run_output_status_panel_is_before_layout_rendering():
    output = run_gui_dry_run()
    assert output.index("output_status_panel_begin") < output.index("layout_plan_begin")
