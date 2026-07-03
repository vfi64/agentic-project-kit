from __future__ import annotations

import subprocess
from types import SimpleNamespace

from agentic_project_kit.pr_closeout_complete import pr_closeout_complete
from agentic_project_kit.transfer_repo_actions import RepoActionResult


def test_pr_closeout_complete_resumes_when_pr_already_merged(monkeypatch) -> None:
    def fake_run(command, *, cwd=None):
        if command == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:2] == ["git", "switch"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == ["git", "pull", "--ff-only"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    monkeypatch.setattr("agentic_project_kit.pr_closeout_complete._run_command", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.pr_closeout_complete._load_pr_info",
        lambda after_pr: (
            {
                "number": after_pr,
                "merged": True,
                "headRefOid": "a" * 40,
                "state": "MERGED",
            },
            subprocess.CompletedProcess(["gh"], 0, "{}", ""),
        ),
    )
    monkeypatch.setattr(
        "agentic_project_kit.pr_closeout_complete.post_merge_complete",
        lambda *args, **kwargs: SimpleNamespace(
            result_status="PASS",
            returncode=0,
            lifecycle_state="NOOP",
            refresh_pr=None,
            next_action="done",
            as_json_data=lambda: {"result_status": "PASS", "returncode": 0},
        ),
    )
    monkeypatch.setattr(
        "agentic_project_kit.pr_closeout_complete.repo_status",
        lambda: RepoActionResult(
            action="repo-status",
            result_status="PASS",
            returncode=0,
            command=["git", "status", "--short"],
            stdout="",
            stderr="",
            next_action="clean",
        ),
    )

    result = pr_closeout_complete(1683)

    assert result.result_status == "PASS"
    assert result.lifecycle_state == "COMPLETE"
    assert result.merged_pr is True
    assert [step.name for step in result.steps] == [
        "local-clean-preflight",
        "switch-main",
        "sync-main-before-pr-closeout",
        "pr-state-lookup",
        "post-merge-complete",
        "repo-status",
    ]
