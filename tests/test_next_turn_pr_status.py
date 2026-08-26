from __future__ import annotations

from agentic_project_kit.next_turn_pr_status import (
    attach_failed_run_logs,
    classify_pr_status,
    fetch_pr_payload,
    render_decision,
)


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


def test_red_pr_status_extracts_failed_run_command_from_details_url() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNSTABLE",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://github.com/vfi64/agentic-project-kit/actions/runs/123456/job/789",
                },
            ],
        },
        pr="2",
    )

    assert decision.failed_run_log_hint == "run: gh run view 123456 --log-failed"
    assert decision.failed_run_diagnostics[0].run_id == "123456"
    assert decision.failed_run_diagnostics[0].command == "gh run view 123456 --log-failed"


def test_failed_run_logs_are_attached_with_bounded_excerpt() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNSTABLE",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://github.com/vfi64/agentic-project-kit/actions/runs/123456/job/789",
                },
            ],
        },
        pr="2",
    )

    with_logs = attach_failed_run_logs(decision, max_lines=2, fetcher=lambda run_id: (0, f"{run_id}\nline2\nline3\n", ""))

    diagnostic = with_logs.failed_run_diagnostics[0]
    assert diagnostic.log_status == "fetched"
    assert diagnostic.log_excerpt == "123456\nline2\n... (1 lines omitted)"


def test_fetch_pr_payload_falls_back_to_exact_head_actions_runs(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run_gh(args: list[str]) -> str:
        calls.append(args)
        if args[:3] == ["pr", "view", "2185"]:
            return (
                '{"state":"OPEN","headRefOid":"abc123","headRefName":"feature",'
                '"mergeStateStatus":"CLEAN","statusCheckRollup":[]}'
            )
        if args[:4] == ["run", "list", "--branch", "feature"]:
            return (
                '[{"databaseId":123456,"name":"CI","workflowName":"CI",'
                '"status":"completed","conclusion":"success",'
                '"url":"https://github.com/vfi64/agentic-project-kit/actions/runs/123456",'
                '"createdAt":"2026-08-26T15:39:51Z","updatedAt":"2026-08-26T15:42:00Z"}]'
            )
        if args == ["api", "repos/{owner}/{repo}/actions/runs/123456/jobs"]:
            return '{"total_count":1}'
        raise AssertionError(args)

    import agentic_project_kit.next_turn_pr_status as pr_status

    monkeypatch.setattr(pr_status, "_run_gh", fake_run_gh)

    payload = fetch_pr_payload("2185")

    assert payload["statusCheckRollupSource"] == "actions_head_runs_fallback"
    assert payload["statusCheckRollup"][0]["name"] == "CI"
    assert payload["statusCheckRollup"][0]["conclusion"] == "success"
    assert calls[0][:3] == ["pr", "view", "2185"]
    assert calls[1][:4] == ["run", "list", "--branch", "feature"]


def test_fetch_pr_payload_keeps_no_checks_when_actions_fallback_fails(monkeypatch) -> None:
    def fake_run_gh(args: list[str]) -> str:
        if args[:3] == ["pr", "view", "2185"]:
            return (
                '{"state":"OPEN","headRefOid":"abc123","headRefName":"feature",'
                '"mergeStateStatus":"CLEAN","statusCheckRollup":[]}'
            )
        if args[:4] == ["run", "list", "--branch", "feature"]:
            raise RuntimeError("actions unavailable")
        raise AssertionError(args)

    import agentic_project_kit.next_turn_pr_status as pr_status

    monkeypatch.setattr(pr_status, "_run_gh", fake_run_gh)

    payload = fetch_pr_payload("2185")

    assert payload["statusCheckRollup"] == []
    assert payload["statusCheckRollupFallbackError"] == "actions unavailable"


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


def test_classify_no_checks_pr_status() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNKNOWN",
            "headRefOid": "abc",
            "statusCheckRollup": [],
        },
        pr="3",
    )
    assert decision.decision == "no-checks"


def test_classify_stale_zero_job_check_without_success_as_stale() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {
                    "name": "CI",
                    "status": "QUEUED",
                    "conclusion": None,
                    "jobCount": 0,
                    "staleRemoteEvidence": True,
                },
            ],
        },
        pr="3",
    )

    assert decision.decision == "stale"
    assert decision.stale_checks == ("CI",)
    assert decision.pending_checks == ()


def test_classify_stale_duplicate_is_neutralized_by_successful_same_named_check() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc",
            "statusCheckRollup": [
                {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"},
                {
                    "name": "CI",
                    "status": "QUEUED",
                    "conclusion": None,
                    "jobCount": 0,
                    "staleRemoteEvidence": True,
                },
            ],
        },
        pr="3",
    )

    assert decision.decision == "green"
    assert decision.successful_checks == ("CI",)
    assert decision.stale_checks == ("CI",)


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
    assert "stale_checks:" in rendered
    assert "failed_run_diagnostics:" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_render_decision_marks_no_checks_as_failed_readiness() -> None:
    decision = classify_pr_status(
        {
            "state": "OPEN",
            "mergeStateStatus": "UNKNOWN",
            "headRefOid": "abc",
            "statusCheckRollup": [],
        },
        pr="5",
    )

    rendered = render_decision(decision)

    assert "decision=no-checks" in rendered
    assert "### RESULT: FAIL ###" in rendered
