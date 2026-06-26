from pathlib import Path
import subprocess
import sys

from agentic_project_kit.cockpit import _resolve_command, _run_command


def test_cockpit_resolves_agentic_kit_to_project_venv(tmp_path: Path) -> None:
    root = tmp_path
    bin_dir = root / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    executable = bin_dir / "agentic-kit"
    executable.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")

    resolved = _resolve_command(("agentic-kit", "workflow", "state"), root)

    assert resolved == [str(executable), "workflow", "state"]


def test_cockpit_resolves_agentic_kit_next_to_current_python(
    tmp_path: Path, monkeypatch
) -> None:
    fake_python = tmp_path / "bin" / "python"
    fake_python.parent.mkdir()
    fake_python.write_text("", encoding="utf-8")
    fake_agentic = tmp_path / "bin" / "agentic-kit"
    fake_agentic.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(fake_python))

    resolved = _resolve_command(("agentic-kit", "doctor"), tmp_path)

    assert resolved == [str(fake_agentic), "doctor"]


def test_cockpit_run_command_returns_structured_missing_executable_failure(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "missing-python"))
    monkeypatch.setenv("PATH", "")

    completed = _run_command(("agentic-kit", "doctor"), tmp_path)

    assert isinstance(completed, subprocess.CompletedProcess)
    assert completed.returncode == 127
    assert completed.stdout == ""
    assert "Command executable not found" in completed.stderr
    assert ".venv/bin/agentic-kit" in completed.stderr
