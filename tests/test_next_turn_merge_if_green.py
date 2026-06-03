from __future__ import annotations

import subprocess

import agentic_project_kit.next_turn_merge_if_green as merge_if_green_module
from agentic_project_kit.next_turn_merge_if_green import (
    MergeIfGreenResult,
    PrMergeRefs,
    build_merge_args,
    decide_merge,
    main_verification_passed,
    render_result,
    verify_merge_refs,
    verify_main_ci,
    wait_for_pr_merge_state,
)
from agentic_project_kit.next_turn_pr_status import classify_pr_status


def status(payload: dict[str, object]):
    return classify_pr_status(payload, pr="1")


def green_payload(*, base_ref_name: str = "main", head_ref_oid: str = "head") -> dict[str, object]:
    return {
        "state": "OPEN",
        "mergeStateStatus": "CLEAN",
        "baseRefName": base_ref_name,
        "baseRefOid": "base",
        "headRefName": "feature",
        "headRefOid": head_ref_oid,
        "statusCheckRollup": [
            {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    }


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


def test_decide_merge_refuses_unknown_merge_state_even_when_checks_are_green() -> None:
    decision, reason = decide_merge(
        status(
            {
                "state": "OPEN",
                "mergeStateStatus": "UNKNOWN",
                "headRefOid": "abc",
                "statusCheckRollup": [
                    {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
                ],
            }
        )
    )
    assert decision == "refuse"
    assert "merge state is not clean: UNKNOWN" == reason


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


def test_verify_merge_refs_accepts_expected_base_and_head() -> None:
    decision, reason = verify_merge_refs(
        PrMergeRefs(
            base_ref_name="main",
            base_ref_oid="base",
            head_ref_name="feature",
            head_ref_oid="head",
        ),
        expected_base_branch="main",
        expected_head_sha="head",
    )

    assert decision == "merge"
    assert reason == "PR base/head refs verified"


def test_verify_merge_refs_refuses_wrong_base_branch() -> None:
    decision, reason = verify_merge_refs(
        PrMergeRefs(
            base_ref_name="develop",
            base_ref_oid="base",
            head_ref_name="feature",
            head_ref_oid="head",
        ),
        expected_base_branch="main",
        expected_head_sha="head",
    )

    assert decision == "refuse"
    assert "expected main" in reason


def test_verify_merge_refs_refuses_missing_head_sha() -> None:
    decision, reason = verify_merge_refs(
        PrMergeRefs(
            base_ref_name="main",
            base_ref_oid="base",
            head_ref_name="feature",
            head_ref_oid="",
        ),
        expected_base_branch="main",
    )

    assert decision == "refuse"
    assert reason == "missing PR head SHA"


def test_verify_merge_refs_refuses_head_drift() -> None:
    decision, reason = verify_merge_refs(
        PrMergeRefs(
            base_ref_name="main",
            base_ref_oid="base",
            head_ref_name="feature",
            head_ref_oid="new-head",
        ),
        expected_base_branch="main",
        expected_head_sha="old-head",
    )

    assert decision == "refuse"
    assert "PR head changed" in reason


def test_build_merge_args_pins_head_commit() -> None:
    args = build_merge_args(
        "123",
        merge_method="squash",
        delete_branch=True,
        match_head_sha="abc123",
    )

    assert args == [
        "pr",
        "merge",
        "123",
        "--squash",
        "--match-head-commit",
        "abc123",
        "--delete-branch",
    ]


def test_merge_if_green_refuses_unexpected_base_before_merge(monkeypatch) -> None:
    monkeypatch.setattr(merge_if_green_module, "fetch_pr_payload", lambda _pr: green_payload(base_ref_name="develop"))

    def fail_run(_args: list[str]) -> subprocess.CompletedProcess[str]:
        raise AssertionError("merge command must not run when base branch mismatches")

    monkeypatch.setattr(merge_if_green_module, "_run_gh", fail_run)

    result = merge_if_green_module.merge_if_green("123", expected_base_branch="main")

    assert result.decision == "refuse"
    assert result.reason == "PR base branch is develop, expected main"
    assert not result.merged




def test_wait_for_pr_merge_state_waits_from_unknown_to_clean() -> None:
    calls: list[dict[str, object]] = []
    sleeps: list[float] = []
    payloads = [
        green_payload(head_ref_oid="abc123") | {"mergeStateStatus": "UNKNOWN"},
        green_payload(head_ref_oid="abc123"),
    ]

    def fetcher(_pr: str) -> dict[str, object]:
        payload = payloads[len(calls)]
        calls.append(payload)
        return payload

    _payload, decision, refs, wait_reason = wait_for_pr_merge_state(
        "123",
        timeout_seconds=20,
        poll_seconds=10,
        fetcher=fetcher,
        sleep=sleeps.append,
    )

    assert decision.decision == "green"
    assert decision.merge_state_status == "CLEAN"
    assert refs.head_ref_oid == "abc123"
    assert wait_reason == ""
    assert len(calls) == 2
    assert sleeps == [10]


def test_merge_if_green_waits_for_unknown_merge_state_before_merge(monkeypatch) -> None:
    commands: list[list[str]] = []
    sleeps: list[float] = []
    payloads = [
        green_payload(head_ref_oid="abc123") | {"mergeStateStatus": "UNKNOWN"},
        green_payload(head_ref_oid="abc123"),
    ]

    def fetcher(_pr: str) -> dict[str, object]:
        return payloads.pop(0)

    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="merged", stderr="")

    monkeypatch.setattr(merge_if_green_module, "_run_gh", fake_run)

    result = merge_if_green_module.merge_if_green(
        "123",
        expected_head_sha="abc123",
        verify_main=False,
        merge_state_timeout_seconds=20,
        merge_state_poll_seconds=10,
        pr_payload_fetcher=fetcher,
        sleep=sleeps.append,
    )

    assert result.decision == "merge"
    assert result.merged
    assert result.status_decision.merge_state_status == "CLEAN"
    assert sleeps == [10]
    assert commands == [["pr", "merge", "123", "--squash", "--match-head-commit", "abc123", "--delete-branch"]]


def test_merge_if_green_refuses_after_merge_state_timeout(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fetcher(_pr: str) -> dict[str, object]:
        return green_payload(head_ref_oid="abc123") | {"mergeStateStatus": "UNKNOWN"}

    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="merged", stderr="")

    monkeypatch.setattr(merge_if_green_module, "_run_gh", fake_run)

    result = merge_if_green_module.merge_if_green(
        "123",
        expected_head_sha="abc123",
        verify_main=False,
        merge_state_timeout_seconds=1,
        merge_state_poll_seconds=0,
        pr_payload_fetcher=fetcher,
        sleep=lambda _seconds: None,
    )

    assert result.decision == "refuse"
    assert result.reason == "merge state stayed UNKNOWN after timeout"
    assert not result.merged
    assert commands == []

def test_merge_if_green_uses_match_head_commit_for_merge(monkeypatch) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(merge_if_green_module, "fetch_pr_payload", lambda _pr: green_payload(head_ref_oid="abc123"))

    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="merged", stderr="")

    monkeypatch.setattr(merge_if_green_module, "_run_gh", fake_run)

    result = merge_if_green_module.merge_if_green("123", verify_main=False)

    assert result.decision == "merge"
    assert result.merged
    assert result.expected_head_sha == "abc123"
    assert commands == [
        [
            "pr",
            "merge",
            "123",
            "--squash",
            "--match-head-commit",
            "abc123",
            "--delete-branch",
        ]
    ]


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
        base_ref_name="main",
        base_ref_oid="base",
        head_ref_name="feature",
        head_ref_oid="abc",
        expected_base_branch="main",
        expected_head_sha="abc",
    )

    rendered = render_result(result)
    assert "NEXT_TURN_MERGE_IF_GREEN" in rendered
    assert "decision=merge" in rendered
    assert "base_ref_name=main" in rendered
    assert "head_ref_oid=abc" in rendered
    assert "expected_head_sha=abc" in rendered
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
