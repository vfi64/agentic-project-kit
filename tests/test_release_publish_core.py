from __future__ import annotations

from pathlib import Path

import agentic_project_kit.release_publish_core as release_publish_core
from agentic_project_kit.release_publish_core import CommandResult, expected_confirmation, publish_release


def test_expected_confirmation_uses_release_tag() -> None:
    assert expected_confirmation("v0.4.9") == "publish-v0.4.9"


def test_publish_release_fails_closed_before_any_command(monkeypatch, tmp_path: Path, capsys) -> None:
    calls: list[list[str]] = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        raise AssertionError(f"release publish core must fail closed before command execution: {args}")

    monkeypatch.setattr(release_publish_core, "run_command", fake_run_command)

    assert publish_release("0.4.9", "publish-v0.4.9", tmp_path, sleep_seconds=0) == 2
    assert calls == []

    out = capsys.readouterr().out
    assert "direct release publish core is disabled after legacy ns removal" in out
    assert "No branch, tag, push, GitHub release, or DOI side effect was attempted." in out
    assert "### RESULT: FAIL ###" in out


def test_publish_release_invalid_confirmation_fails_without_command(monkeypatch, tmp_path: Path, capsys) -> None:
    calls: list[list[str]] = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        raise AssertionError(f"release publish core must reject confirmation before command execution: {args}")

    monkeypatch.setattr(release_publish_core, "run_command", fake_run_command)

    assert publish_release("0.4.9", "wrong-token", tmp_path, sleep_seconds=0) == 2
    assert calls == []

    out = capsys.readouterr().out
    assert "refusing release publish without exact confirmation token" in out
    assert "supported agentic-kit release workflow" in out


def test_publish_release_invalid_version_fails_without_command(monkeypatch, tmp_path: Path, capsys) -> None:
    calls: list[list[str]] = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        raise AssertionError(f"release publish core must reject invalid version before command execution: {args}")

    monkeypatch.setattr(release_publish_core, "run_command", fake_run_command)

    assert publish_release("not-a-version", "publish-vnot-a-version", tmp_path, sleep_seconds=0) == 2
    assert calls == []

    out = capsys.readouterr().out
    assert "release publish core is disabled after legacy ns removal" in out or "invalid semantic version" in out
