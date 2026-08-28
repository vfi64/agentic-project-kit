from __future__ import annotations

from pathlib import Path
import tomllib

import yaml


CI_WORKFLOW = Path(".github/workflows/ci.yml")
PYPROJECT = Path("pyproject.toml")


def _run_steps(steps: list[dict[str, object]]) -> list[str]:
    return [str(step.get("run", "")) for step in steps]


def _step_by_name(steps: list[dict[str, object]], name: str) -> dict[str, object]:
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(f"missing step: {name}")


def test_ci_required_job_keeps_full_gate_as_default() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))

    assert data["name"] == "CI"
    assert data["permissions"] == {"contents": "read"}
    test_job = data["jobs"]["test"]
    assert "if" not in test_job

    steps = test_job["steps"]
    runs = "\n".join(_run_steps(steps))
    classify_step = _step_by_name(steps, "Classify CI runtime policy")

    assert "PYTHONPATH=src python -m agentic_project_kit.ci_runtime_policy admin-refresh" in runs
    assert "PYTHONPATH=src python -m agentic_project_kit.ci_runtime_policy main-push" in runs
    assert 'FINAL_TREE="$(git rev-parse "${CURRENT_SHA}^{tree}"' in runs
    assert '--final-tree "$FINAL_TREE"' in runs
    assert '"admin-refresh-light"' in str(classify_step["run"])
    assert '"tree-proof"' in str(classify_step["run"])
    assert _step_by_name(steps, "Install package")["if"] != "false"
    assert _step_by_name(steps, "Ruff")["if"] == "steps.runtime-policy.outputs.gate-mode == 'full'"
    assert _step_by_name(steps, "Tests")["if"] == "steps.runtime-policy.outputs.gate-mode == 'full'"
    assert _step_by_name(steps, "CLI smoke")["if"] == "steps.runtime-policy.outputs.gate-mode == 'full'"


def test_admin_refresh_light_gate_runs_only_handoff_registry_and_docs_checks() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = data["jobs"]["test"]["steps"]
    admin_step = _step_by_name(steps, "Admin refresh light gate")
    run = str(admin_step["run"])

    assert admin_step["if"] == "steps.runtime-policy.outputs.gate-mode == 'admin-refresh-light'"
    assert "POLICY_MUTATION=" in run
    assert "agentic-kit handoff check" in run
    assert "agentic-kit dpa current-handoff-refresh --json" in run
    assert "successor handoff validation_report.json is not PASS" in run
    assert "unexpected admin refresh mutation" in run
    assert "agentic-kit handoff post-merge-refresh-status" not in run
    assert "agentic-kit transfer post-merge-check" not in run
    assert "python -m agentic_project_kit.protected_change_planner" in run
    assert "agentic-kit transfer protected-diff-plan" in run
    assert "agentic-kit doc-registry reconcile --json" in run
    assert "agentic-kit doc-registry check-unregistered --json" in run
    assert "agentic-kit check-docs" in run
    assert "tests/test_successor_handoff_package.py" in run
    assert "tests/test_chat_entrypoint_contract.py" in run
    assert "tests/test_documentation_registry.py" in run
    assert "python -m pytest -q" not in {
        line.strip() for line in run.splitlines()
    }


def test_main_push_tree_proof_lane_is_inside_required_test_job() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = data["jobs"]["test"]["steps"]
    tree_proof = _step_by_name(steps, "Main push tree proof gate")

    assert tree_proof["if"] == "steps.runtime-policy.outputs.gate-mode == 'tree-proof'"
    assert "main-push-policy.json" in str(tree_proof["run"])
    assert "TREE_PROOF" in str(tree_proof["run"])


def test_parallel_pytest_is_shadow_only_and_uses_fixed_worker_count() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))

    assert "pytest-parallel-shadow" in data["jobs"]
    shadow = data["jobs"]["pytest-parallel-shadow"]
    assert shadow["continue-on-error"] is True
    assert shadow["timeout-minutes"] == 20
    assert "needs" not in data["jobs"]["test"]
    assert "needs" not in shadow
    shadow_run = "\n".join(_run_steps(shadow["steps"]))
    assert "python -m pytest -q -n 4 --durations=20" in shadow_run
    assert "PYTEST_PARALLEL_SHADOW_RC=$rc" in shadow_run
    assert "::warning title=pytest-parallel-shadow::diagnostic shadow pytest failed" in shadow_run
    assert "exit 0" in shadow_run


def test_pytest_xdist_is_dev_dependency_only() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert "pytest-xdist>=3.6" in project["project"]["optional-dependencies"]["dev"]
    assert "pytest-xdist>=3.6" not in project["project"]["dependencies"]
