"""Sequential deterministic slice runner.

The runner executes workflow steps only while the previous step has reached
a successful target state. Retryable and failing states stop the slice before
any dependent follow-up actions can create artificial cascading failures.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from agentic_project_kit.control_state import ControlStatus, StepResult


StepCallable = Callable[[], StepResult]


@dataclass(frozen=True)
class SliceStep:
    """Named workflow step."""

    name: str
    run: StepCallable


@dataclass(frozen=True)
class SliceRunResult:
    """Result of a sequential slice execution."""

    status: ControlStatus
    completed_steps: tuple[str, ...]
    stopped_at: str | None
    step_results: tuple[StepResult, ...]

    @property
    def is_success(self) -> bool:
        return self.status in {ControlStatus.PASS, ControlStatus.DONE, ControlStatus.NOOP}

    @property
    def is_retryable(self) -> bool:
        return self.status in {ControlStatus.PENDING, ControlStatus.WAIT}


def run_slice(steps: Sequence[SliceStep]) -> SliceRunResult:
    """Run steps sequentially and stop on retryable or failing outcomes."""
    completed: list[str] = []
    results: list[StepResult] = []

    for step in steps:
        result = step.run()
        results.append(result)

        if result.is_success:
            completed.append(step.name)
            continue

        return SliceRunResult(
            status=result.status,
            completed_steps=tuple(completed),
            stopped_at=step.name,
            step_results=tuple(results),
        )

    if not steps:
        status = ControlStatus.NOOP
    else:
        status = ControlStatus.PASS

    return SliceRunResult(
        status=status,
        completed_steps=tuple(completed),
        stopped_at=None,
        step_results=tuple(results),
    )
