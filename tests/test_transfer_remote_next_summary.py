from __future__ import annotations

from types import SimpleNamespace

from agentic_project_kit.cli_commands.transfer import _echo_remote_next_user_summary


class FakeRuleAck:
    def as_json_data(self) -> dict[str, object]:
        return {
            "present": True,
            "confirmed": False,
            "head": "old1234",
            "blocking_reasons": ["stale_rule_ack"],
        }


def test_remote_next_summary_shows_local_state_rule_ack_and_blockers(capsys):
    result = SimpleNamespace(
        result_status="BLOCKED",
        returncode=2,
        reasons=("dirty_worktree",),
        post_report_actions={
            "committed": True,
            "pushed": False,
            "blocked_reason": "git_push_failed",
            "commit_head": "abc1234",
        },
        published_report_path="docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        report_path="docs/reports/transfer_runs/latest-remote-next-report.json",
        next_action="Inspect the published remote-next diagnostic report before retrying.",
        preflight={
            "current_branch": "feature/example",
            "dirty_state": {
                "clean": False,
                "staged_changes": ["docs/reports/command_runs/LATEST_COMMAND_RUN.txt"],
                "unstaged_changes": ["src/example.py"],
                "untracked_files": ["scratch.log"],
            },
        },
        branch="feature/example",
        head="abc1234",
        rule_ack=FakeRuleAck(),
        local_run=SimpleNamespace(state={}),
    )

    _echo_remote_next_user_summary(result)

    output = capsys.readouterr().out
    assert "TRANSFER_REMOTE_NEXT_DONE" in output
    assert "LOCAL_STATE:" in output
    assert "CLEAN:                  no" in output
    assert "BRANCH:                 feature/example" in output
    assert "STAGED:                 docs/reports/command_runs/LATEST_COMMAND_RUN.txt" in output
    assert "UNSTAGED:               src/example.py" in output
    assert "UNTRACKED:              scratch.log" in output
    assert "RULE_ACK:" in output
    assert "PRESENT:                yes" in output
    assert "CONFIRMED:              no" in output
    assert "BLOCKING_REASON:        stale_rule_ack" in output
    assert "BLOCKERS:" in output
    assert "REASON:                 dirty_worktree" in output
    assert "BLOCKED_REASON:         git_push_failed" in output
    assert "CHAT_REPLY:             g" in output

def test_remote_next_summary_shows_new_order_required_for_no_current_order(capsys):
    result = SimpleNamespace(
        result_status="BLOCKED",
        returncode=2,
        reasons=("no_current_transfer_order",),
        post_report_actions={
            "committed": True,
            "pushed": True,
            "commit_head": "abc1234",
        },
        published_report_path="docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        report_path="docs/reports/transfer_runs/latest-remote-next-report.json",
        next_action="Create or queue a fresh remote-next transfer order, then rerun the canonical command.",
        preflight={
            "current_branch": "main",
            "dirty_state": {
                "clean": True,
                "staged_changes": [],
                "unstaged_changes": [],
                "untracked_files": [],
            },
        },
        branch=None,
        head="abc1234",
        rule_ack=FakeRuleAck(),
        local_run=SimpleNamespace(state={}),
    )

    _echo_remote_next_user_summary(result)

    output = capsys.readouterr().out
    assert "STATE:                  NEW_ORDER_REQUIRED" in output
    assert "REASON:                 no_current_transfer_order" in output
    assert "NEXT:                   Create or queue a fresh remote-next transfer order, then rerun the canonical command." in output

