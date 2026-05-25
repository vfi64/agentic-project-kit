from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_inspector import EvidenceVerdict
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.run_summary_renderer import SummaryPayload
from agentic_project_kit.run_summary_renderer import render_summary


def test_marker_only_pass_fails_when_summary_required(tmp_path: Path) -> None:
    log = tmp_path / "marker-only-pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path, require_summary=True)
    assert result.verdict == EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    assert not result.success
    assert result.require_summary
    assert not result.structured_summary.found


def test_structured_pass_succeeds_when_summary_required(tmp_path: Path) -> None:
    payload = SummaryPayload(
        comm_id="COMM-TEST",
        slice="require summary test",
        scope="TEST",
        branch="main",
        origin="local",
        state_mode="local",
        mode_check="require summary",
        work="PASS",
        evidence="PASS",
        overall="PASS",
        remote_evidence="NOT_REQUIRED",
        pr="NONE",
        head_sha="abc123",
        ci="not-required",
        merge="not-required",
        terminal_log="docs/reports/terminal/test.log",
        terminal_log_remote="NONE",
        terminal_log_local="docs/reports/terminal/test.log",
        command_report="require-summary-test",
        interpretation="Require-summary evidence inspector test.",
        safe_step="continue",
        chat_reply="d",
    )
    log = tmp_path / "structured-pass.log"
    log.write_text(render_summary(payload), encoding="utf-8")
    result = inspect_evidence(log, root=tmp_path, require_summary=True)
    assert result.verdict == EvidenceVerdict.PASS_CONTINUE
    assert result.success
    assert result.structured_summary.found


def test_cli_require_summary_rejects_marker_only_pass(tmp_path: Path) -> None:
    log = tmp_path / "marker-only-pass.log"
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "inspect", str(log), "--root", str(tmp_path), "--require-summary"])
    assert result.exit_code == 1
    assert "require_summary: yes" in result.output
    assert "missing structured summary block" in result.output
