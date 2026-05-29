from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_inspector import EvidenceVerdict
from agentic_project_kit.evidence_inspector import LogClassificationState
from agentic_project_kit.evidence_inspector import classify_log
from agentic_project_kit.evidence_inspector import render_log_classification
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.evidence_inspector import render_evidence_inspection


def test_missing_evidence_requires_upload_first(tmp_path: Path) -> None:
    result = inspect_evidence(tmp_path / "missing.log", root=tmp_path)
    assert result.verdict == EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST
    assert not result.success


def test_pass_evidence_allows_continue(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.PASS_CONTINUE
    assert result.success


def test_fail_evidence_requires_diagnosis(tmp_path: Path) -> None:
    log = tmp_path / "fail.log"
    log.write_text("### RESULT: FAIL ###\n", encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.FAIL_DIAGNOSE
    assert not result.success


def test_hidden_fail_before_final_pass_is_ambiguous(tmp_path: Path) -> None:
    log = tmp_path / "mixed.log"
    log.write_text("### RESULT: FAIL ###\nthen later\n### RESULT: PASS ###\n", encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    assert result.hidden_fail_before_final_pass


def test_unstructured_evidence_is_ambiguous(tmp_path: Path) -> None:
    log = tmp_path / "plain.log"
    log.write_text("plain output\n", encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED


def test_latest_pointer_is_used(tmp_path: Path) -> None:
    pointer = tmp_path / "docs" / "reports" / "terminal" / "LATEST_TERMINAL_LOG.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    log = tmp_path / "docs" / "reports" / "terminal" / "latest.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    pointer.write_text("docs/reports/terminal/latest.log\n", encoding="utf-8")
    result = inspect_evidence(root=tmp_path)
    assert result.path == log
    assert result.success


def test_render_evidence_inspection_contains_verdict(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    text = render_evidence_inspection(inspect_evidence(log, root=tmp_path))
    assert "EVIDENCE_INSPECTION" in text
    assert "verdict: PASS_CONTINUE" in text
    assert "### RESULT: PASS ###" in text


def test_evidence_inspect_cli_passes_for_pass_log(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "inspect", str(log), "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "verdict: PASS_CONTINUE" in result.output


def test_evidence_inspect_cli_fails_for_fail_log(tmp_path: Path) -> None:
    log = tmp_path / "fail.log"
    log.write_text("### RESULT: FAIL ###\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "inspect", str(log), "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert "verdict: FAIL_DIAGNOSE" in result.output



def test_classify_log_allows_clean_pass(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.READY_TO_CONTINUE
    assert result.decision == "continue"
    assert result.success


def test_classify_log_blocks_hidden_fail_before_pass(tmp_path: Path) -> None:
    log = tmp_path / "mixed.log"
    log.write_text("### RESULT: FAIL ###\nthen later\n### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.BLOCKED_BY_HIDDEN_FAIL
    assert result.decision == "fail"
    assert result.hidden_fail


def test_classify_log_blocks_pending(tmp_path: Path) -> None:
    log = tmp_path / "pending.log"
    log.write_text("### RESULT: PENDING ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.BLOCKED_BY_PENDING
    assert result.decision == "pending"


def test_classify_log_detects_missing_summary_when_required(tmp_path: Path) -> None:
    log = tmp_path / "missing-summary.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.BLOCKED_BY_MISSING_SUMMARY
    assert "missing structured summary block" in result.reasons


def test_classify_log_detects_invalid_summary(tmp_path: Path) -> None:
    log = tmp_path / "bad-summary.log"
    log.write_text(
        "================================================================\n"
        "SUMMARY COMM-TEST | 2026-05-29 12:00:00 +0000\n"
        "RESULT\n"
        "  OVERALL: PASS\n"
        "### RESULT: PASS ###\n"
        "================================================================\n",
        encoding="utf-8",
    )
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.BLOCKED_BY_BAD_SUMMARY
    assert not result.summary_valid


def test_classify_log_detects_test_failure(tmp_path: Path) -> None:
    log = tmp_path / "test-failure.log"
    log.write_text("FAILED tests/test_example.py::test_demo\n### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.BLOCKED_BY_TEST_FAILURE


def test_classify_log_detects_traceback(tmp_path: Path) -> None:
    log = tmp_path / "traceback.log"
    log.write_text("Traceback (most recent call last):\nValueError: boom\n### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path)
    assert result.state == LogClassificationState.BLOCKED_BY_TRACEBACK


def test_render_log_classification_is_machine_readable(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    text = render_log_classification(classify_log(log, root=tmp_path))
    assert "LOG_CLASSIFICATION" in text
    assert "state=READY_TO_CONTINUE" in text
    assert "decision=continue" in text


def test_evidence_classify_log_cli_passes_for_clean_pass(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "classify-log", str(log), "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "LOG_CLASSIFICATION" in result.output
    assert "state=READY_TO_CONTINUE" in result.output


def test_evidence_classify_log_cli_fails_for_hidden_fail(tmp_path: Path) -> None:
    log = tmp_path / "mixed.log"
    log.write_text("### RESULT: FAIL ###\nthen later\n### RESULT: PASS ###\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "classify-log", str(log), "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert "state=BLOCKED_BY_HIDDEN_FAIL" in result.output
