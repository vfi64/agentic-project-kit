"""KIT-GF-073: a consumer's light-path SKIPPED checks pass only for a light pull request.

A consumer following the documented KIT-GF-063 fragment skips its heavy jobs on a light pull
request. Until now only the Kit's own pytest-parallel-shadow counted as an optional skipped
check, so pr wait-ci, PR status and post-merge settlement blocked on every light refresh. The
fixtures execute the installed wheel in an external Git workspace.
"""
import json
import os
import subprocess
import sys
import textwrap

import pytest
import yaml
from test_external_rule_registry import installed_kit as installed_kit, external as external

PROBE = textwrap.dedent(
    """
    import json, sys
    from agentic_project_kit.ci_readiness import classify_pr_readiness
    from agentic_project_kit.next_turn_pr_status import classify_pr_status
    snapshot = json.loads(sys.argv[1])
    readiness = classify_pr_readiness(snapshot, expected_head_sha=snapshot["headRefOid"])
    status = classify_pr_status(snapshot, pr="1")
    print(json.dumps({"outcome": readiness.outcome, "reasons": list(readiness.reasons),
                      "decision": status.decision, "skipped_optional": list(status.skipped_optional_checks)}))
    """
)


def _git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _pull_request(root, installed_kit, *, declared, product_change=False, branch="docs/post-pr42-handoff-refresh",
                  playwright="SKIPPED"):
    config = root / ".agentic/config.yaml"
    data = yaml.safe_load(config.read_text())
    if declared is not None:
        data.setdefault("gates", {})["light_path_skipped_checks"] = declared
    config.write_text(yaml.safe_dump(data, sort_keys=False))
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture baseline")
    base = _git(root, "rev-parse", "HEAD")
    _git(root, "switch", "-c", branch)
    state = root / ".agentic/state/status.md"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("Refreshed state")
    if product_change:
        (root / "product.py").write_text("changed = True\n")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture refresh")
    head = _git(root, "rev-parse", "HEAD")
    snapshot = {
        "state": "OPEN", "baseRefOid": base, "headRefOid": head, "headRefName": branch,
        "mergeStateStatus": "CLEAN", "mergeable": "MERGEABLE",
        "statusCheckRollup": [
            {"name": "agentic-gate", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "playwright", "status": "COMPLETED", "conclusion": playwright},
        ],
    }
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}
    result = subprocess.run([sys.executable, "-c", PROBE, json.dumps(snapshot)], cwd=root, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]
    return json.loads(result.stdout)


def test_declared_light_path_check_skipped_on_a_light_refresh_pr_is_green(external, installed_kit):
    root, _ = external
    data = _pull_request(root, installed_kit, declared=["playwright"])
    assert data["outcome"] == "READY_TO_MERGE"
    assert data["decision"] == "green"
    assert data["skipped_optional"] == ["playwright"]


@pytest.mark.parametrize(
    "case",
    [
        {"declared": ["playwright"], "product_change": True},  # full classification
        {"declared": ["playwright"], "branch": "codex/product-work"},  # not a refresh branch: full
        {"declared": None},  # nothing declared: the old rule stays
        {"declared": ["deploy"]},  # a different check is declared
    ],
)
def test_skipped_check_still_blocks_outside_a_declared_light_pr(external, installed_kit, case):
    root, _ = external
    data = _pull_request(root, installed_kit, **case)
    assert data["outcome"] == "BLOCKED"
    assert data["reasons"] == ["check skipped: playwright"]
    assert data["decision"] == "unknown"


def test_a_declared_light_path_check_that_fails_stays_red(external, installed_kit):
    root, _ = external
    data = _pull_request(root, installed_kit, declared=["playwright"], playwright="FAILURE")
    assert data["outcome"] == "BLOCKED"
    assert data["reasons"] == ["check failed: playwright"]
    assert data["decision"] == "red"


@pytest.mark.parametrize("value", [["playwright", "playwright"], [""], [" playwright"], "playwright", [1]])
def test_invalid_light_path_declaration_is_refused(tmp_path, value):
    from agentic_project_kit.workspace import load_workspace

    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/config.yaml").write_text(yaml.safe_dump(
        {"kit_schema_version": 2, "project": {"name": "x", "type": "generic"}, "hygiene": {"doc_lifecycle": "off"},
         "gates": {"light_path_skipped_checks": value}}))
    with pytest.raises(RuntimeError, match="light_path_skipped_checks"):
        load_workspace(tmp_path)
