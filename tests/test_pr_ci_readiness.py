from agentic_project_kit.ci_readiness import (
    ALREADY_MERGED,
    BLOCKED,
    READY_TO_MERGE,
    TIMEOUT,
    WAITING,
    classify_pr_readiness,
)


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
