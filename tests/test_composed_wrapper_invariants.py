from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_project_kit.composed_wrapper_invariants import (
    assert_no_failed_required_step_promoted_to_pass,
    validate_no_failed_required_step_promoted_to_pass,
)


@dataclass(frozen=True)
class DummyResult:
    result_status: str
    lifecycle_state: str = ""


@dataclass(frozen=True)
class DummyStep:
    name: str
    result: DummyResult


def test_composed_wrapper_invariant_blocks_failed_step_promoted_to_pass() -> None:
    violations = validate_no_failed_required_step_promoted_to_pass(
        wrapper="demo-wrapper",
        wrapper_status="PASS",
        steps=[DummyStep("required-check", DummyResult("FAIL", "NOOP"))],
    )

    assert len(violations) == 1
    assert violations[0].wrapper == "demo-wrapper"
    assert violations[0].step_name == "required-check"


def test_composed_wrapper_invariant_allows_explicit_recovery_state() -> None:
    violations = validate_no_failed_required_step_promoted_to_pass(
        wrapper="post-merge-complete",
        wrapper_status="PASS",
        steps=[
            DummyStep(
                "initial-post-merge-check",
                DummyResult("FAIL", "REFRESH_REQUIRED"),
            )
        ],
        allowed_recovery_states=("REFRESH_REQUIRED",),
    )

    assert violations == []


def test_composed_wrapper_invariant_ignores_non_pass_wrapper_result() -> None:
    violations = validate_no_failed_required_step_promoted_to_pass(
        wrapper="demo-wrapper",
        wrapper_status="BLOCKED",
        steps=[DummyStep("required-check", DummyResult("FAIL", "NOOP"))],
    )

    assert violations == []


def test_composed_wrapper_invariant_assertion_raises_on_violation() -> None:
    with pytest.raises(AssertionError, match="demo-wrapper returned PASS"):
        assert_no_failed_required_step_promoted_to_pass(
            wrapper="demo-wrapper",
            wrapper_status="PASS",
            steps=[DummyStep("required-check", DummyResult("BLOCKED"))],
        )
