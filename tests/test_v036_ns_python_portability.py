from pathlib import Path


def ns_text() -> str:
    return Path("ns").read_text(encoding="utf-8")


def test_ns_python_resolver_prefers_venv_then_system_python() -> None:
    text = ns_text()
    assert "resolve_python()" in text
    assert text.index(".venv/bin/python") < text.index(".venv/bin/python3")
    assert text.index(".venv/bin/python3") < text.index("command -v python3")
    lines = text.splitlines()
    python3_line = next(i for i, line in enumerate(lines) if "command -v python3" in line)
    python_line = next(i for i, line in enumerate(lines) if "command -v python " in line)
    assert python3_line < python_line


def test_ns_python_module_routes_use_resolved_interpreter() -> None:
    text = ns_text()
    assert "PYTHONPATH=src .venv/bin/python" not in text
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.cli governance check' in text
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.cli actions list' in text
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff refresh' in text


def test_finalize_guard_route_is_not_naked_command() -> None:
    text = ns_text()
    assert 'agentic_project_kit.finalize_guard "$@"' in text
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.finalize_guard "$@"' in text
    assert "\n  agentic_project_kit.finalize_guard" not in text
