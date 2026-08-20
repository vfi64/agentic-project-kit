from __future__ import annotations

from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
import agentic_project_kit.cli_commands.init as init_module
import agentic_project_kit.templates as templates_module


def _completed(argv: list[str], returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout)


def _patch_git_available(monkeypatch) -> None:
    monkeypatch.setattr(init_module.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None)


def _patch_template_git_init(monkeypatch) -> None:
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "init"]:
            return _completed(command)
        return _completed(command)

    monkeypatch.setattr(templates_module.subprocess, "run", fake_run)


def test_init_requires_git_before_project_mutation(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "no-git-project"

    monkeypatch.setattr(init_module.shutil, "which", lambda name: None)

    def unexpected_create_project(*args, **kwargs):
        raise AssertionError("create_project must not run when git is unavailable")

    monkeypatch.setattr(init_module, "create_project", unexpected_create_project)

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--type",
            "generic",
            "--description",
            "No git smoke",
            "--kit-source",
            "none",
        ],
    )

    assert result.exit_code == 2
    assert "Git is required for `agentic-kit init`" in result.output
    assert "pip cannot install this" in result.output
    assert "system prerequisite portably" in result.output
    assert not target.exists()


def test_init_warns_when_initial_git_commit_fails(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    _patch_git_available(monkeypatch)
    _patch_template_git_init(monkeypatch)

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


def test_init_generated_project_check_and_doctor_do_not_emit_legacy_warning(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "docker-greenfield"
    _patch_git_available(monkeypatch)
    _patch_template_git_init(monkeypatch)

    def fake_run_git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["git", *args], 0, "")

    monkeypatch.setattr(init_module, "_run_git", fake_run_git)

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--type",
            "generic",
            "--description",
            "Docker greenfield smoke",
            "--kit-source",
            "none",
        ],
    )

    assert result.exit_code == 0, result.output

    check_result = CliRunner().invoke(app, ["check", "--root", str(target)])
    doctor_result = CliRunner().invoke(app, ["doctor", "--root", str(target)])

    assert check_result.exit_code == 0, check_result.output
    assert doctor_result.exit_code == 0, doctor_result.output
    assert "LegacyProfileDeprecationWarning" not in check_result.output
    assert "implicit legacy profile" not in check_result.output
    assert "LegacyProfileDeprecationWarning" not in doctor_result.output
    assert "implicit legacy profile" not in doctor_result.output
    assert "[SKIP] workspace manifest" in doctor_result.output
    assert ".agentic/project.yaml" in doctor_result.output
