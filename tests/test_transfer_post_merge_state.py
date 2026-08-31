from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.transfer_post_merge_state import (
    CHECK_FAILED_STATE,
    NEEDS_HANDOFF_REFRESH_STATE,
    NEEDS_SUCCESSOR_PACKAGE_REFRESH_STATE,
    READY_STATE,
    post_merge_state,
)


@dataclass(frozen=True)
class Result:
    stdout: str = ""
    stderr: str = ""
    next_action: str = ""
    result_status: str = "PASS"
    returncode: int = 0


def test_post_merge_state_requires_successful_noop_before_ready() -> None:
    result = Result(
        stdout="POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        result_status="FAIL",
        returncode=1,
    )

    assert post_merge_state(result) == CHECK_FAILED_STATE


def test_post_merge_state_accepts_successor_package_refresh_state_from_next_action() -> None:
    result = Result(
        stdout="POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        next_action="STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package",
        result_status="FAIL",
        returncode=1,
    )

    assert post_merge_state(result) == NEEDS_SUCCESSOR_PACKAGE_REFRESH_STATE


def test_post_merge_state_accepts_legacy_refresh_required_before_blocked_state() -> None:
    result = Result(
        stdout="POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
        next_action="STATE=BLOCKED; NEXT=diagnose_handoff_refresh_status",
        result_status="FAIL",
        returncode=1,
    )

    assert post_merge_state(result) == NEEDS_HANDOFF_REFRESH_STATE


def test_post_merge_state_accepts_successful_ready_state() -> None:
    result = Result(
        stdout="POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        next_action="STATE=READY\nNEXT=none",
    )

    assert post_merge_state(result) == READY_STATE
