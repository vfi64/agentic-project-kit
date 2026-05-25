from pathlib import Path

from agentic_project_kit.evidence_inspector import EvidenceVerdict
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.run_summary_renderer import SummaryPayload
from agentic_project_kit.run_summary_renderer import render_summary


def _summary(**overrides: str) -> str:
    data = dict(
        comm_id="COMM-TEST",
        slice="summary-parser-test",
        scope="test",
        work="PASS",
        evidence="PASS",
        overall="PASS",
        remote_evidence="NOT_REQUIRED",
        terminal_log="docs/reports/terminal/test.log",
        chat_reply="d",
    )
    data.update(overrides)
    return render_summary(SummaryPayload(**data))


def test_structured_pass_summary_allows_continue(tmp_path: Path) -> None:
    log = tmp_path / "summary-pass.log"
    log.write_text(_summary(), encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.PASS_CONTINUE
    assert result.structured_summary.found
    assert result.structured_summary.valid
    assert result.structured_summary.overall == "PASS"


def test_structured_fail_summary_requires_diagnosis(tmp_path: Path) -> None:
    log = tmp_path / "summary-fail.log"
    log.write_text(_summary(work="FAIL", evidence="FAIL", overall="FAIL", chat_reply="f"), encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.FAIL_DIAGNOSE
    assert result.structured_summary.valid
    assert result.structured_summary.overall == "FAIL"


def test_invalid_structured_pass_is_ambiguous(tmp_path: Path) -> None:
    text = _summary().replace("  CHAT_REPLY: d", "  CHAT_REPLY: f")
    log = tmp_path / "summary-invalid.log"
    log.write_text(text, encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.verdict == EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    assert not result.structured_summary.valid
    assert "invalid pass: chat_reply must be d" in result.structured_summary.findings


def test_structured_summary_overrides_hidden_expected_fail_marker(tmp_path: Path) -> None:
    log = tmp_path / "summary-with-expected-fail.log"
    log.write_text("expected negative smoke\n### RESULT: FAIL ###\n" + _summary(), encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path)
    assert result.hidden_fail_before_final_pass
    assert result.structured_summary.valid
    assert result.verdict == EvidenceVerdict.PASS_CONTINUE
