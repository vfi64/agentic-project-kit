from typer.testing import CliRunner

from agentic_project_kit.ci_readiness import (
    ALREADY_MERGED,
    BLOCKED,
    GH_ERROR,
    READY_TO_MERGE,
    TIMEOUT,
    WAITING,
    classify_pr_readiness,
    gh_pr_snapshot_provider,
    render_pr_readiness,
    wait_for_pr_readiness,
)
from agentic_project_kit.cli import app


def clean_snapshot():
    return {
        "state": "OPEN",
        "headRefOid": "abc123",
        "mergeStateStatus": "CLEAN",
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [
            {
                "name": "test",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            }
        ],
    }


def test_clean_ci_snapshot_is_ready_to_merge():
    decision = classify_pr_readiness(
        clean_snapshot(),
        expected_head_sha="abc123",
        expected_checks=("test",),
    )
    assert decision.outcome == READY_TO_MERGE
    assert decision.terminal
    assert decision.success


def test_optional_skipped_shadow_does_not_block_readiness():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"].append(
        {
            "name": "pytest-parallel-shadow",
            "status": "COMPLETED",
            "conclusion": "SKIPPED",
        }
    )

    decision = classify_pr_readiness(
        snapshot,
        expected_head_sha="abc123",
        expected_checks=("test",),
    )

    assert decision.outcome == READY_TO_MERGE
    assert decision.success


def test_unlisted_skipped_check_blocks_readiness():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"].append(
        {
            "name": "deploy",
            "status": "COMPLETED",
            "conclusion": "SKIPPED",
        }
    )

    decision = classify_pr_readiness(snapshot, expected_head_sha="abc123")

    assert decision.outcome == BLOCKED
    assert decision.terminal
    assert decision.reasons == ("check skipped: deploy",)


def test_only_optional_skipped_shadow_waits_for_required_evidence():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"] = [
        {
            "name": "pytest-parallel-shadow",
            "status": "COMPLETED",
            "conclusion": "SKIPPED",
        }
    ]

    decision = classify_pr_readiness(snapshot)

    assert decision.outcome == WAITING
    assert not decision.success
    assert decision.reasons == ("no successful required checks reported yet",)


def test_changed_head_sha_blocks_merge_readiness():
    snapshot = clean_snapshot()
    snapshot["headRefOid"] = "moved"
    decision = classify_pr_readiness(snapshot, expected_head_sha="abc123")
    assert decision.outcome == BLOCKED
    assert "head SHA changed" in decision.reasons[0]


def test_pending_checks_wait_instead_of_passing():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"][0]["status"] = "IN_PROGRESS"
    snapshot["statusCheckRollup"][0]["conclusion"] = ""
    decision = classify_pr_readiness(snapshot, elapsed_seconds=120, timeout_seconds=300)
    assert decision.outcome == WAITING
    assert not decision.terminal


def test_timeout_is_terminal_failure():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"][0]["status"] = "IN_PROGRESS"
    decision = classify_pr_readiness(snapshot, elapsed_seconds=301, timeout_seconds=300)
    assert decision.outcome == TIMEOUT
    assert decision.terminal
    assert not decision.success


def test_failed_check_blocks_immediately():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"][0]["conclusion"] = "FAILURE"
    decision = classify_pr_readiness(snapshot)
    assert decision.outcome == BLOCKED
    assert "check failed" in decision.reasons[0]


def test_no_checks_waits_instead_of_false_pass():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"] = []
    decision = classify_pr_readiness(snapshot)
    assert decision.outcome == WAITING
    assert not decision.terminal
    assert "no status checks" in decision.reasons[0]


def test_stale_zero_job_check_blocks_without_wait_loop():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"] = [
        {
            "name": "CI",
            "status": "QUEUED",
            "conclusion": "",
            "staleRemoteEvidence": True,
        }
    ]

    decision = classify_pr_readiness(snapshot)

    assert decision.outcome == BLOCKED
    assert decision.terminal
    assert decision.reasons == ("stale queued/no-job remote check: CI",)


def test_stale_duplicate_check_does_not_block_same_named_success():
    snapshot = clean_snapshot()
    snapshot["statusCheckRollup"] = [
        {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {
            "name": "CI",
            "status": "QUEUED",
            "conclusion": "",
            "staleRemoteEvidence": True,
        },
    ]

    decision = classify_pr_readiness(snapshot)

    assert decision.outcome == READY_TO_MERGE
    assert decision.success


def test_missing_expected_check_waits_not_passes():
    decision = classify_pr_readiness(clean_snapshot(), expected_checks=("test", "lint"))
    assert decision.outcome == WAITING
    assert "expected check missing: lint" in decision.reasons


def test_merged_pr_with_successful_checks_is_idempotent_success():
    snapshot = clean_snapshot()
    snapshot["state"] = "MERGED"
    snapshot["mergeStateStatus"] = "UNKNOWN"
    snapshot["mergeable"] = "UNKNOWN"
    decision = classify_pr_readiness(snapshot)
    assert decision.outcome == ALREADY_MERGED
    assert decision.success


def test_unclean_merge_state_blocks_even_after_successful_checks():
    snapshot = clean_snapshot()
    snapshot["mergeStateStatus"] = "BEHIND"
    decision = classify_pr_readiness(snapshot)
    assert decision.outcome == BLOCKED
    assert "mergeStateStatus is not CLEAN" in decision.reasons[0]


def test_non_mergeable_pr_blocks_even_after_successful_checks():
    snapshot = clean_snapshot()
    snapshot["mergeable"] = "CONFLICTING"
    decision = classify_pr_readiness(snapshot)
    assert decision.outcome == BLOCKED
    assert "PR is not mergeable" in decision.reasons[0]


def test_wait_for_pr_readiness_retries_pending_then_passes():
    snapshots = [
        {
            **clean_snapshot(),
            "statusCheckRollup": [{"name": "test", "status": "IN_PROGRESS", "conclusion": ""}],
        },
        clean_snapshot(),
    ]
    clock_values = iter([0, 0, 1])
    sleeps = []

    def provider():
        return snapshots.pop(0)

    decision = wait_for_pr_readiness(
        provider,
        expected_head_sha="abc123",
        timeout_seconds=30,
        interval_seconds=5,
        clock=lambda: next(clock_values),
        sleep=sleeps.append,
    )
    assert decision.outcome == READY_TO_MERGE
    assert sleeps == [5]


def test_wait_for_pr_readiness_turns_provider_error_into_terminal_failure():
    def provider():
        raise RuntimeError("gh unavailable")

    decision = wait_for_pr_readiness(provider, clock=lambda: 0, sleep=lambda seconds: None)
    assert decision.outcome == GH_ERROR
    assert decision.terminal
    assert not decision.success
    assert decision.reasons == ("gh unavailable",)


def test_gh_pr_snapshot_provider_uses_exact_head_actions_fallback(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(command, check=False, capture_output=True, text=True):
        calls.append(command)
        if command[:3] == ["gh", "pr", "view"]:
            return type(
                "Completed",
                (),
                {
                    "returncode": 0,
                    "stdout": (
                        '{"state":"OPEN","headRefOid":"abc123","headRefName":"feature",'
                        '"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE","statusCheckRollup":[]}'
                    ),
                    "stderr": "",
                },
            )()
        if command[:4] == ["gh", "run", "list", "--branch"]:
            return type(
                "Completed",
                (),
                {
                    "returncode": 0,
                    "stdout": (
                        '[{"databaseId":123456,"name":"CI","workflowName":"CI",'
                        '"status":"completed","conclusion":"success",'
                        '"url":"https://github.com/vfi64/agentic-project-kit/actions/runs/123456",'
                        '"createdAt":"2026-08-26T15:39:51Z","updatedAt":"2026-08-26T15:42:00Z"}]'
                    ),
                    "stderr": "",
                },
            )()
        if command == ["gh", "api", "repos/{owner}/{repo}/actions/runs/123456/jobs"]:
            return type("Completed", (), {"returncode": 0, "stdout": '{"total_count":1}', "stderr": ""})()
        raise AssertionError(command)

    import agentic_project_kit.ci_readiness as ci_readiness

    monkeypatch.setattr(ci_readiness.subprocess, "run", fake_run)

    payload = gh_pr_snapshot_provider(2185)()

    assert payload["statusCheckRollup"][0]["name"] == "CI"
    assert payload["statusCheckRollup"][0]["conclusion"] == "success"
    assert calls[0][:3] == ["gh", "pr", "view"]
    assert "headRefName" in calls[0][5]
    assert calls[1][:4] == ["gh", "run", "list", "--branch"]


def test_gh_pr_snapshot_provider_keeps_no_checks_when_actions_fallback_fails(monkeypatch):
    def fake_run(command, check=False, capture_output=True, text=True):
        if command[:3] == ["gh", "pr", "view"]:
            return type(
                "Completed",
                (),
                {
                    "returncode": 0,
                    "stdout": (
                        '{"state":"OPEN","headRefOid":"abc123","headRefName":"feature",'
                        '"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE","statusCheckRollup":[]}'
                    ),
                    "stderr": "",
                },
            )()
        if command[:4] == ["gh", "run", "list", "--branch"]:
            return type("Completed", (), {"returncode": 1, "stdout": "", "stderr": "actions unavailable"})()
        raise AssertionError(command)

    import agentic_project_kit.ci_readiness as ci_readiness

    monkeypatch.setattr(ci_readiness.subprocess, "run", fake_run)

    payload = gh_pr_snapshot_provider(2185)()

    assert payload["statusCheckRollup"] == []
    assert payload["statusCheckRollupFallbackError"] == "actions unavailable"


def test_render_pr_readiness_includes_machine_readable_outcome():
    rendered = render_pr_readiness(
        classify_pr_readiness(clean_snapshot(), expected_head_sha="abc123")
    )
    assert "PR readiness outcome: READY_TO_MERGE" in rendered
    assert "success=true" in rendered


def test_pr_wait_ci_help_is_registered_without_running_gh():
    result = CliRunner().invoke(app, ["pr", "wait-ci", "--help"])
    assert result.exit_code == 0
    assert "Polling interval" in result.output
    assert "Maximum wait time" in result.output


def test_pr_status_help_is_registered_without_running_gh():
    result = CliRunner().invoke(app, ["pr", "status", "--help"])
    assert result.exit_code == 0
    assert "Print deterministic PR/CI status" in result.output


def test_pr_status_cli_no_failed_log_fetch_skips_fetcher(monkeypatch):
    from agentic_project_kit.cli_commands import pr as pr_commands

    monkeypatch.setattr(
        pr_commands,
        "fetch_pr_payload",
        lambda pr: {
            "state": "OPEN",
            "mergeStateStatus": "UNSTABLE",
            "headRefOid": "abc123",
            "statusCheckRollup": [
                {
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://github.com/vfi64/agentic-project-kit/actions/runs/123456/job/789",
                },
            ],
        },
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("failed log fetch should be skipped")

    monkeypatch.setattr(pr_commands, "attach_failed_run_logs", fail_if_called)

    result = CliRunner().invoke(app, ["pr", "status", "123", "--no-failed-log-fetch"])
    assert result.exit_code == 0
    assert "decision=red" in result.output
    assert "log_status=not-fetched" in result.output


def test_pr_status_cli_renders_green_snapshot_without_running_gh(monkeypatch):
    from agentic_project_kit.cli_commands import pr as pr_commands

    monkeypatch.setattr(
        pr_commands,
        "fetch_pr_payload",
        lambda pr: {
            "state": "OPEN",
            "mergeStateStatus": "CLEAN",
            "headRefOid": "abc123",
            "statusCheckRollup": [
                {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        },
    )

    result = CliRunner().invoke(app, ["pr", "status", "123"])
    assert result.exit_code == 0
    assert "NEXT_TURN_PR_STATUS" in result.output
    assert "pr=123" in result.output
    assert "decision=green" in result.output

def test_pr_merge_if_green_help_is_registered_without_running_gh():
    result = CliRunner().invoke(app, ["pr", "merge-if-green", "--help"])
    assert result.exit_code == 0
    assert "Merge only when PR checks are green" in result.output


def test_pr_merge_if_green_cli_passes_expected_head_sha(monkeypatch):
    from agentic_project_kit.cli_commands import pr as pr_commands

    captured: dict[str, object] = {}

    def fake_merge_if_green(pr_number: str, **kwargs):
        from agentic_project_kit.next_turn_merge_if_green import MergeIfGreenResult
        from agentic_project_kit.next_turn_pr_status import classify_pr_status

        captured["pr_number"] = pr_number
        captured.update(kwargs)
        status = classify_pr_status(
            {
                "state": "OPEN",
                "mergeStateStatus": "CLEAN",
                "headRefOid": "expected-sha",
                "statusCheckRollup": [
                    {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
                ],
            },
            pr=pr_number,
        )
        return MergeIfGreenResult(
            pr=pr_number,
            decision="merge",
            reason="DRY_RUN: PR is green",
            status_decision=status,
            merged=False,
            merge_output="",
            expected_head_sha=str(kwargs["expected_head_sha"]),
        )

    monkeypatch.setattr(pr_commands, "merge_if_green", fake_merge_if_green)

    result = CliRunner().invoke(
        app,
        ["pr", "merge-if-green", "123", "--dry-run", "--expected-head-sha", "expected-sha"],
    )

    assert result.exit_code == 0
    assert captured["pr_number"] == "123"
    assert captured["expected_head_sha"] == "expected-sha"
    assert "expected_head_sha=expected-sha" in result.output
