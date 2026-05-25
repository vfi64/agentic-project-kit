from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_inspector import EvidenceVerdict
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
