from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli_commands.transfer import transfer_app


def test_transfer_continue_refreshes_missing_llm_context_before_running(monkeypatch) -> None:
    calls: list[str] = []

    def fake_eval(root, *, max_age_minutes):
        calls.append("eval")
        if calls.count("eval") == 1:
            return {
                "result_status": "BLOCKED",
                "final_signal": "f",
                "next_action": "missing context",
                "max_age_minutes": max_age_minutes,
                "valid_contexts": [],
                "blockers": ["outbox_llm_execution_context_missing"],
                "checked": {},
            }
        return {
            "result_status": "PASS",
            "final_signal": "d",
            "next_action": "Fresh LLM context gate passed; planning may continue.",
            "max_age_minutes": max_age_minutes,
            "valid_contexts": ["outbox"],
            "blockers": [],
            "checked": {},
        }

    def fake_refresh(root):
        calls.append("refresh")
        return {"result_status": "PASS"}

    def fake_continue(root, branch):
        calls.append("continue")
        return {"returncode": 0, "result_status": "PASS", "next_action": "done"}

    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer._evaluate_llm_context_freshness", fake_eval)
    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer.refresh_llm_context_carriers", fake_refresh)
    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer.run_transfer_continue", fake_continue)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.render_transfer_continue_summary",
        lambda result: "CONTINUE SUMMARY",
    )

    result = CliRunner().invoke(transfer_app, ["continue", "main", "--no-json"])

    assert result.exit_code == 0
    assert calls == ["eval", "refresh", "eval", "continue"]
    assert "CONTINUE SUMMARY" in result.stdout


def test_transfer_continue_blocks_when_context_refresh_does_not_fix_gate(monkeypatch) -> None:
    def fake_eval(root, *, max_age_minutes):
        return {
            "result_status": "BLOCKED",
            "final_signal": "f",
            "next_action": "still missing",
            "max_age_minutes": max_age_minutes,
            "valid_contexts": [],
            "blockers": ["outbox_llm_execution_context_missing"],
            "checked": {},
        }

    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer._evaluate_llm_context_freshness", fake_eval)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.refresh_llm_context_carriers",
        lambda root: {"result_status": "PASS"},
    )

    result = CliRunner().invoke(transfer_app, ["continue", "main", "--no-json"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout
    assert "BLOCKERS" in result.stdout


def test_show_last_report_is_compact_by_default(monkeypatch) -> None:
    report = {
        "label": "demo",
        "returncode": 0,
        "final_signal": "d",
        "chat_reply": "g",
        "next_action": "next",
        "llm_execution_context": {"large": "context"},
    }
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.read_latest_transfer_report",
        lambda root: json.dumps(report),
    )

    result = CliRunner().invoke(transfer_app, ["show-last-report"])

    assert result.exit_code == 0
    assert "TRANSFER_SHOW_LAST_REPORT" in result.stdout
    assert "llm_execution_context" not in result.stdout
    assert "FULL_REPORT" in result.stdout


def test_show_last_report_json_keeps_full_report(monkeypatch) -> None:
    text = '{"llm_execution_context": {"large": "context"}}'
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.read_latest_transfer_report",
        lambda root: text,
    )

    result = CliRunner().invoke(transfer_app, ["show-last-report", "--json"])

    assert result.exit_code == 0
    assert "llm_execution_context" in result.stdout
