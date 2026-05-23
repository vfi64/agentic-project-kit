from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable

READY_TO_MERGE = "READY_TO_MERGE"
ALREADY_MERGED = "ALREADY_MERGED"
WAITING = "WAITING"
BLOCKED = "BLOCKED"
TIMEOUT = "TIMEOUT"
GH_ERROR = "GH_ERROR"

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


SnapshotProvider = Callable[[], dict[str, Any]]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


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


def wait_for_pr_readiness(
    snapshot_provider: SnapshotProvider,
    *,
    expected_head_sha: str | None = None,
    timeout_seconds: int = 2700,
    interval_seconds: int = 20,
    expected_checks: tuple[str, ...] = (),
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
) -> ReadinessDecision:
    start = clock()
    while True:
        elapsed = int(clock() - start)
        try:
            snapshot = snapshot_provider()
        except Exception as exc:
            return ReadinessDecision(GH_ERROR, (str(exc),), True)
        decision = classify_pr_readiness(
            snapshot,
            expected_head_sha=expected_head_sha,
            elapsed_seconds=elapsed,
            timeout_seconds=timeout_seconds,
            expected_checks=expected_checks,
        )
        if decision.terminal:
            return decision
        remaining = timeout_seconds - elapsed
        if remaining <= 0:
            return ReadinessDecision(TIMEOUT, ("timeout reached while waiting for CI",), True)
        sleep(min(interval_seconds, remaining))


def gh_pr_snapshot_provider(pr_number: int) -> SnapshotProvider:
    def provider() -> dict[str, Any]:
        completed = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "state,headRefOid,mergeStateStatus,mergeable,statusCheckRollup",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip() or "gh pr view failed"
            raise RuntimeError(details)
        return json.loads(completed.stdout)

    return provider


def render_pr_readiness(decision: ReadinessDecision) -> str:
    lines = [
        f"PR readiness outcome: {decision.outcome}",
        f"terminal={str(decision.terminal).lower()}",
        f"success={str(decision.success).lower()}",
    ]
    lines.extend(f"- {reason}" for reason in decision.reasons)
    return "\n".join(lines)
