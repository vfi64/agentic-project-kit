from __future__ import annotations

from agentic_project_kit.next_turn_evidence import (
    EvidenceFinalizeResult,
    EvidencePublishPlan,
    render_finalize_result,
    render_plan,
)
from agentic_project_kit.next_turn_result import build_result, render_summary
from agentic_project_kit.next_turn_runner import NextTurnRunResult, render_result


def test_canonical_summary_contains_the_only_final_result_marker() -> None:
    result = build_result(
        run_id="summary",
        work_result="PASS",
        evidence_result="PASS",
        remote_evidence="PARTIAL",
        terminal_log="/tmp/summary.log",
        remote_terminal_log="docs/reports/terminal/summary.log",
        command_report="docs/reports/command_runs/summary.json",
    )
    rendered = render_summary(result)
    assert rendered.count("SUMMARY") == 1
    assert rendered.count("### RESULT:") == 1
    assert "### RESULT: PASS ###" in rendered


def test_runner_subresult_does_not_emit_final_result_marker() -> None:
    result = NextTurnRunResult(
        command_id="runner",
        outcome="PASS_EXECUTED",
        exit_code=0,
        script_path=".agentic/commands/inbox/next-turn.py",
        yaml_path=".agentic/commands/inbox/next-turn.yaml",
        terminal_log="docs/reports/terminal/next-turn-latest.log",
        command_report="docs/reports/command_runs/next-turn-latest.json",
        timestamp_utc="2026-01-01T00:00:00+00:00",
    )
    rendered = render_result(result)
    assert "NEXT_TURN_RUNNER" in rendered
    assert "subresult=PASS" in rendered
    assert "### RESULT:" not in rendered
    assert "SUMMARY" not in rendered


def test_evidence_plan_and_finalize_are_subresults_not_final_summaries() -> None:
    plan = EvidencePublishPlan(
        run_id="evidence",
        local_terminal_log="/tmp/evidence.log",
        work_result="PASS",
        files_to_stage=("docs/reports/terminal/evidence.log",),
        commit_message="Record evidence",
        branch="feature/evidence",
        push_command="git push -u origin feature/evidence",
    )
    finalize = EvidenceFinalizeResult(
        plan=plan,
        committed=True,
        pushed=False,
        already_clean=False,
        commit_sha="abc123",
        message="PASS: evidence committed",
    )
    rendered = render_plan(plan) + "\n" + render_finalize_result(finalize)
    assert "subresult=PASS" in rendered
    assert "### RESULT:" not in rendered
    assert "SUMMARY" not in rendered
