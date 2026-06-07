from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def test_transfer_pr_complete_command_is_registered_in_source() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    assert '@transfer_app.command("pr-complete")' in text
    assert "transfer_pr_complete_result" in text
    assert "TRANSFER_PR_COMPLETE" in text
    assert '"pr-wait-ci"' in text
    assert '"pr-merge-safe"' in text
    assert '"post-merge-complete"' in text
    assert '"rules", "acknowledge"' in text


def test_transfer_pr_complete_orchestrates_wait_merge_sync_ack_and_post_merge(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *, text=False, capture_output=False):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-complete",
            "123",
            "--expected-head-sha",
            "0123456789abcdef0123456789abcdef01234567",
            "--merge-method",
            "squash",
        ],
    )

    assert result.exit_code == 0
    assert "TRANSFER_PR_COMPLETE" in result.stdout
    assert "STATE:" in result.stdout
    assert "PASS" in result.stdout
    assert [call[:3] for call in calls[:2]] == [
        ["./.venv/bin/agentic-kit", "transfer", "pr-wait-ci"],
        ["./.venv/bin/agentic-kit", "transfer", "pr-merge-safe"],
    ]
    assert calls[2] == ["git", "switch", "main"]
    assert calls[3] == ["git", "pull", "--ff-only", "origin", "main"]
    assert calls[4] == ["./.venv/bin/agentic-kit", "rules", "acknowledge"]
    assert calls[5] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-complete", "--after-pr", "123"]


def test_transfer_pr_complete_blocks_on_first_failed_step(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *, text=False, capture_output=False):
        calls.append(list(argv))
        returncode = 1 if "pr-merge-safe" in argv else 0
        return subprocess.CompletedProcess(argv, returncode, "out\n", "err\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

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
    assert "STATE:" in result.stdout
    assert "BLOCKED" in result.stdout
    assert "FAILED_STEP:" in result.stdout
    assert "pr-merge-safe" in result.stdout
    assert len(calls) == 2
