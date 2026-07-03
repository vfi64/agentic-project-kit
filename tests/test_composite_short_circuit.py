from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_project_kit.composite_short_circuit import (
    assert_no_effectful_steps_after_required_failure,
    validate_no_effectful_steps_after_required_failure,
)


@dataclass(frozen=True)
class DummyResult:
    result_status: str
    action: str


@dataclass(frozen=True)
class DummyStep:
    name: str
    result: DummyResult


def step(name: str, status: str, action: str | None = None) -> DummyStep:
    return DummyStep(name=name, result=DummyResult(result_status=status, action=action or name))


def test_short_circuit_blocks_commit_after_failed_gate() -> None:
    violations = validate_no_effectful_steps_after_required_failure(
        wrapper="patch-cycle-complete",
        steps=[
            step("protected-diff-plan", "FAIL"),
            step("commit", "PASS"),
        ],
    )

    assert len(violations) == 1
    assert violations[0].failed_step_name == "protected-diff-plan"
    assert violations[0].later_step_name == "commit"


def test_short_circuit_blocks_pr_after_failed_push() -> None:
    violations = validate_no_effectful_steps_after_required_failure(
        wrapper="patch-cycle-complete",
        steps=[
            step("push-current", "BLOCKED"),
            step("pr-create", "PASS"),
        ],
    )

    assert len(violations) == 1
    assert violations[0].later_action == "pr-create"


def test_short_circuit_allows_diagnostic_steps_after_failure() -> None:
    violations = validate_no_effectful_steps_after_required_failure(
        wrapper="patch-cycle-complete",
        steps=[
            step("pytest", "FAIL"),
            step("repo-status", "PASS"),
            step("diagnose", "PASS"),
        ],
    )

    assert violations == []


def test_short_circuit_allows_explicit_recovery_step() -> None:
    violations = validate_no_effectful_steps_after_required_failure(
        wrapper="post-merge-complete",
        steps=[
            step("pr-merge-safe", "BLOCKED"),
            step("merge-block-recovery-main-sync", "PASS", "pull-current"),
            step("merge-block-recovery-post-merge-check", "PASS", "post-merge-check"),
        ],
        allowed_recovery_actions=("pull-current", "post-merge-check"),
    )

    assert violations == []


def test_short_circuit_assertion_raises() -> None:
    with pytest.raises(AssertionError, match="executed effectful step commit"):
        assert_no_effectful_steps_after_required_failure(
            wrapper="patch-cycle-complete",
            steps=[
                step("pytest", "FAIL"),
                step("commit", "PASS"),
            ],
        )
