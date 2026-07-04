from pathlib import Path


def test_pr_create_complete_runs_restore_known_volatile_after_pr_complete() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py").read_text(encoding="utf-8")

    assert '"restore-known-volatile-after-pr-complete"' in text
    assert '[agentic_kit, "transfer", "restore-known-volatile", "--json"]' in text


def test_pr_create_complete_runs_restore_known_volatile_after_post_merge_followup() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py").read_text(encoding="utf-8")

    assert '"restore-known-volatile-after-post-merge-followup"' in text
    assert text.count('"restore-known-volatile"') >= 2
