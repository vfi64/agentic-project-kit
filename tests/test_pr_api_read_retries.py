"""Bounded retries apply only to observable transient GitHub read failures."""
import pytest

from agentic_project_kit.ci_readiness import BLOCKED, GH_ERROR, READY_TO_MERGE, TIMEOUT, render_pr_readiness, wait_for_pr_readiness
from test_pr_ci_readiness import clean_snapshot


def test_transient_read_recovers_without_repeating_a_mutation():
    calls, sleeps = [], []
    def provider():
        calls.append("read")
        if len(calls) == 1:
            raise RuntimeError("HTTP 503 Service Unavailable")
        return clean_snapshot()
    decision = wait_for_pr_readiness(provider, expected_head_sha="abc123",
        clock=lambda: 0, sleep=sleeps.append, interval_seconds=5)
    assert decision.outcome == READY_TO_MERGE
    assert calls == ["read", "read"] and sleeps == [5]


def test_transient_read_retries_are_bounded_even_with_a_constant_clock():
    calls, sleeps = [], []
    def provider():
        calls.append("read")
        raise RuntimeError("HTTP 503 Service Unavailable")
    decision = wait_for_pr_readiness(provider, clock=lambda: 0, sleep=sleeps.append)
    assert decision.outcome == GH_ERROR and len(calls) == 3 and len(sleeps) == 2


@pytest.mark.parametrize("message", ["GraphQL: API rate limit already exceeded",
                                     "HTTP 401 Bad credentials", "HTTP 403 Forbidden",
                                     "malformed response"])
def test_nontransient_errors_are_not_retried(message):
    calls, sleeps = [], []
    def provider():
        calls.append("read")
        raise RuntimeError(message)
    decision = wait_for_pr_readiness(provider, clock=lambda: 0, sleep=sleeps.append)
    assert decision.outcome == GH_ERROR and calls == ["read"] and not sleeps


def test_retry_deadline_stops_before_another_read():
    times = iter([0, 0, 0, 5])
    calls, sleeps = [], []
    def provider():
        calls.append("read")
        raise RuntimeError("HTTP 503 Service Unavailable")
    decision = wait_for_pr_readiness(provider, timeout_seconds=5, interval_seconds=10,
                                    clock=lambda: next(times), sleep=sleeps.append)
    assert decision.outcome == TIMEOUT and calls == ["read"] and sleeps == [5]
    assert "HTTP 503" in render_pr_readiness(decision)


def test_rate_limit_diagnostic_preserves_observable_reset_without_polling():
    message = "GraphQL: API rate limit exceeded; resetAt=2026-10-09T19:13:58Z"
    def provider():
        raise RuntimeError(message)
    sleeps = []
    decision = wait_for_pr_readiness(provider, clock=lambda: 0, sleep=sleeps.append)
    assert decision.outcome == GH_ERROR and not sleeps
    assert message in render_pr_readiness(decision)


def test_real_ci_failure_is_never_retried():
    calls, sleeps = [], []
    def provider():
        calls.append("read")
        snapshot = clean_snapshot()
        snapshot['statusCheckRollup'][0]['conclusion'] = 'FAILURE'
        return snapshot
    decision = wait_for_pr_readiness(provider, clock=lambda: 0, sleep=sleeps.append)
    assert decision.outcome == BLOCKED and calls == ["read"] and not sleeps
