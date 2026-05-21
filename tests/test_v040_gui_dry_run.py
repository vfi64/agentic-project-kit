from pathlib import Path
import subprocess
import sys

from agentic_project_kit.gui_dry_run import render_result, run_gui_dry_run


def test_gui_dry_run_module_reports_required_checks():
    result = run_gui_dry_run(Path.cwd())
    output = render_result(result)
    assert "GUI DRY RUN" in output
    assert "no window is opened" in output
    assert "tkinter_available=" in output
    assert "window_launch_ready=" in output
    assert "tkinter_note=nonblocking for --dry-run" in output
    assert "action_registry_available=true" in output
    assert "action_specs_available=true" in output
    assert "mode_guard_available=true" in output
    assert "shell_adapters_absent=true" in output


def test_gui_dry_run_module_cli_has_deterministic_output():
    result = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.gui_dry_run", "--dry-run"],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "GUI DRY RUN" in result.stdout
    assert "### RESULT:" in result.stdout
    assert "Traceback" not in result.stdout


def test_ns_gui_dry_run_route_is_python_backed():
    text = Path("ns").read_text(encoding="utf-8")
    assert 'if [ "${1:-}" = "gui" ]' in text
    assert "agentic_project_kit.gui_dry_run" in text
    assert "tools/ns_gui" not in text


def test_ns_gui_dry_run_executes_without_shell_adapter():
    result = subprocess.run(
        ["./ns", "gui", "--dry-run"],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "GUI DRY RUN" in result.stdout
    assert "no window is opened" in result.stdout
    assert "tools/ns_gui" not in result.stdout



def test_gui_dry_run_mode_guard_detection_uses_existing_ns_routes():
    module = Path("src/agentic_project_kit/gui_dry_run.py").read_text(encoding="utf-8")
    assert "agentic_project_kit.mode_guard" not in module
    assert "\"mode-check\" in ns_text" in module
    assert "\"mode-write\" in ns_text" in module





def test_gui_dry_run_does_not_require_tkinter_for_no_window_contract():
    module = Path("src/agentic_project_kit/gui_dry_run.py").read_text(encoding="utf-8")
    start = module.index("    ok = all((")
    end = module.index("    message =", start)
    ok_block = module[start:end]
    assert "tkinter_available" not in ok_block
    assert "action_registry_available" in ok_block
    assert "action_specs_available" in ok_block
    assert "mode_guard_available" in ok_block
    assert "shell_adapters_absent" in ok_block
    assert "tkinter_note=nonblocking for --dry-run" in module
    assert "window_launch_ready=" in module
