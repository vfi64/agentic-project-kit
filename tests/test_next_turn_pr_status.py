from __future__ import annotations

from agentic_project_kit.next_turn_pr_status import classify_pr_status, render_decision


def test_classify_green_pr_status() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        },
        pr="1",
    )
    assert decision.decision == "green"
    assert decision.successful_checks == ("test",)


def test_classify_red_pr_status() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNSTABLE",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "FAILURE"},
            ],
        },
        pr="2",
    )
    assert decision.decision == "red"
    assert decision.failed_checks == ("test",)
    assert "gh run view" in decision.failed_run_log_hint


def test_classify_pending_pr_status() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNKNOWN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "test", "status": "IN_PROGRESS", "conclusion": None},
            ],
        },
        pr="3",
    )
    assert decision.decision == "pending"
    assert decision.pending_checks == ("test",)


def test_classify_not_open_pr_status() -> None:
    decision = classify_pr_status(
        {
            "state": "MERGED",
            "mergeStateStatus": "UNKNOWN",
            "headRefOid": "abc",
            "statusCheckRollup": [],
        },
        pr="4",
    )
    assert decision.decision == "not-open"


def test_render_decision_contains_required_contract_lines() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        },
        pr="5",
    )
    rendered = render_decision(decision)
    assert "NEXT_TURN_PR_STATUS" in rendered
    assert "decision=green" in rendered
    assert "### RESULT: PASS ###" in rendered
