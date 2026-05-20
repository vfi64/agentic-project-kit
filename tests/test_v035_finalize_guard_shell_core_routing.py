from pathlib import Path


def test_finalize_guard_shell_delegates_status_classification_to_python_core() -> None:
    script = Path("tools/ns_finalize_guard.sh").read_text(encoding="utf-8")
    assert "python -m agentic_project_kit.finalize_guard" in script
    assert "STATUS: PASS_NEEDS_PR" not in script
    assert "STATUS: PASS_SUPERSEDED" not in script
    assert "STATUS: FAIL_CONFLICT_RELEVANT" not in script


def test_ns_finalize_guard_route_keeps_shell_adapter() -> None:
    ns = Path("./ns").read_text(encoding="utf-8")
    assert "tools/ns_finalize_guard.sh" in ns
    assert "finalize-guard" in ns
