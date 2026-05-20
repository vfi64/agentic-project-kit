from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app

runner = CliRunner()


def test_evidence_guard_cli_accepts_clean_pass(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("ok\n### RESULT: PASS ###\n", encoding="utf-8")
    result = runner.invoke(app, ["evidence", "guard", str(log)])
    assert result.exit_code == 0
    assert "PASS:" in result.output
    assert "final_result=PASS" in result.output


def test_evidence_guard_cli_rejects_false_pass(tmp_path: Path) -> None:
    log = tmp_path / "false-pass.log"
    log.write_text("FAIL: targeted tests failed\n### RESULT: PASS ###\n", encoding="utf-8")
    result = runner.invoke(app, ["evidence", "guard", str(log)])
    assert result.exit_code == 1
    assert "FAIL:" in result.output
    assert "final PASS conflicts" in result.output
