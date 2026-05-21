from pathlib import Path

from agentic_project_kit.portability_shell_gate import PortabilityShellGateReport, build_portability_shell_gate_report, render_portability_shell_gate_report

def test_portability_gate_reports_blocking_tracked_shell_files():
    report = build_portability_shell_gate_report(Path("."))
    assert "tools/ns_up_pr_completion.sh" in report.blocking_shell_files
    assert not report.ok

def test_portability_gate_render_uses_fail_for_blocking_files():
    report = PortabilityShellGateReport(shell_files=("tools/example.sh",), blocking_shell_files=("tools/example.sh",))
    rendered = render_portability_shell_gate_report(report)
    assert "blocking_shell_file_count=1" in rendered
    assert "### RESULT: FAIL ###" in rendered

def test_portability_gate_render_uses_pass_without_blockers():
    report = PortabilityShellGateReport(shell_files=(), blocking_shell_files=())
    assert "### RESULT: PASS ###" in render_portability_shell_gate_report(report)
