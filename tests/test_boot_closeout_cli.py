from typer.testing import CliRunner

from agentic_project_kit.cli import app


def test_boot_closeout_cli_reports_pass() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["boot", "closeout"])
    assert result.exit_code == 0, result.output
    assert "CHAT_SWITCH_CLOSEOUT: PASS" in result.output
