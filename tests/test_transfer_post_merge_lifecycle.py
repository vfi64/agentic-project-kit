from __future__ import annotations

from agentic_project_kit.transfer_post_merge_lifecycle import post_merge_complete
from agentic_project_kit.transfer_repo_actions import RepoActionResult

TARGET = "agentic_project_kit.transfer_post_merge_lifecycle"


def _result(action: str, stdout: str, *, returncode: int = 0) -> RepoActionResult:
    return RepoActionResult(
        action=action,
        result_status="PASS" if returncode == 0 else "FAIL",
        returncode=returncode,
        command=[action],
        stdout=stdout,
        stderr="",
        next_action="next",
    )


def _patch_successful_pull(monkeypatch, calls: list[str] | None = None) -> None:
    def fake_pull_current(**_kwargs):
        if calls is not None:
            calls.append("pull_current")
        return _result("pull-current", "Already up to date.\n")

    monkeypatch.setattr(f"{TARGET}.pull_current", fake_pull_current)


def test_post_merge_complete_noop_stops_without_refresh(monkeypatch):
    calls: list[str] = []

    def fake_post_merge_check(**_kwargs):
        calls.append("post_merge_check")
        return _result(
            "post-merge-check",
            "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        )

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)

    result = post_merge_complete(1083)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.lifecycle_state == "NOOP"
    assert [step.name for step in result.steps] == ["initial-post-merge-check"]
    assert calls == ["post_merge_check"]


def test_post_merge_complete_treats_refresh_required_output_as_lifecycle_state_even_on_nonzero_returncode(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        ]
    )
    calls: list[str] = []
    _patch_successful_pull(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("post_merge_check")
        return _result(
            "post-merge-check",
            next(post_merge_outputs),
            returncode=1,
        )

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result(
            "admin-refresh-pr",
            "existing_pr=1092\n",
        ),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result("pr-merge-safe", "merged\n"),
    )

    result = post_merge_complete(1084)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.lifecycle_state == "COMPLETE"
    assert result.refresh_pr == 1092
    assert calls == ["post_merge_check", "pull_current", "post_merge_check"]


def test_post_merge_complete_refresh_required_completes_after_one_refresh(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        ]
    )
    calls: list[str] = []
    _patch_successful_pull(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("post_merge_check")
        return _result("post-merge-check", next(post_merge_outputs))

    def fake_admin_refresh_pr(after_pr, **_kwargs):
        calls.append(f"admin_refresh_pr:{after_pr}")
        return _result(
            "admin-refresh-pr",
            "https://github.com/vfi64/agentic-project-kit/pull/1090\n",
        )

    def fake_pr_wait_ci(pr_number, **_kwargs):
        calls.append(f"pr_wait_ci:{pr_number}")
        return _result("pr-wait-ci", "ci green\n")

    def fake_pr_merge_safe(pr_number, **_kwargs):
        calls.append(f"pr_merge_safe:{pr_number}")
        return _result("pr-merge-safe", "merged\n")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.admin_refresh_pr", fake_admin_refresh_pr)
    monkeypatch.setattr(f"{TARGET}.pr_wait_ci", fake_pr_wait_ci)
    monkeypatch.setattr(f"{TARGET}.pr_merge_safe", fake_pr_merge_safe)

    result = post_merge_complete(1083)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.lifecycle_state == "COMPLETE"
    assert result.refresh_pr == 1090
    assert result.refresh_loop_detected is False
    assert [step.name for step in result.steps] == [
        "initial-post-merge-check",
        "admin-refresh-pr",
        "admin-refresh-pr-wait-ci",
        "admin-refresh-pr-merge-safe",
        "final-main-sync",
        "final-post-merge-check",
    ]
    assert calls == [
        "post_merge_check",
        "admin_refresh_pr:1083",
        "pr_wait_ci:1090",
        "pr_merge_safe:1090",
        "pull_current",
        "post_merge_check",
    ]


def test_post_merge_complete_recovers_when_merge_step_blocks_but_final_check_is_noop(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
        ]
    )
    calls: list[str] = []
    _patch_successful_pull(monkeypatch, calls)

    def fake_post_merge_check(**_kwargs):
        calls.append("post_merge_check")
        return _result("post-merge-check", next(post_merge_outputs))

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result("admin-refresh-pr", "existing_pr=1086\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result(
            "pr-merge-safe",
            "merge evidence unavailable after remote merge\n",
            returncode=1,
        ),
    )

    result = post_merge_complete(1084)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.lifecycle_state == "COMPLETE"
    assert result.refresh_pr == 1086
    assert result.refresh_loop_detected is False
    assert [step.name for step in result.steps] == [
        "initial-post-merge-check",
        "admin-refresh-pr",
        "admin-refresh-pr-wait-ci",
        "admin-refresh-pr-merge-safe",
        "merge-block-recovery-main-sync",
        "merge-block-recovery-post-merge-check",
    ]
    assert "recovery" in result.next_action
    assert calls == ["post_merge_check", "pull_current", "post_merge_check"]


def test_post_merge_complete_blocks_when_final_main_sync_fails(monkeypatch):
    def fake_pull_current(**_kwargs):
        return _result("pull-current", "fast-forward rejected\n", returncode=1)

    monkeypatch.setattr(
        f"{TARGET}.post_merge_check",
        lambda **_kwargs: _result(
            "post-merge-check",
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
        ),
    )
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result("admin-refresh-pr", "existing_pr=1086\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result("pr-merge-safe", "merged\n"),
    )
    monkeypatch.setattr(f"{TARGET}.pull_current", fake_pull_current)

    result = post_merge_complete(1084)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.lifecycle_state == "FINAL_MAIN_SYNC_BLOCKED"
    assert result.refresh_pr == 1086
    assert [step.name for step in result.steps][-1] == "final-main-sync"


def test_post_merge_complete_does_not_hide_merge_block_when_recovery_check_fails(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=STRANGE\n",
        ]
    )
    _patch_successful_pull(monkeypatch)

    monkeypatch.setattr(
        f"{TARGET}.post_merge_check",
        lambda **_kwargs: _result("post-merge-check", next(post_merge_outputs)),
    )
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result("admin-refresh-pr", "existing_pr=1086\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result("pr-merge-safe", "blocked\n", returncode=1),
    )

    result = post_merge_complete(1084)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.lifecycle_state == "ADMIN_REFRESH_MERGE_BLOCKED"
    assert result.refresh_pr == 1086
    assert [step.name for step in result.steps] == [
        "initial-post-merge-check",
        "admin-refresh-pr",
        "admin-refresh-pr-wait-ci",
        "admin-refresh-pr-merge-safe",
        "merge-block-recovery-main-sync",
        "merge-block-recovery-post-merge-check",
    ]


def test_post_merge_complete_stops_on_refresh_loop(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
        ]
    )
    _patch_successful_pull(monkeypatch)

    def fake_post_merge_check(**_kwargs):
        return _result("post-merge-check", next(post_merge_outputs))

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result("admin-refresh-pr", "existing_pr=1091\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result("pr-merge-safe", "merged\n"),
    )

    result = post_merge_complete(1083)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.lifecycle_state == "REFRESH_LOOP_DETECTED"
    assert result.refresh_pr == 1091
    assert result.refresh_loop_detected is True
    assert "Stop" in result.next_action


def test_post_merge_complete_stops_on_refresh_loop_after_merge_block_recovery(monkeypatch):
    post_merge_outputs = iter(
        [
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
        ]
    )
    _patch_successful_pull(monkeypatch)

    monkeypatch.setattr(
        f"{TARGET}.post_merge_check",
        lambda **_kwargs: _result("post-merge-check", next(post_merge_outputs)),
    )
    monkeypatch.setattr(
        f"{TARGET}.admin_refresh_pr",
        lambda _after_pr, **_kwargs: _result("admin-refresh-pr", "existing_pr=1091\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_wait_ci",
        lambda _pr_number, **_kwargs: _result("pr-wait-ci", "ci green\n"),
    )
    monkeypatch.setattr(
        f"{TARGET}.pr_merge_safe",
        lambda _pr_number, **_kwargs: _result("pr-merge-safe", "blocked\n", returncode=1),
    )

    result = post_merge_complete(1083)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.lifecycle_state == "REFRESH_LOOP_DETECTED"
    assert result.refresh_pr == 1091
    assert result.refresh_loop_detected is True
    assert [step.name for step in result.steps][-1] == "merge-block-recovery-post-merge-check"


def test_post_merge_complete_stops_without_chained_refresh_for_refresh_only_pr(monkeypatch):
    calls: list[str] = []

    def fake_post_merge_check(**_kwargs):
        calls.append("post_merge_check")
        return _result(
            "post-merge-check",
            "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n",
        )

    def fake_admin_refresh_pr(after_pr, **_kwargs):
        calls.append(f"admin_refresh_pr:{after_pr}")
        return _result(
            "admin-refresh-pr",
            "NOOP: PR #1546 is already a refresh-only handoff PR; skipping chained admin refresh.\n",
        )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("refresh-only PR must not start CI wait or merge")

    monkeypatch.setattr(f"{TARGET}.post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(f"{TARGET}.admin_refresh_pr", fake_admin_refresh_pr)
    monkeypatch.setattr(f"{TARGET}.pr_wait_ci", fail_if_called)
    monkeypatch.setattr(f"{TARGET}.pr_merge_safe", fail_if_called)

    result = post_merge_complete(1546)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.lifecycle_state == "REFRESH_ONLY_PR_NOOP"
    assert result.refresh_pr is None
    assert [step.name for step in result.steps] == [
        "initial-post-merge-check",
        "admin-refresh-pr",
    ]
    assert calls == ["post_merge_check", "admin_refresh_pr:1546"]


def test_post_merge_complete_blocks_unknown_initial_state(monkeypatch):
    monkeypatch.setattr(
        f"{TARGET}.post_merge_check",
        lambda **_kwargs: _result(
            "post-merge-check",
            "POST_MERGE_HANDOFF_REFRESH\nresult=STRANGE\n",
        ),
    )

    result = post_merge_complete(1083)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.lifecycle_state == "UNKNOWN"
    assert [step.name for step in result.steps] == ["initial-post-merge-check"]


def test_post_merge_complete_blocks_when_initial_check_failed_even_if_output_says_noop(monkeypatch):
    from agentic_project_kit.transfer_post_merge_lifecycle import post_merge_complete
    from agentic_project_kit.transfer_repo_actions import RepoActionResult

    failing = RepoActionResult(
        action="post-merge-check",
        result_status="FAIL",
        returncode=1,
        command=["agentic-kit", "handoff", "post-merge-refresh-status"],
        stdout=(
            "POST_MERGE_HANDOFF_REFRESH\n"
            "refresh_required=False\n"
            "result=NOOP\n"
            "validation_report.json generated_head does not match HEAD or refresh-only ancestry\n"
        ),
        stderr="",
        next_action="STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package",
    )

    monkeypatch.setattr(
        "agentic_project_kit.transfer_post_merge_lifecycle.post_merge_check",
        lambda main_branch="main": failing,
    )

    result = post_merge_complete(after_pr=1687, ci_timeout_seconds=1, ci_poll_seconds=1)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 1
    assert result.lifecycle_state == "INITIAL_POST_MERGE_CHECK_FAILED"
    assert "NEEDS_SUCCESSOR_PACKAGE_REFRESH" in result.next_action
    assert "Post-merge lifecycle is complete" not in result.next_action
