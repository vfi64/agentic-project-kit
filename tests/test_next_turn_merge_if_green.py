from __future__ import annotations

from agentic_project_kit.next_turn_merge_if_green import decide_merge, render_result
from agentic_project_kit.next_turn_pr_status import classify_pr_status


def status(payload: dict[str, object]):
    return classify_pr_status(payload, pr="1")


def test_decide_merge_accepts_green_open_pr() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "OPEN",
                "mergeStateStatus": "CLEAN",
                "headRefOid": "abc",
                "statusCheckRollup": [
                    {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
                ],
            }
        )
    )
    assert decision == "merge"
    assert reason == "PR is green"


def test_decide_merge_refuses_red_pr() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "OPEN",
                "mergeStateStatus": "UNSTABLE",
                "headRefOid": "abc",
                "statusCheckRollup": [
                    {"name": "test", "status": "COMPLETED", "conclusion": "FAILURE"},
                ],
            }
        )
    )
    assert decision == "refuse"
    assert "not green" in reason


def test_decide_merge_refuses_pending_pr() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "OPEN",
                "mergeStateStatus": "UNKNOWN",
                "headRefOid": "abc",
                "statusCheckRollup": [
                    {"name": "test", "status": "IN_PROGRESS", "conclusion": None},
                ],
            }
        )
    )
    assert decision == "refuse"
    assert "pending" in reason


def test_decide_merge_refuses_not_open_pr() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "MERGED",
                "mergeStateStatus": "UNKNOWN",
                "headRefOid": "abc",
                "statusCheckRollup": [],
            }
        )
    )
    assert decision == "refuse"
    assert "not open" in reason


def test_render_result_contains_contract_lines() -> None:
    st = status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        }
    )

    class Result:
        pr = "1"
        decision = "merge"
        reason = "PR is green"
        status_decision = st
        merged = False

    rendered = render_result(Result())  # type: ignore[arg-type]
    assert "NEXT_TURN_MERGE_IF_GREEN" in rendered
    assert "decision=merge" in rendered
    assert "### RESULT: PASS ###" in rendered
