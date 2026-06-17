from __future__ import annotations

from pathlib import Path
import sys

import tools.screen_control_gate as gate


def test_default_screen_control_gate_commands_use_venv_python() -> None:
    commands = gate.default_commands("./.venv/bin/python")
    assert commands[0].argv == ("./.venv/bin/python", "-m", "pytest", "-q")
    assert commands[1].argv == ("./.venv/bin/python", "-m", "ruff", "check", ".")
    assert commands[2].argv == ("./.venv/bin/agentic-kit", "check-docs")
    assert commands[3].argv == ("./.venv/bin/agentic-kit", "doctor")


def test_run_gate_captures_output_without_shell(tmp_path: Path) -> None:
    output = tmp_path / "screen.txt"
    commands = [
        gate.GateCommand(
            "python-hello",
            (sys.executable, "-c", "print('hello screen gate')"),
        )
    ]
    rc = gate.run_gate(commands, output)
    assert rc == 0
    text = output.read_text(encoding="utf-8")
    assert "hello screen gate" in text
    assert "RESULT=SCREEN_CONTROL_GATE_DONE rc=0" in text


def test_legacy_shell_screen_gate_is_not_required_by_python_references() -> None:
    for path in [Path("src"), Path("tools"), Path("tests")]:
        for file_path in path.rglob("*.py"):
            if file_path == Path("tests/test_screen_control_gate_portability.py"):
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            assert "screen_control_gate.sh" not in text
