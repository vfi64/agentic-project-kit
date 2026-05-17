"""Deterministic workflow control states.

This module separates command execution results from target-state outcomes.
A workflow step may be successful because the desired target state already
exists, even if a low-level command would otherwise fail or be unnecessary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControlStatus(str, Enum):
    """Machine-readable status values for deterministic workflow steps."""

    PASS = "PASS"
    DONE = "DONE"
    NOOP = "NOOP"
    ALREADY_ON_MAIN = "ALREADY_ON_MAIN"
    ALREADY_MERGED = "ALREADY_MERGED"
    ALREADY_RELEASED = "ALREADY_RELEASED"
    DOI_VERIFIED = "DOI_VERIFIED"
    SUPERSEDED = "SUPERSEDED"
    PENDING = "PENDING"
    WAIT = "WAIT"
    FAIL = "FAIL"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


SUCCESS_STATUSES = frozenset({
    ControlStatus.PASS,
    ControlStatus.DONE,
    ControlStatus.NOOP,
    ControlStatus.ALREADY_ON_MAIN,
    ControlStatus.ALREADY_MERGED,
    ControlStatus.ALREADY_RELEASED,
    ControlStatus.DOI_VERIFIED,
    ControlStatus.SUPERSEDED,
})

RETRYABLE_STATUSES = frozenset({
    ControlStatus.PENDING,
    ControlStatus.WAIT,
})

FAILURE_STATUSES = frozenset({
    ControlStatus.FAIL,
    ControlStatus.NEEDS_HUMAN_REVIEW,
})


@dataclass(frozen=True)
class StepResult:
    """Result of a workflow step after target-state classification."""

    status: ControlStatus
    message: str
    detail: str = ""

    @property
    def is_success(self) -> bool:
        return self.status in SUCCESS_STATUSES

    @property
    def is_retryable(self) -> bool:
        return self.status in RETRYABLE_STATUSES

    @property
    def is_failure(self) -> bool:
        return self.status in FAILURE_STATUSES

    @property
    def should_continue(self) -> bool:
        return self.is_success


def normalize_status(value: str | ControlStatus) -> ControlStatus:
    """Return a ControlStatus from a user/tool supplied value."""
    if isinstance(value, ControlStatus):
        return value
    normalized = value.strip().upper().replace("-", "_")
    return ControlStatus(normalized)
