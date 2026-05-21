from pathlib import Path


def test_finalize_guard_shell_adapter_has_been_removed() -> None:
    assert not Path("tools/ns_finalize_guard.sh").exists()


def test_finalize_guard_python_core_remains_callable() -> None:
    core = Path("src/agentic_project_kit/finalize_guard.py").read_text(encoding="utf-8")
    assert "def main" in core
    assert "render_finalize_guard" in core


def test_ns_finalize_guard_route_does_not_call_removed_shell_adapter() -> None:
    ns = Path("./ns").read_text(encoding="utf-8")
    assert "tools/ns_finalize_guard.sh" not in ns
