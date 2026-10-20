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


def _step_by_uses(steps: list[dict[str, object]], uses: str) -> dict[str, object]:
    for step in steps:
        if step.get("uses") == uses:
            return step
    raise AssertionError(f"missing uses step: {uses}")


FULL = "needs.classify.outputs.gate-mode == 'full'"


def test_ci_required_job_keeps_full_gate_as_default() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))

    assert data["name"] == "CI"
    assert data["permissions"] == {
        "actions": "read",
        "checks": "read",
        "contents": "read",
        "pull-requests": "read",
    }
    classify = data["jobs"]["classify"]
    assert "if" not in classify and "needs" not in classify
    assert classify["outputs"] == {"gate-mode": "${{ steps.runtime-policy.outputs.gate-mode }}"}

    steps = classify["steps"]
    runs = "\n".join(_run_steps(steps))
    classify_step = _step_by_name(steps, "Classify CI runtime policy")
    checkout_step = steps[0]

    assert checkout_step["uses"] == "actions/checkout@v6"
    assert checkout_step["with"] == {"fetch-depth": 1}
    assert _step_by_uses(steps, "actions/setup-python@v6")["with"] == {
        "python-version": "3.13",
        "cache": "pip",
        "cache-dependency-path": "pyproject.toml",
    }
    assert "fetch_commit()" in runs
    assert 'git fetch --no-tags --depth=1 origin "$sha"' in runs
    assert 'refs/pull/${PR_NUMBER}/head' in runs
    assert "changed paths unavailable; falling back to full-repository path set" in runs
    assert "PYTHONPATH=src python -m agentic_project_kit.ci_runtime_policy admin-refresh" in runs
    assert "PYTHONPATH=src python -m agentic_project_kit.ci_github_proof" in runs
    assert "PYTHONPATH=src python -m agentic_project_kit.ci_runtime_policy main-push" in runs
    assert 'FINAL_TREE="$(git rev-parse "${CURRENT_SHA}^{tree}"' in runs
    assert '--final-tree "$FINAL_TREE"' in runs
    assert '--tested-tree "$TESTED_TREE"' in runs
    assert '--pr-checks-passed "$PR_CHECKS_PASSED"' in runs
    assert '"admin-refresh-light"' in str(classify_step["run"])
    assert '"tree-proof"' in str(classify_step["run"])
    keep = _step_by_name(steps, "Keep the runtime policy for the required test job")
    assert keep["with"]["name"] == "ci-runtime-policy" and keep["with"]["if-no-files-found"] == "error"

    test_job = data["jobs"]["test"]
    assert test_job["needs"] == ["classify", "test-shard"]
    assert test_job["if"] == "${{ !cancelled() }}"
    test_steps = test_job["steps"]
    upstream = _step_by_name(test_steps, "Upstream jobs succeeded")
    assert test_steps[0] is upstream
    assert upstream["env"] == {"CLASSIFY_RESULT": "${{ needs.classify.result }}",
                               "SHARD_RESULT": "${{ needs.test-shard.result }}"}
    assert 'test "$CLASSIFY_RESULT" = success' in upstream["run"] and 'test "$SHARD_RESULT" = success' in upstream["run"]
    assert _step_by_name(test_steps, "Runtime policy from the classify job")["with"]["name"] == "ci-runtime-policy"
    assert _step_by_name(test_steps, "Install package")["if"] == "needs.classify.outputs.gate-mode != 'tree-proof'"
    assert _step_by_name(test_steps, "Ruff")["if"] == FULL
    assert _step_by_name(test_steps, "Tests")["if"] == FULL
    assert _step_by_name(test_steps, "Tests")["run"] == (
        'python -m agentic_project_kit.ci_test_shards check --full "$RUNNER_TEMP/collected-full.txt" '
        '--shards-dir "$RUNNER_TEMP/shards" --count 3'
    )
    assert "--write-collected" in _step_by_name(test_steps, "Collect the full suite")["run"]
    assert _step_by_name(test_steps, "CLI smoke")["if"] == FULL


def test_the_suite_runs_in_deterministic_shards_that_always_report() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    shard = data["jobs"]["test-shard"]
    assert shard["needs"] == "classify" and "if" not in shard   # never a skipped check
    assert shard["strategy"] == {"fail-fast": False, "matrix": {"shard": [0, 1, 2]}}
    steps = shard["steps"]
    assert steps[0]["if"] == "needs.classify.outputs.gate-mode != 'full'"
    assert all(step["if"] == FULL for step in steps[1:])
    run = str(_step_by_name(steps, "Tests (shard)")["run"])
    assert "--collect-only --shard-index ${{ matrix.shard }} --shard-count 3 --write-collected" in run
    assert "python -m pytest -q -n 4 --dist worksteal --durations=20 --shard-index ${{ matrix.shard }} --shard-count 3 --junitxml" in run
    assert _step_by_name(steps, "Keep the shard report")["with"]["if-no-files-found"] == "error"


def test_admin_refresh_light_gate_runs_only_handoff_registry_and_docs_checks() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = data["jobs"]["test"]["steps"]
    admin_step = _step_by_name(steps, "Admin refresh light gate")
    run = str(admin_step["run"])

    assert admin_step["if"] == "needs.classify.outputs.gate-mode == 'admin-refresh-light'"
    assert admin_step["env"]["EVENT_NAME"] == "${{ github.event_name }}"
    assert admin_step["env"]["BEFORE_SHA"] == "${{ github.event.before }}"
    assert admin_step["env"]["CURRENT_SHA"] == "${{ github.sha }}"
    assert admin_step["env"]["PR_BASE_SHA"] == "${{ github.event.pull_request.base.sha }}"
    assert admin_step["env"]["PR_HEAD_SHA"] == "${{ github.event.pull_request.head.sha }}"
    assert admin_step["env"]["PR_NUMBER"] == "${{ github.event.pull_request.number }}"
    assert 'git fetch --no-tags --depth=1 origin "$PR_BASE_SHA" "$PR_HEAD_SHA"' in run
    assert "POLICY_MUTATION=" in run
    assert "agentic-kit handoff check" in run
    assert "validate_successor_package()" in run
    assert "agentic-kit dpa current-handoff-refresh --json" in run
    assert "post-merge-settle-refresh)" in run
    assert "validate_successor_package" in run
    assert "successor handoff validation_report.json is not PASS" in run
    assert 'git diff "$PR_BASE_SHA" "$PR_HEAD_SHA" --output "$RUNNER_TEMP/admin-refresh.diff"' in run
    assert 'git diff "$BEFORE_SHA" "$CURRENT_SHA" --output "$RUNNER_TEMP/admin-refresh.diff"' in run
    assert "cannot determine admin refresh diff endpoints" in run
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

    assert tree_proof["if"] == "needs.classify.outputs.gate-mode == 'tree-proof'"
    assert "main-push-policy.json" in str(tree_proof["run"])
    assert "TREE_PROOF" in str(tree_proof["run"])


def test_parallel_pytest_is_required_and_shadow_is_manual_diagnostic_only() -> None:
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))

    assert "pytest-parallel-shadow" in data["jobs"]
    shadow = data["jobs"]["pytest-parallel-shadow"]
    assert shadow["if"] == "github.event_name == 'workflow_dispatch'"
    assert shadow["continue-on-error"] is True
    assert shadow["timeout-minutes"] == 20
    assert "needs" not in shadow
    shadow_run = "\n".join(_run_steps(shadow["steps"]))
    assert _step_by_uses(shadow["steps"], "actions/setup-python@v6")["with"] == {
        "python-version": "3.13",
        "cache": "pip",
        "cache-dependency-path": "pyproject.toml",
    }
    assert "python -m pytest -q -n 4 --durations=20" in shadow_run
    assert "PYTEST_PARALLEL_SHADOW_RC=$rc" in shadow_run
    assert "::warning title=pytest-parallel-shadow::diagnostic shadow pytest failed" in shadow_run
    assert "exit 0" in shadow_run


def test_pytest_xdist_is_dev_dependency_only() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert "pytest-xdist>=3.6" in project["project"]["optional-dependencies"]["dev"]
    assert "pytest-xdist>=3.6" not in project["project"]["dependencies"]
