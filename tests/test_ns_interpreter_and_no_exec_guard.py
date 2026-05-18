from pathlib import Path


def test_ns_has_central_interpreter_discovery() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "resolve_python()" in text
    assert "PY=\"$(resolve_python || true)\"" in text
    assert ".venv/bin/python" in text
    assert ".venv/bin/python3" in text


def test_ns_does_not_hardcode_python3_for_terminal_paths() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "PYTHONPATH=src python3 -m agentic_project_kit.terminal_logging" not in text
    assert "PYTHONPATH=src python3 -m agentic_project_kit.communication_artifact_gc" not in text
    assert "PYTHONPATH=src python3 -m agentic_project_kit.agent_command_runner" not in text
    assert "PYTHONPATH=src \"$PY\" -m agentic_project_kit.terminal_logging" in text


def test_ns_has_no_top_level_exec_dispatches() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "exec .venv/bin/agentic-kit" not in text
    assert "exec agentic-kit" not in text
    assert "exec tools/" not in text
    assert "exec python3 tools/next-step.py" not in text
