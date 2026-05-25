from pathlib import Path
import sys

from agentic_project_kit.workflow_summary_runner import (
    render_workflow_summary,
    run_python_workflow,
)


def test_python_workflow_runner_writes_logs_and_structured_summary(tmp_path: Path) -> None:
    script = tmp_path / "ok_script.py"
    script.write_text("print('runner-ok')\n", encoding="utf-8")
    terminal_log = tmp_path / "terminal.log"
    command_report = tmp_path / "command.txt"
    result = run_python_workflow(
        [sys.executable, str(script)],
        name="unit-run",
        terminal_log=terminal_log,
        command_report=command_report,
    )
    assert result.exit_code == 0
    assert result.work_result == "PASS"
    assert terminal_log.read_text(encoding="utf-8").strip() == "runner-ok"
    assert "PYTHON_WORKFLOW_RUNNER" in command_report.read_text(encoding="utf-8")
    summary = render_workflow_summary(result)
    assert "SUMMARY COMM-PYTHON-WORKFLOW" in summary
    assert "  WORK: PASS" in summary
    assert "  EVIDENCE: PASS" in summary
    assert "  OVERALL: PASS" in summary
    assert "  CHAT_REPLY: d" in summary
    assert "### RESULT: PASS ###" in summary


def test_python_workflow_runner_failure_uses_summary_renderer(tmp_path: Path) -> None:
    script = tmp_path / "fail_script.py"
    script.write_text("print('runner-fail')\nraise SystemExit(7)\n", encoding="utf-8")
    terminal_log = tmp_path / "terminal.log"
    command_report = tmp_path / "command.txt"
    result = run_python_workflow(
        [sys.executable, str(script)],
        name="unit-fail",
        terminal_log=terminal_log,
        command_report=command_report,
    )
    assert result.exit_code == 7
    assert result.work_result == "FAIL"
    summary = render_workflow_summary(result)
    assert "  WORK: FAIL" in summary
    assert "  OVERALL: FAIL" in summary
    assert "  CHAT_REPLY: f" in summary
    assert "### RESULT: FAIL ###" in summary
