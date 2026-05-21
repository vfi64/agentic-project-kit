from __future__ import annotations

from pathlib import Path

from agentic_project_kit.audit_test_matrix import discover_gui_entry_tests, existing_contract_tests, pytest_argv_for

def test_gui_entry_matrix_discovers_real_tests() -> None:
    paths = discover_gui_entry_tests(Path.cwd())
    assert paths
    assert any("test_action_registry.py" in path for path in paths)
    assert all(Path(path).exists() for path in paths)

def test_contract_matrix_filters_to_existing_tests() -> None:
    paths = existing_contract_tests(Path.cwd())
    assert paths
    assert all(Path(path).exists() for path in paths)

def test_pytest_argv_uses_argument_list_not_shell_pipeline() -> None:
    argv = pytest_argv_for(["tests/test_action_registry.py", "tests/test_action_specs.py"])
    joined = " ".join(argv)
    assert argv[:2] == ["-m", "pytest"]
    assert "xargs" not in joined
    assert "PATH=" not in joined
    assert argv[-1] == "-q"
