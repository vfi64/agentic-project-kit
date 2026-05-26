from __future__ import annotations

from agentic_project_kit.next_turn_merge_if_green import (
    MergeIfGreenResult,
    decide_merge,
    main_verification_passed,
    render_result,
    verify_main_ci,
)
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


def test_decide_merge_refuses_no_checks_pr() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "OPEN",
                "mergeStateStatus": "UNKNOWN",
                "headRefOid": "abc",
                "statusCheckRollup": [],
            }
        )
    )
    assert decision == "refuse"
    assert "no-checks" in reason


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

    result = MergeIfGreenResult(
        pr="1",
        decision="merge",
        reason="PR is green",
        status_decision=st,
        merged=False,
        merge_output="",
    )

    rendered = render_result(result)
    assert "NEXT_TURN_MERGE_IF_GREEN" in rendered
    assert "decision=merge" in rendered
    assert "main_verification_required=false" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_verify_main_ci_waits_until_green_for_merge_commit() -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fetcher(commit_sha: str, branch: str) -> dict[str, object]:
        calls.append(f"{branch}:{commit_sha}")
        check = (
            {"name": "test", "status": "IN_PROGRESS", "conclusion": None}
            if len(calls) == 1
            else {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"}
        )
        return {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": commit_sha,
            "statusCheckRollup": [check],
        }

    decision = verify_main_ci(
        "abc123def456",
        branch="main",
        timeout_seconds=20,
        poll_seconds=10,
        fetcher=fetcher,
        sleep=sleeps.append,
    )

    assert decision.decision == "green"
    assert calls == ["main:abc123def456", "main:abc123def456"]
    assert sleeps == [10]


def test_verify_main_ci_attaches_failed_log_diagnostics() -> None:
    decision = verify_main_ci(
        "abc123def456",
        branch="main",
        timeout_seconds=1,
        poll_seconds=0,
        fetcher=lambda commit_sha, branch: {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": commit_sha,
            "statusCheckRollup": [
                {
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://github.com/vfi64/agentic-project-kit/actions/runs/123456/job/789",
                },
            ],
        },
        failed_log_fetcher=lambda run_id: (0, f"{run_id}\nfailed line\n", ""),
    )

    diagnostic = decision.failed_run_diagnostics[0]
    assert decision.decision == "red"
    assert diagnostic.run_id == "123456"
    assert diagnostic.log_status == "fetched"
    assert diagnostic.log_excerpt == "123456\nfailed line"


def test_render_result_marks_post_merge_red_main_ci_as_fail() -> None:
    pr_status = status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "head",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        }
    )
    main_status = verify_main_ci(
        "abc123def456",
        branch="main",
        timeout_seconds=1,
        poll_seconds=0,
        fetcher=lambda commit_sha, branch: {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": commit_sha,
            "statusCheckRollup": [
                {
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://github.com/vfi64/agentic-project-kit/actions/runs/123456/job/789",
                },
            ],
        },
        failed_log_fetcher=lambda run_id: (0, "failed line\n", ""),
    )
    result = MergeIfGreenResult(
        pr="1",
        decision="merge",
        reason="PR is green",
        status_decision=pr_status,
        merged=True,
        merge_output="merged",
        merge_commit_sha="abc123def456",
        main_verification_required=True,
        main_status_decision=main_status,
    )

    rendered = render_result(result)
    assert not main_verification_passed(result)
    assert "main_verification_decision=red" in rendered
    assert "main_verification_passed=false" in rendered
    assert "gh run view 123456 --log-failed" in rendered
    assert "### RESULT: FAIL ###" in rendered
