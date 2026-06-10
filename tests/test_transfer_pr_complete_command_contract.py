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

    def fake_run(argv, *args, **kwargs):
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
            "--skip-llm-context-gate",
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
    assert "--skip-llm-context-gate" not in calls[0]
    assert "--skip-llm-context-gate" in calls[1]
    assert calls[2] == ["git", "switch", "main"]
    assert calls[3] == ["git", "pull", "--ff-only", "origin", "main"]
    assert calls[4] == ["./.venv/bin/agentic-kit", "rules", "acknowledge"]
    assert calls[5] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-complete", "--after-pr", "123"]


def test_transfer_pr_complete_blocks_on_first_failed_step(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
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
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 2
    assert "STATE:" in result.stdout
    assert "BLOCKED" in result.stdout
    assert "FAILED_STEP:" in result.stdout
    assert "pr-merge-safe" in result.stdout
    assert len(calls) == 2


def test_transfer_pr_create_complete_orchestrates_create_and_complete(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "0123456789abcdef0123456789abcdef01234567\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"stdout":"https://github.com/vfi64/agentic-project-kit/pull/123\\n"}\n',
                "",
            )
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-complete"]:
            return subprocess.CompletedProcess(command, 0, "completed\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create-complete",
            "--title",
            "Demo",
            "--body",
            "Body",
            "--base",
            "main",
            "--head",
            "current",
            "--merge-method",
            "squash",
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 0
    assert "TRANSFER_PR_CREATE_COMPLETE" in result.stdout
    assert "PR:" in result.stdout
    assert "123" in result.stdout
    assert calls[0] == ["git", "branch", "--show-current"]
    assert calls[1] == ["git", "rev-parse", "HEAD"]
    assert calls[2][:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create"]
    assert calls[3][:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-complete"]
    assert "123" in calls[3]
    assert "0123456789abcdef0123456789abcdef01234567" in calls[3]


def test_transfer_pr_create_complete_uses_existing_pr_when_create_fails(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "0123456789abcdef0123456789abcdef01234567\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create"]:
            return subprocess.CompletedProcess(command, 1, "", "already exists\n")
        if command[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(command, 0, "456\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-complete"]:
            return subprocess.CompletedProcess(command, 0, "completed\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create-complete",
            "--title",
            "Demo",
            "--body",
            "Body",
            "--base",
            "main",
            "--head",
            "current",
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 0
    assert "TRANSFER_PR_CREATE_COMPLETE" in result.stdout
    assert "456" in result.stdout
    assert any(call[:3] == ["gh", "pr", "view"] for call in calls)
    assert calls[-1][:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-complete"]
    assert "456" in calls[-1]


def test_transfer_pr_create_complete_post_merge_complete_uses_concrete_pr_number(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "0123456789abcdef0123456789abcdef01234567\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"stdout":"https://github.com/vfi64/agentic-project-kit/pull/789\\n"}\n',
                "",
            )
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-complete"]:
            return subprocess.CompletedProcess(command, 0, "completed\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "sync-main"]:
            return subprocess.CompletedProcess(command, 0, "synced\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-complete"]:
            return subprocess.CompletedProcess(command, 0, "post merge\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"]:
            return subprocess.CompletedProcess(command, 0, "checked\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "repo-status"]:
            return subprocess.CompletedProcess(command, 0, "clean\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create-complete",
            "--title",
            "Demo",
            "--body",
            "Body",
            "--base",
            "main",
            "--head",
            "current",
            "--merge-method",
            "squash",
            "--post-merge-complete",
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 0
    assert "789" in result.stdout
    assert any(
        call == [
            "./.venv/bin/agentic-kit",
            "transfer",
            "post-merge-complete",
            "--after-pr",
            "789",
        ]
        for call in calls
    )
    assert not any("PR_NUMMER" in " ".join(call) for call in calls)
    assert not any("<" in " ".join(call) or ">" in " ".join(call) for call in calls)

def test_transfer_pr_complete_continues_when_wait_ci_blocks_but_pr_status_is_green(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-wait-ci"]:
            return subprocess.CompletedProcess(command, 2, "wait blocked\n", "wait failed\n")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-status"]:
            return subprocess.CompletedProcess(
                command,
                0,
                "NEXT_TURN_PR_STATUS\n"
                "pr=123\n"
                "state=OPEN\n"
                "merge_state_status=CLEAN\n"
                "head_ref_oid=0123456789abcdef0123456789abcdef01234567\n"
                "decision=green\n",
                "",
            )
        return subprocess.CompletedProcess(command, 0, "ok\n", "")

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
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 0
    assert "TRANSFER_PR_COMPLETE" in result.stdout
    assert "PASS" in result.stdout
    assert [call[:3] for call in calls[:3]] == [
        ["./.venv/bin/agentic-kit", "transfer", "pr-wait-ci"],
        ["./.venv/bin/agentic-kit", "transfer", "pr-status"],
        ["./.venv/bin/agentic-kit", "transfer", "pr-merge-safe"],
    ]

def test_transfer_pr_create_resolves_head_current_before_pr_create(monkeypatch) -> None:
    from agentic_project_kit.cli_commands import transfer as transfer_module

    captured: dict[str, str] = {}

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    class FakeRepoResult:
        returncode = 0

    def fake_pr_create(*, base: str, head: str, title: str, body: str):
        captured["base"] = base
        captured["head"] = head
        captured["title"] = title
        captured["body"] = body
        return FakeRepoResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(transfer_module, "pr_create", fake_pr_create)
    monkeypatch.setattr(transfer_module, "_echo_repo_result", lambda result, json_output: None)
    monkeypatch.setattr(transfer_module, "_require_transfer_capability", lambda capability: None)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create",
            "--base",
            "main",
            "--head",
            "current",
            "--title",
            "Demo",
            "--body",
            "Body",
            "--skip-llm-context-gate",
        ],
    )

    assert result.exit_code == 0
    assert captured["head"] == "feature/demo"

