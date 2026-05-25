from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.pass_already_done import CompletionOutcome
from agentic_project_kit.pass_already_done import classify_completion
from agentic_project_kit.pass_already_done import render_classification


def test_zero_exit_is_pass() -> None:
    result = classify_completion(exit_code=0, output="ok")
    assert result.outcome == CompletionOutcome.PASS
    assert result.success


def test_nothing_to_commit_requires_verified_target_state() -> None:
    output = "On branch main\nnothing to commit, working tree clean\n"
    without_verification = classify_completion(exit_code=1, output=output)
    with_verification = classify_completion(exit_code=1, output=output, target_verified=True)
    assert without_verification.outcome == CompletionOutcome.FAIL
    assert with_verification.outcome == CompletionOutcome.PASS_ALREADY_DONE
    assert with_verification.success


def test_everything_up_to_date_can_be_pass_already_done() -> None:
    result = classify_completion(exit_code=1, output="Everything up-to-date", target_verified=True)
    assert result.outcome == CompletionOutcome.PASS_ALREADY_DONE


def test_pull_request_already_exists_can_be_pass_already_done() -> None:
    result = classify_completion(exit_code=1, output="a pull request for branch feature/x already exists", target_verified=True)
    assert result.outcome == CompletionOutcome.PASS_ALREADY_DONE


def test_traceback_is_fail_even_when_target_verified() -> None:
    result = classify_completion(exit_code=1, output="Traceback: boom", target_verified=True)
    assert result.outcome == CompletionOutcome.FAIL


def test_render_classification_reports_pass_marker() -> None:
    result = classify_completion(exit_code=1, output="nothing to commit", target_verified=True)
    text = render_classification(result)
    assert "outcome: PASS_ALREADY_DONE" in text
    assert "### RESULT: PASS ###" in text


def test_cli_classify_pass_already_done(tmp_path: Path) -> None:
    output_file = tmp_path / "out.txt"
    output_file.write_text("nothing to commit, working tree clean\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["pass-already-done", "classify", str(output_file), "--exit-code", "1", "--target-verified"],
    )
    assert result.exit_code == 0, result.output
    assert "outcome: PASS_ALREADY_DONE" in result.output


def test_cli_classify_fail_without_verified_target(tmp_path: Path) -> None:
    output_file = tmp_path / "out.txt"
    output_file.write_text("nothing to commit, working tree clean\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["pass-already-done", "classify", str(output_file), "--exit-code", "1"])
    assert result.exit_code == 1
    assert "outcome: FAIL" in result.output
