from pathlib import Path
import pytest
from agentic_project_kit import cli_executable


@pytest.mark.parametrize("mode", ["declared", "local-first", "unrunnable", "running"])
def test_shared_owned_resolution_order(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(cli_executable, "current_agentic_kit", lambda: "/running/bin/agentic-kit")
    owned = tmp_path / "owned/bin"
    owned.mkdir(parents=True)
    python = owned / "python"
    python.write_text("#!/usr/bin/env python\n")
    script = owned / "agentic-kit"
    script.write_text("#!/usr/bin/env python\n")
    config = tmp_path / ".agentic/config.yaml"
    config.parent.mkdir()
    config.write_text(
        "kit_schema_version: 2\nproject: {name: fixture, type: generic}\nprofile: generic\nhygiene: {doc_lifecycle: warn, review_budgets: {governance: 180}}\nkit:\n  interpreter: "
        + str(python)
        + "\n"
    )
    expected = str(script)
    if mode == "local-first":
        local = tmp_path / ".venv/bin/agentic-kit"
        local.parent.mkdir(parents=True)
        local.write_text("#!/usr/bin/env python\n")
        expected = str(local)
    if mode == "unrunnable":
        script.write_text("#!/missing/interpreter\n")
        expected = "/running/bin/agentic-kit"
    if mode == "running":
        script.unlink()
        expected = "/running/bin/agentic-kit"
    assert cli_executable.default_agentic_kit(tmp_path) == expected
    if mode == "declared":
        assert cli_executable.owned_agentic_kit(tmp_path, allow_declared=False) == ""
    if mode in {"unrunnable", "running"}:
        assert cli_executable.owned_agentic_kit(tmp_path) == ""


def test_runtime_sources_do_not_execute_literal_venv_kit():
    import ast

    root = Path(__file__).resolve().parents[1] / "src/agentic_project_kit"
    for p in root.rglob("*.py"):
        assert not any(
            isinstance(n, ast.Constant) and n.value == "./.venv/bin/agentic-kit"
            for n in ast.walk(ast.parse(p.read_text()))
        ), str(p)


def test_native_gui_terminal_uses_selected_owned_executable(tmp_path, monkeypatch):
    from agentic_project_kit import gui_task_editor

    monkeypatch.setattr(gui_task_editor.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        cli_executable, "default_agentic_kit", lambda root: "/owned/runtime/agentic-kit"
    )
    result = gui_task_editor.build_terminal_launch_plan(tmp_path, platform_name="Darwin")
    assert result.command == ("/owned/runtime/agentic-kit", "transfer", "continue", "--json")


@pytest.mark.parametrize(
    "python_name,script_name", [("python", "agentic-kit"), ("python.exe", "agentic-kit.exe")]
)
def test_running_entrypoint_suffix(tmp_path, monkeypatch, python_name, script_name):
    script = tmp_path / script_name
    script.write_text("#!/bin/sh\nexit 0\n")
    monkeypatch.setattr(cli_executable.sys, "executable", str(tmp_path / python_name))
    assert cli_executable.current_agentic_kit() == str(script)
