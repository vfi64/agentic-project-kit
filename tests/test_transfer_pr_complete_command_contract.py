from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def test_transfer_pr_complete_command_is_registered_in_source() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    assert '@transfer_app.command("pr-complete")' in text
    assert "transfer_pr_complete_result" in text
    assert "TRANSFER_PR_COMPLETE" in text


def test_transfer_pr_complete_stub_blocks_until_orchestration_slice() -> None:
    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-complete",
            "123",
            "--expected-head-sha",
            "0123456789abcdef0123456789abcdef01234567",
        ],
    )
    assert result.exit_code == 2
    assert "TRANSFER_PR_COMPLETE" in result.stdout
    assert "STATE:                 BLOCKED" in result.stdout
    assert "Implement pr-complete orchestration" in result.stdout
