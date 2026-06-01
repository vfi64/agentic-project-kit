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
    assert result.report.splitlines() == [
        "PR green",
        "FINAL_SIGNAL=d",
        "FINAL_NEXT=Run transfer pr-wait-ci or pr-merge-safe with the verified head SHA.",
    ]


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

def test_pr_status_transfer_rejects_short_expected_head_sha(monkeypatch):
    calls = []

    def fake_fetch(pr):
        calls.append(pr)
        return {"headRefOid": "0" * 40}

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        fake_fetch,
    )

    result = pr_status_transfer(123, expected_head_sha="abc123")

    assert calls == []
    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert result.decision == "red"
    assert result.head_ref_oid == ""
    assert "full 40-character head SHA" in result.report


def test_pr_status_transfer_expected_head_sha_matches(monkeypatch):
    class Decision:
        decision = "green"

    head = "a" * 40

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        lambda pr: {"number": pr, "headRefOid": head},
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.classify_pr_status",
        lambda payload, pr: Decision(),
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.render_decision",
        lambda decision: "PR green",
    )

    result = pr_status_transfer(123, expected_head_sha=head)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.head_ref_oid == head


def test_transfer_pr_status_cli_rejects_short_expected_head_sha(monkeypatch):
    calls = []

    def fake_fetch(pr):
        calls.append(pr)
        return {"headRefOid": "0" * 40}

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        fake_fetch,
    )

    result = CliRunner().invoke(
        app,
        ["transfer", "pr-status", "123", "--expected-head-sha", "abc123"],
    )

    assert calls == []
    assert result.exit_code == 2
    assert "full 40-character head SHA" in result.stdout

def test_pr_status_transfer_rejects_short_sha_with_final_signal():
    result = pr_status_transfer(123, expected_head_sha="abc123")

    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert result.report.splitlines()[-2] == "FINAL_SIGNAL=f"
    assert result.report.splitlines()[-1] == "FINAL_NEXT=Re-run with the full PR head SHA."

def test_pr_status_transfer_returns_structured_failure_when_pr_lookup_fails(monkeypatch):
    def boom(_pr):
        raise RuntimeError("GraphQL: Could not resolve to a PullRequest with the number of 1040.")

    monkeypatch.setattr(
        "agentic_project_kit.transfer_pr_actions.fetch_pr_payload",
        boom,
    )

    result = pr_status_transfer(1040)

    assert result.result_status == "FAIL"
    assert result.returncode == 1
    assert result.decision == "red"
    assert "PR_STATUS_LOOKUP_FAILED" in result.report
    assert "Could not resolve to a PullRequest" in result.report
    assert "FINAL_SIGNAL=f" in result.report
    assert "Inspect the PR number or discover the existing PR" in result.report

