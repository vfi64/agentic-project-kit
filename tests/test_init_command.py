from __future__ import annotations

from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
import agentic_project_kit.cli_commands.init as init_module


def test_init_warns_when_initial_git_commit_fails(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        command = ("git", *args)
        calls.append(command)
        if args[0] == "commit":
            return subprocess.CompletedProcess(
                list(command),
                128,
                "Author identity unknown\nfatal: unable to auto-detect email address\n",
            )
        return subprocess.CompletedProcess(list(command), 0, "")

    monkeypatch.setattr(init_module, "_run_git", fake_run_git)

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / "docker-greenfield"),
            "--type",
            "generic",
            "--description",
            "Docker greenfield smoke",
            "--kit-source",
            "none",
        ],
    )

    assert result.exit_code == 0, result.output
    assert ("git", "add", ".") in calls
    assert ("git", "commit", "-m", "Initialize agentic project") in calls
    assert "Initial Git commit was not created" in result.output
    assert "Configure Git identity" in result.output
