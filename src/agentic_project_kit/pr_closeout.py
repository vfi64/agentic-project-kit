from __future__ import annotations

from dataclasses import dataclass
from typing import Any

READY_TO_MERGE = "READY_TO_MERGE"
BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class PrCloseoutResult:
    outcome: str
    reasons: tuple[str, ...]

def _check_success(entry: dict[str, Any]) -> bool:
    return entry.get("status") == "COMPLETED" and entry.get("conclusion") == "SUCCESS"

def evaluate_pr_closeout(pr: dict[str, Any], expected_check_names: tuple[str, ...] = ("test",)) -> PrCloseoutResult:
    reasons: list[str] = []
    if pr.get("state") != "OPEN":
        reasons.append("state is not OPEN")
    if pr.get("mergeStateStatus") != "CLEAN":
        reasons.append("mergeStateStatus is not CLEAN")
    if pr.get("mergeable") not in ("MERGEABLE", True):
        reasons.append("PR is not mergeable")
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        reasons.append("no status checks reported")
    names = {str(item.get("name", "")) for item in checks if isinstance(item, dict)}
    for expected in expected_check_names:
        if expected not in names:
            reasons.append(f"expected check missing: {expected}")
    for item in checks:
        if isinstance(item, dict) and not _check_success(item):
            name = item.get("name", "<unknown>")
            status = item.get("status", "<unknown>")
            conclusion = item.get("conclusion", "<unknown>")
            reasons.append(f"check not successful: {name} status={status} conclusion={conclusion}")
    if reasons:
        return PrCloseoutResult(BLOCKED, tuple(reasons))
    return PrCloseoutResult(READY_TO_MERGE, ("merge required; do not continue without merge or explicit block",))

def render_pr_closeout(result: PrCloseoutResult) -> str:
    lines = [f"PR closeout outcome: {result.outcome}"]
    for reason in result.reasons:
        lines.append(f"- {reason}")
    return "\n".join(lines)
