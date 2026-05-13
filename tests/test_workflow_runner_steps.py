import sys

import pytest

from tools.workflow_runner import WorkflowFailure, _step_command, load_workflow


def test_workflow_runner_supports_pytest_step() -> None:
    assert _step_command("pytest", {}) == [sys.executable, "-m", "pytest", "-q"]


def test_current_work_uses_default_local_gate(tmp_path) -> None:
    workflow_path = tmp_path / "current_work.yaml"
    workflow_path.write_text(
        "name: default-local-gate\n"
        "state: READY\n"
        "timeout_seconds: 600\n"
        "base_branch: main\n"
        "steps:\n"
        "  - git_fetch\n"
        "  - git_switch_main\n"
        "  - git_pull_ff_only\n"
        "  - pytest\n"
        "  - ruff_check\n"
        "  - check_docs\n"
        "  - doctor\n",
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert workflow["name"] == "default-local-gate"
    assert workflow["steps"] == [
        "git_fetch",
        "git_switch_main",
        "git_pull_ff_only",
        "pytest",
        "ruff_check",
        "check_docs",
        "doctor",
    ]


def test_workflow_runner_rejects_shell_like_pytest_variants() -> None:
    with pytest.raises(WorkflowFailure):
        _step_command("python -m pytest -q", {})
