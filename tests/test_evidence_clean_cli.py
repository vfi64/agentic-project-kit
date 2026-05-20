from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_clean import CleanCheckResult

runner = CliRunner()


def test_evidence_clean_check_cli_passes(monkeypatch) -> None:
    def fake_check(root, expected_log):
        return CleanCheckResult(True, str(expected_log), (), ("?? " + str(expected_log),))

    monkeypatch.setattr("agentic_project_kit.cli_commands.evidence.check_clean_except_expected_log", fake_check)
    result = runner.invoke(app, ["evidence", "clean-check", "docs/reports/terminal/x.log"])
    assert result.exit_code == 0
    assert "PASS: worktree clean except expected log" in result.output


def test_evidence_clean_check_cli_fails(monkeypatch) -> None:
    def fake_check(root, expected_log):
        return CleanCheckResult(False, str(expected_log), (" M README.md",), ("?? " + str(expected_log), " M README.md"))

    monkeypatch.setattr("agentic_project_kit.cli_commands.evidence.check_clean_except_expected_log", fake_check)
    result = runner.invoke(app, ["evidence", "clean-check", "docs/reports/terminal/x.log"])
    assert result.exit_code == 1
    assert "FAIL: worktree dirty beyond expected log" in result.output
    assert " M README.md" in result.output
