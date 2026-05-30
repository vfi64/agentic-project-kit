from __future__ import annotations

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_pr_actions import pr_status_transfer



def test_pr_status_transfer_green(monkeypatch):
    class Decision:
        decision = "green"

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        lambda pr: {"number": pr},
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.classify_pr_status",
        lambda payload, pr: Decision(),
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.render_decision",
        lambda decision: "PR green",
    )

    result = pr_status_transfer(123)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.decision == "green"
    assert result.report == "PR green"


def test_pr_status_transfer_red_fetches_logs(monkeypatch):
    class RedDecision:
        decision = "red"

    class RedWithLogs:
        decision = "red"

    calls = []

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        lambda pr: {"number": pr},
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.classify_pr_status",
        lambda payload, pr: RedDecision(),
    )

    def fake_attach(decision, max_lines):
        calls.append(max_lines)
        return RedWithLogs()

    monkeypatch.setattr("agentic_project_kit.transfer_pr_actions.attach_failed_run_logs", fake_attach)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.render_decision",
        lambda decision: "PR red",
    )

    result = pr_status_transfer(123, failed_log_lines=17)

    assert calls == [17]
    assert result.result_status == "FAIL"
    assert result.returncode == 1
    assert result.decision == "red"


def test_transfer_pr_status_cli_json(monkeypatch):
    class Decision:
        decision = "green"

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        lambda pr: {"number": pr},
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.classify_pr_status",
        lambda payload, pr: Decision(),
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.render_decision",
        lambda decision: "PR green",
    )

    result = CliRunner().invoke(app, ["transfer", "pr-status", "123", "--json"])

    assert result.exit_code == 0
    assert '"decision": "green"' in result.stdout
    assert '"result_status": "PASS"' in result.stdout
