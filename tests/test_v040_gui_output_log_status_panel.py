from agentic_project_kit.gui_output_status_panel import build_output_status_panel, render_output_status_panel


def test_output_status_panel_preserves_log_paths_and_evidence_state():
    panel = build_output_status_panel(
        branch="main",
        dirty=False,
        latest_output="doctor passed",
        terminal_log="docs/reports/terminal/example.log",
        terminal_log_remote="docs/reports/terminal/example.log",
        terminal_log_local="/tmp/example.log",
        evidence_state="remote_evidence_pass",
        summary="OVERALL PASS",
    )
    assert panel.status == "clean"
    assert panel.branch == "main"
    assert panel.terminal_log_remote == "docs/reports/terminal/example.log"
    assert panel.terminal_log_local == "/tmp/example.log"
    assert panel.evidence_state == "remote_evidence_pass"


def test_output_status_panel_rendering_has_stable_sections():
    panel = build_output_status_panel(branch="feature/x", dirty=True, latest_output="failed step", summary="summary text")
    rendered = render_output_status_panel(panel)
    assert "GUI OUTPUT STATUS PANEL" in rendered
    assert "status=dirty" in rendered
    assert "branch=feature/x" in rendered
    assert "latest_output_begin" in rendered
    assert "failed step" in rendered
    assert "latest_output_end" in rendered
    assert "summary_begin" in rendered
    assert "summary text" in rendered
    assert "summary_end" in rendered


def test_output_status_panel_defaults_are_safe_for_initial_gui():
    panel = build_output_status_panel()
    assert panel.status == "clean"
    assert panel.terminal_log == "NONE"
    assert panel.terminal_log_remote == "NONE"
    assert panel.terminal_log_local == "NONE"
    assert panel.latest_output == "No output captured yet."
    assert panel.summary == "No summary captured yet."
