from agentic_project_kit.local_feature_gate import PYTHON_RUFF_TARGETS, _ruff_command


def test_local_feature_gate_runs_ruff_only_on_python_source_trees() -> None:
    command = _ruff_command()

    assert command[-2:] == ["src", "tests"]
    assert "README.md" not in command
    assert "CITATION.cff" not in command
    assert "." not in command[4:]


def test_local_feature_gate_ruff_targets_are_declared_contract() -> None:
    assert PYTHON_RUFF_TARGETS == ("src", "tests")
