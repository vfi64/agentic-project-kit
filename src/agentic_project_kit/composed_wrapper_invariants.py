from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


class StepLike(Protocol):
    name: str
    result: object


@dataclass(frozen=True)
class WrapperInvariantViolation:
    wrapper: str
    step_name: str
    step_status: str
    wrapper_status: str
    allowed_recovery_states: tuple[str, ...]
    message: str


def _status_of(result: object) -> str:
    value = getattr(result, "result_status", "")
    return str(value or "").upper()


def _state_of(result: object) -> str:
    value = getattr(result, "lifecycle_state", "")
    if not value:
        value = getattr(result, "state", "")
    return str(value or "").upper()


def validate_no_failed_required_step_promoted_to_pass(
    *,
    wrapper: str,
    wrapper_status: str,
    steps: Iterable[StepLike],
    allowed_recovery_states: Iterable[str] = (),
) -> list[WrapperInvariantViolation]:
    """Validate the central composed-wrapper safety invariant.

    A composed wrapper must not report PASS when a required substep reported
    FAIL/BLOCKED unless that substep state is explicitly allowlisted as a
    recovery state by the wrapper.

    The helper is intentionally small and pure so lifecycle tests can use it
    without shelling out or creating repository state.
    """

    normalized_wrapper_status = str(wrapper_status or "").upper()
    if normalized_wrapper_status != "PASS":
        return []

    allowed = tuple(str(item or "").upper() for item in allowed_recovery_states)
    violations: list[WrapperInvariantViolation] = []

    for step in steps:
        result = getattr(step, "result", None)
        step_status = _status_of(result)
        step_state = _state_of(result)
        if step_status not in {"FAIL", "BLOCKED"}:
            continue
        if step_state and step_state in allowed:
            continue
        violations.append(
            WrapperInvariantViolation(
                wrapper=wrapper,
                step_name=str(getattr(step, "name", "")),
                step_status=step_status,
                wrapper_status=normalized_wrapper_status,
                allowed_recovery_states=allowed,
                message=(
                    f"{wrapper} returned PASS although required step "
                    f"{getattr(step, 'name', '')!s} returned {step_status}."
                ),
            )
        )

    return violations


def assert_no_failed_required_step_promoted_to_pass(
    *,
    wrapper: str,
    wrapper_status: str,
    steps: Iterable[StepLike],
    allowed_recovery_states: Iterable[str] = (),
) -> None:
    violations = validate_no_failed_required_step_promoted_to_pass(
        wrapper=wrapper,
        wrapper_status=wrapper_status,
        steps=steps,
        allowed_recovery_states=allowed_recovery_states,
    )
    if violations:
        raise AssertionError("; ".join(item.message for item in violations))
