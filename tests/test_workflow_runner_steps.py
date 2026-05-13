import sys
from pathlib import Path

import pytest
import yaml

from tools.workflow_runner import WorkflowFailure, _step_command, load_workflow


def test_workflow_runner_supports_pytest_step() -> None:
    assert _step_command("pytest", {}) == [sys.executable, "-m", "pytest", "-q"]


def test_current_work_uses_default_current_branch_local_gate() -> None:
    workflow = load_workflow(Path(".agentic/current_work.yaml"))

    assert workflow["name"] == "default-current-branch-local-gate"
    assert workflow["steps"] == [
        "git_fetch",
        "git_pull_ff_only",
        "pytest",
        "ruff_check",
        "check_docs",
        "doctor",
    ]


def test_current_work_steps_are_documented_in_coverage() -> None:
    workflow = load_workflow(Path(".agentic/current_work.yaml"))
    coverage = yaml.safe_load(Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8"))
    coverage_text = Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8")

    assert "default-local-gate-workflow-coverage" in {rule["id"] for rule in coverage["rules"]}
    assert workflow["name"] in coverage_text
    for step in workflow["steps"]:
        assert step in coverage_text


def test_workflow_runner_rejects_shell_like_pytest_variants() -> None:
    with pytest.raises(WorkflowFailure):
        _step_command("python -m pytest -q", {})
