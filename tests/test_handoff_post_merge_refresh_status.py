from __future__ import annotations



def test_post_merge_refresh_status_treats_refresh_only_head_as_fresh(monkeypatch):
    import subprocess
    from typer.testing import CliRunner

    from agentic_project_kit.cli_commands.handoff import handoff_app

    class Status:
        result = "POST_MERGE_HANDOFF_REFRESH"
        current_head = "45851407"
        latest_successor_prompt = "docs/reports/terminal/post-pr1281-successor-chat-handoff.md"
        latest_successor_prompt_commit = "old1234"
        latest_successor_prompt_fresh_for_head = False
        freshness_warning_present = True
        refresh_required = True
        next_safe_action = "run_prepare_successor_handoff"

    def fake_check_status(*args, **kwargs):
        return Status()

    def fake_run(argv, **kwargs):
        assert argv == ["git", "log", "-1", "--pretty=%s"]
        return subprocess.CompletedProcess(
            argv,
            0,
            "Refresh successor handoff after PR1281 (#1282)\n",
            "",
        )

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.handoff.evaluate_post_merge_handoff_refresh",
        fake_check_status,
    )
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.handoff.subprocess.run",
        fake_run,
    )

    result = CliRunner().invoke(handoff_app, ["post-merge-refresh-status"])

    assert result.exit_code == 0
    assert "refresh_only_merge_commit_is_fresh=True" in result.stdout
    assert "result=NOOP" in result.stdout
