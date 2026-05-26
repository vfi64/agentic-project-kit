from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.pass_already_done import CompletionOutcome
from agentic_project_kit.result_report_classifier import classify_report
from agentic_project_kit.result_report_classifier import render_report_classification


def test_report_classifier_promotes_verified_noop(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("nothing to commit, working tree clean\n", encoding="utf-8")
    result = classify_report(report, raw_exit_code=1, target_verified=True)
    assert result.classification.outcome == CompletionOutcome.PASS_ALREADY_DONE
    assert result.success


def test_report_classifier_fails_unverified_noop(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("nothing to commit, working tree clean\n", encoding="utf-8")
    result = classify_report(report, raw_exit_code=1)
    assert result.classification.outcome == CompletionOutcome.FAIL
    assert not result.success


def test_render_report_classification_has_effective_success(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("Everything up-to-date\n", encoding="utf-8")
    result = classify_report(
        report,
        raw_exit_code=1,
        target_verified=True,
        target_state="remote-sync",
    )
    text = render_report_classification(result)
    assert "WORKFLOW_REPORT_CLASSIFICATION" in text
    assert "target_state: remote-sync" in text
    assert "effective_success: yes" in text
    assert "outcome: PASS_ALREADY_DONE" in text


def test_report_classifier_renders_normalized_target_state(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("Everything up-to-date\n", encoding="utf-8")
    result = classify_report(
        report,
        raw_exit_code=1,
        target_verified=True,
        target_state="remote_sync",
    )

    assert result.target_state == "remote-sync"
    assert "target_state: remote-sync" in render_report_classification(result)


def test_cli_report_classification_pass(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("Everything up-to-date\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "pass-already-done",
            "report",
            str(report),
            "--exit-code",
            "1",
            "--target-verified",
            "--target-state",
            "remote-sync",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "WORKFLOW_REPORT_CLASSIFICATION" in result.output
    assert "outcome: PASS_ALREADY_DONE" in result.output


def test_cli_report_classification_fail_without_verification(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("Everything up-to-date\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["pass-already-done", "report", str(report), "--exit-code", "1"])
    assert result.exit_code == 1
    assert "outcome: FAIL" in result.output
