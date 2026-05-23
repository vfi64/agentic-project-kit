from __future__ import annotations

from dataclasses import dataclass
from typing import Any

READY_TO_MERGE = "READY_TO_MERGE"
ALREADY_MERGED = "ALREADY_MERGED"
WAITING = "WAITING"
BLOCKED = "BLOCKED"
TIMEOUT = "TIMEOUT"

SUCCESS_OUTCOMES = {READY_TO_MERGE, ALREADY_MERGED}
FAILED_CONCLUSIONS = {
    "ACTION_REQUIRED",
    "CANCELLED",
    "FAILURE",
    "STARTUP_FAILURE",
    "STALE",
    "TIMED_OUT",
}
SUCCESS_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}


@dataclass(frozen=True)
class ReadinessDecision:
    outcome: str
    reasons: tuple[str, ...]
    terminal: bool

    @property
    def success(self) -> bool:
        return self.outcome in SUCCESS_OUTCOMES


def normalize_status_checks(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    raw = snapshot.get("statusCheckRollup") or []
    if isinstance(raw, dict):
        raw = raw.get("nodes") or raw.get("edges") or []
    checks: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("node"), dict):
            item = item["node"]
        checks.append(
            {
                "name": str(item.get("name") or item.get("context") or ""),
                "status": str(item.get("status") or item.get("state") or "").upper(),
                "conclusion": str(item.get("conclusion") or "").upper(),
            }
        )
    return checks


def classify_pr_readiness(
    snapshot: dict[str, Any],
    *,
    expected_head_sha: str | None = None,
    elapsed_seconds: int = 0,
    timeout_seconds: int = 2700,
    expected_checks: tuple[str, ...] = (),
) -> ReadinessDecision:
    if elapsed_seconds >= timeout_seconds:
        return ReadinessDecision(
            TIMEOUT,
            (f"timeout reached after {elapsed_seconds}s",),
            True,
        )

    actual_head_sha = str(
        snapshot.get("headRefOid") or snapshot.get("headSha") or snapshot.get("head_sha") or ""
    )
    if expected_head_sha and actual_head_sha and actual_head_sha != expected_head_sha:
        return ReadinessDecision(
            BLOCKED,
            (f"head SHA changed: expected {expected_head_sha}, got {actual_head_sha}",),
            True,
        )

    state = str(snapshot.get("state") or "").upper()
    checks = normalize_status_checks(snapshot)
    successful = [
        check
        for check in checks
        if check["status"] == "COMPLETED" and check["conclusion"] in SUCCESS_CONCLUSIONS
    ]

    if state == "MERGED" and checks and len(successful) == len(checks):
        return ReadinessDecision(ALREADY_MERGED, (), True)

    if state != "OPEN":
        return ReadinessDecision(BLOCKED, (f"PR state is not OPEN: {state or '<unknown>'}",), True)

    if not checks:
        return ReadinessDecision(WAITING, ("no status checks reported yet",), False)

    names = {check["name"] for check in checks}
    missing = tuple(name for name in expected_checks if name and name not in names)
    if missing:
        return ReadinessDecision(
            WAITING,
            tuple(f"expected check missing: {name}" for name in missing),
            False,
        )

    failed = [check for check in checks if check["conclusion"] in FAILED_CONCLUSIONS]
    if failed:
        return ReadinessDecision(
            BLOCKED,
            tuple(f"check failed: {check['name'] or '<unknown>'}" for check in failed),
            True,
        )

    pending = [check for check in checks if check not in successful]
    if pending:
        return ReadinessDecision(
            WAITING,
            tuple(f"check pending: {check['name'] or '<unknown>'}" for check in pending),
            False,
        )

    merge_state = str(snapshot.get("mergeStateStatus") or "").upper()
    mergeable = snapshot.get("mergeable")
    if merge_state != "CLEAN":
        return ReadinessDecision(
            BLOCKED,
            (f"mergeStateStatus is not CLEAN: {merge_state or '<unknown>'}",),
            True,
        )
    if mergeable not in (True, "MERGEABLE", "mergeable"):
        return ReadinessDecision(BLOCKED, (f"PR is not mergeable: {mergeable!r}",), True)

    return ReadinessDecision(
        READY_TO_MERGE,
        ("all required checks passed and merge state is clean",),
        True,
    )
