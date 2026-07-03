from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


TERMINAL_BAD_STATUSES = {"FAIL", "BLOCKED"}
DEFAULT_EFFECTFUL_ACTIONS_AFTER_FAILURE = {
    "commit",
    "push",
    "push-current",
    "pr-create",
    "pr-create-complete",
    "pr-complete",
    "pr-merge",
    "pr-merge-safe",
    "merge",
    "admin-refresh-pr",
    "post-merge-complete",
    "prepare-successor-handoff",
    "successor-handoff",
    "handoff",
    "release",
    "publish",
}


class StepLike(Protocol):
    name: str
    result: object


@dataclass(frozen=True)
class CompositeShortCircuitViolation:
    wrapper: str
    failed_step_name: str
    failed_step_status: str
    later_step_name: str
    later_action: str
    message: str


def _status_of(result: object) -> str:
    return str(getattr(result, "result_status", "") or "").upper()


def _action_of(step: StepLike) -> str:
    result = getattr(step, "result", None)
    action = getattr(result, "action", "")
    if action:
        return str(action)
    return str(getattr(step, "name", ""))


def _is_allowed_recovery_step(action: str, allowed_recovery_actions: tuple[str, ...]) -> bool:
    normalized = action.lower()
    return any(item.lower() == normalized for item in allowed_recovery_actions)


def _is_effectful_after_failure(action: str, effectful_actions: tuple[str, ...]) -> bool:
    normalized = action.lower()
    return any(item.lower() in normalized for item in effectful_actions)


def validate_no_effectful_steps_after_required_failure(
    *,
    wrapper: str,
    steps: Iterable[StepLike],
    allowed_recovery_actions: Iterable[str] = (),
    effectful_actions: Iterable[str] = DEFAULT_EFFECTFUL_ACTIONS_AFTER_FAILURE,
) -> list[CompositeShortCircuitViolation]:
    """Validate composite-wrapper short-circuit discipline.

    After a required substep reports FAIL/BLOCKED, a composite command must not
    execute later effectful steps such as commit, push, PR creation, merge,
    handoff refresh, release, or publish. Explicit recovery steps may be
    allowlisted by the wrapper.
    """

    steps_tuple = tuple(steps)
    allowed = tuple(str(item) for item in allowed_recovery_actions)
    effectful = tuple(str(item) for item in effectful_actions)
    violations: list[CompositeShortCircuitViolation] = []

    first_failure: tuple[str, str] | None = None
    for step in steps_tuple:
        status = _status_of(getattr(step, "result", None))
        if status in TERMINAL_BAD_STATUSES:
            first_failure = (str(getattr(step, "name", "")), status)
            break

    if first_failure is None:
        return []

    failed_step_name, failed_status = first_failure
    failure_seen = False
    for step in steps_tuple:
        if not failure_seen:
            if str(getattr(step, "name", "")) == failed_step_name:
                failure_seen = True
            continue

        action = _action_of(step)
        if _is_allowed_recovery_step(action, allowed):
            continue
        if not _is_effectful_after_failure(action, effectful):
            continue

        violations.append(
            CompositeShortCircuitViolation(
                wrapper=wrapper,
                failed_step_name=failed_step_name,
                failed_step_status=failed_status,
                later_step_name=str(getattr(step, "name", "")),
                later_action=action,
                message=(
                    f"{wrapper} executed effectful step {getattr(step, 'name', '')!s} "
                    f"after {failed_step_name} returned {failed_status}."
                ),
            )
        )

    return violations


def assert_no_effectful_steps_after_required_failure(
    *,
    wrapper: str,
    steps: Iterable[StepLike],
    allowed_recovery_actions: Iterable[str] = (),
    effectful_actions: Iterable[str] = DEFAULT_EFFECTFUL_ACTIONS_AFTER_FAILURE,
) -> None:
    violations = validate_no_effectful_steps_after_required_failure(
        wrapper=wrapper,
        steps=steps,
        allowed_recovery_actions=allowed_recovery_actions,
        effectful_actions=effectful_actions,
    )
    if violations:
        raise AssertionError("; ".join(item.message for item in violations))
