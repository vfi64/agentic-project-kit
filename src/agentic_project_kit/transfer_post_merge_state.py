from __future__ import annotations

import re


READY_STATE = "READY"
NEEDS_HANDOFF_REFRESH_STATE = "NEEDS_HANDOFF_REFRESH"
NEEDS_SUCCESSOR_PACKAGE_REFRESH_STATE = "NEEDS_SUCCESSOR_PACKAGE_REFRESH"
BLOCKED_STATE = "BLOCKED"
CHECK_FAILED_STATE = "CHECK_FAILED"
UNKNOWN_STATE = "UNKNOWN"

REFRESHABLE_POST_MERGE_STATES = {
    NEEDS_HANDOFF_REFRESH_STATE,
    NEEDS_SUCCESSOR_PACKAGE_REFRESH_STATE,
}


def post_merge_state(result: object) -> str:
    """Classify a post-merge-check result without promoting failures to ready."""

    next_action = str(getattr(result, "next_action", "") or "")
    stdout = str(getattr(result, "stdout", "") or "")
    stderr = str(getattr(result, "stderr", "") or "")
    returncode = int(getattr(result, "returncode", 1) or 0)
    result_status = str(getattr(result, "result_status", "") or "")
    combined = f"{next_action}\n{stdout}\n{stderr}"

    state_lines = [
        match.group(1)
        for match in re.finditer(r"^STATE=([A-Z_]+)", combined, flags=re.MULTILINE)
    ]
    for state in state_lines:
        if state in REFRESHABLE_POST_MERGE_STATES:
            return state

    if "result=REFRESH_REQUIRED" in combined:
        return NEEDS_HANDOFF_REFRESH_STATE

    if BLOCKED_STATE in state_lines:
        return BLOCKED_STATE

    if READY_STATE in state_lines and returncode == 0 and result_status == "PASS":
        return READY_STATE

    if "result=NOOP" in combined and returncode == 0 and result_status == "PASS":
        return READY_STATE

    if returncode != 0 or result_status != "PASS":
        return CHECK_FAILED_STATE

    return UNKNOWN_STATE
