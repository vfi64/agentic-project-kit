from __future__ import annotations

from agentic_project_kit.transfer_post_merge_settle import post_merge_settle
from agentic_project_kit.transfer_repo_actions import RepoActionResult

TARGET = "agentic_project_kit.transfer_post_merge_settle"


def _result(
    action: str,
    stdout: str,
    *,
    returncode: int = 0,
    next_action: str = "",
) -> RepoActionResult:
    return RepoActionResult(
        action=action,
        result_status="PASS" if returncode == 0 else "FAIL",
        returncode=returncode,
        command=[action],
        stdout=stdout,
        stderr="",
        next_action=next_action,
    )


def _patch_common_pr_steps(monkeypatch, calls: list[str]) -> None:
    def fake_wait(pr_number: int, **_kwargs):
        calls.append(f"wait:{pr_number}")
        return _result("pr-wait-ci", "ci green\n")

    def fake_merge(pr_number: int, **_kwargs):
        calls.append(f"merge:{pr_number}")
        return _result("pr-merge-safe", "merged\n")

    def fake_pull(**_kwargs):
        calls.append("pull")
        return _result("pull-current", "Already up to date.\n")

    monkeypatch.setattr(f"{TARGET}.pr_wait_ci", fake_wait)
    monkeypatch.setattr(f"{TARGET}.pr_merge_safe", fake_merge)
    monkeypatch.setattr(f"{TARGET}.pull_current", fake_pull)


def test_post_merge_settle_ready_stops_without_refresh(monkeypatch):
    calls: list[str] = []

    def fake_post_merge_check(**_kwargs):
        calls.append("check")
        return _result("post-merge-check", "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.successor_package_refresh_pr", lambda *_args, **_kwargs: calls.append("successor"))
    monkeypatch.setattr(f"{TARGET}.admin_refresh_pr", lambda *_args, **_kwargs: calls.append("handoff"))

    result = post_merge_settle(1878)

    assert result.result_status == "PASS"
    assert result.lifecycle_state == "READY"
    assert result.refresh_prs == ()
    assert result.refresh_kinds == ()
    assert [step.name for step in result.steps] == ["initial-post-merge-check"]
    assert calls == ["check"]


def test_post_merge_settle_treats_legacy_blocked_refresh_as_handoff_refresh(monkeypatch):
    post_merge_states = iter(
        [
            (
                "POST_MERGE_HANDOFF_REFRESH\n"
                "current_head=63c3a6eb\n"
                "freshness_warning_present=True\n"
                "refresh_required=True\n"
                "result=REFRESH_REQUIRED\n"
                "next_safe_action=create_administrative_handoff_refresh\n",
                "STATE=BLOCKED; NEXT=diagnose_handoff_refresh_status",
                1,
            ),
            ("POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", "", 0),
        ]
    )
    calls: list[str] = []
    _patch_common_pr_steps(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("check")
        stdout, next_action, returncode = next(post_merge_states)
        return _result("post-merge-check", stdout, returncode=returncode, next_action=next_action)

    def fake_handoff(after_pr: int, **_kwargs):
        calls.append(f"handoff:{after_pr}")
        return _result("admin-refresh-pr", "existing_pr=1883\n")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.admin_refresh_pr", fake_handoff)

    result = post_merge_settle(1882)

    assert result.result_status == "PASS"
    assert result.lifecycle_state == "COMPLETE"
    assert result.refresh_prs == (1883,)
    assert result.refresh_kinds == ("handoff-refresh",)
    assert calls == ["check", "handoff:1882", "wait:1883", "merge:1883", "pull", "check"]


def test_post_merge_settle_runs_successor_then_handoff_refresh(monkeypatch):
    post_merge_states = iter(
        [
            ("", "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package"),
            ("POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n", ""),
            ("POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", ""),
        ]
    )
    calls: list[str] = []
    _patch_common_pr_steps(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("check")
        stdout, next_action = next(post_merge_states)
        return _result("post-merge-check", stdout, next_action=next_action)

    def fake_successor(after_pr: int, **_kwargs):
        calls.append(f"successor:{after_pr}")
        return _result("successor-package-refresh-pr", "https://github.test/repo/pull/1880\n")

    def fake_handoff(after_pr: int, **_kwargs):
        calls.append(f"handoff:{after_pr}")
        return _result("admin-refresh-pr", "existing_pr=1881\n")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.successor_package_refresh_pr", fake_successor)
    monkeypatch.setattr(f"{TARGET}.admin_refresh_pr", fake_handoff)

    result = post_merge_settle(1878, ci_timeout_seconds=1, ci_poll_seconds=1)

    assert result.result_status == "PASS"
    assert result.lifecycle_state == "COMPLETE"
    assert result.refresh_prs == (1880, 1881)
    assert result.refresh_kinds == ("successor-package-refresh", "handoff-refresh")
    assert result.refresh_loop_detected is False
    assert calls == [
        "check",
        "successor:1878",
        "wait:1880",
        "merge:1880",
        "pull",
        "check",
        "handoff:1880",
        "wait:1881",
        "merge:1881",
        "pull",
        "check",
    ]


def test_post_merge_settle_blocks_repeated_refresh_kind(monkeypatch):
    post_merge_states = iter(
        [
            ("", "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package"),
            ("", "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package"),
        ]
    )
    calls: list[str] = []
    _patch_common_pr_steps(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("check")
        stdout, next_action = next(post_merge_states)
        return _result("post-merge-check", stdout, next_action=next_action)

    def fake_successor(after_pr: int, **_kwargs):
        calls.append(f"successor:{after_pr}")
        return _result("successor-package-refresh-pr", "existing_pr=1880\n")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.successor_package_refresh_pr", fake_successor)

    result = post_merge_settle(1878)

    assert result.result_status == "BLOCKED"
    assert result.lifecycle_state == "REFRESH_LOOP_DETECTED"
    assert result.refresh_loop_detected is True
    assert result.refresh_prs == (1880,)
    assert calls == ["check", "successor:1878", "wait:1880", "merge:1880", "pull", "check"]


def test_post_merge_settle_blocks_when_refresh_limit_reached(monkeypatch):
    post_merge_states = iter(
        [
            ("", "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package"),
            ("POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n", ""),
        ]
    )
    calls: list[str] = []
    _patch_common_pr_steps(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("check")
        stdout, next_action = next(post_merge_states)
        return _result("post-merge-check", stdout, next_action=next_action)

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(
        f"{TARGET}.successor_package_refresh_pr",
        lambda after_pr, **_kwargs: _result("successor-package-refresh-pr", "existing_pr=1880\n"),
    )

    result = post_merge_settle(1878, refresh_limit=1)

    assert result.result_status == "BLOCKED"
    assert result.lifecycle_state == "REFRESH_LIMIT_EXCEEDED"
    assert result.refresh_prs == (1880,)
    assert result.refresh_loop_detected is True
