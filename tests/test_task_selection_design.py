"""Review-only D1 matrix; these tests never invoke a selected command."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task_selection_design", ROOT / "scripts/task_selection_design_check.py")
DESIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DESIGN)


def load():
    return (yaml.safe_load((ROOT / DESIGN.PROPOSAL).read_text()),
            json.loads((ROOT / "docs/reference/agentic-kit-commands.json").read_text()))


def context(manifest):
    return {"manifest_sha": manifest["meta"]["manifest_sha"], "observed_head": "a" * 40, "current_head": "a" * 40}


def values(route):
    sample = {"nonempty_string": "fixture-value", "positive_integer": 7, "full_commit": "b" * 40,
              "stable_version": "1.1.7", "nonempty_string_list": ["src/example.py"]}
    return {k: sample[v] for k, v in route["inputs"].items()}


@pytest.mark.parametrize("index", range(len(yaml.safe_load((ROOT / DESIGN.PROPOSAL).read_text())["routes"])))
def test_each_reviewed_intent_matches_without_execution_or_permission(index, monkeypatch):
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("selection must never run a process"))
    proposal, manifest = load()
    route = proposal["routes"][index]
    answer = DESIGN.evaluate(proposal, manifest, route["task"], route["when"], values(route), context(manifest))
    command = next(c for c in manifest["commands"] if c["qualified_name"] == route["command"])
    assert answer["result_status"] == "MATCH"
    assert answer["command"] == route["command"]
    assert answer["contract"]["safety"] == command["safety"]
    assert answer["contract"]["remote_effects"] == command["remote_effects"]
    assert answer["implementation_status"] == "DESIGN_SIMULATION"
    assert answer["execution_authorized"] is False
    assert "argv" not in answer


def test_missing_facts_are_not_guessed_from_tag_or_task():
    p, m = load()
    answer = DESIGN.evaluate(p, m, "finish_work", {}, {}, context(m))
    assert answer["result_status"] == "NEEDS_FACTS"
    assert "branch_role" in answer["missing"]
    assert "command" not in answer


def test_known_wrong_state_blocks_and_unknown_task_stays_unknown():
    p, m = load()
    answer = DESIGN.evaluate(p, m, "settle_merged_pr", {"workspace_mode": "managed", "pr_state": "open"}, {"after_pr": 7}, context(m))
    assert answer["result_status"] == "BLOCKED"
    assert DESIGN.evaluate(p, m, "closeout", {}, {}, {})["result_status"] == "UNKNOWN_TASK"


def test_required_user_inputs_are_explicit():
    p, m = load()
    answer = DESIGN.evaluate(p, m, "complete_open_pr", {"workspace_mode": "managed", "pr_state": "open"}, {}, context(m))
    assert answer["result_status"] == "NEEDS_INPUTS"
    assert answer["missing"] == ["expected_head_sha", "pr_number"]


@pytest.mark.parametrize("bad", [True, 0, -1, "7"])
def test_invalid_pr_inputs_never_match(bad):
    p, m = load()
    answer = DESIGN.evaluate(p, m, "settle_merged_pr", {"workspace_mode": "managed", "pr_state": "merged"}, {"after_pr": bad}, context(m))
    assert answer["result_status"] == "INVALID_INPUT"


@pytest.mark.parametrize("change", ["stale", "manifest", "short", "missing"])
def test_context_identity_and_freshness_are_not_optional(change):
    p, m = load()
    ctx = context(m)
    expected = "INVALID_INPUT"
    if change == "stale":
        ctx["current_head"] = "b" * 40
        expected = "NEEDS_FACTS"
    elif change == "manifest":
        ctx["manifest_sha"] = "other"
    elif change == "short":
        ctx["observed_head"] = "abc"
    else:
        ctx = {}
        expected = "NEEDS_FACTS"
    assert DESIGN.evaluate(p, m, "check_work", {"workspace_mode": "managed"}, {}, ctx)["result_status"] == expected


def test_ambiguous_routes_never_use_the_first_match():
    p, m = load()
    duplicate = copy.deepcopy(p["routes"][0])
    duplicate["when"] = {}
    p["routes"].append(duplicate)
    a = DESIGN.evaluate(p, m, "check_work", {"workspace_mode": "managed"}, {}, context(m))
    p["routes"].reverse()
    b = DESIGN.evaluate(p, m, "check_work", {"workspace_mode": "managed"}, {}, context(m))
    assert a == b
    assert a["result_status"] == "AMBIGUOUS"
    assert a["execution_authorized"] is False


def test_unknown_alternative_is_not_dropped_for_a_known_match():
    p, m = load()
    alternative = copy.deepcopy(p["routes"][0])
    alternative["when"]["pr_state"] = "open"
    p["routes"].append(alternative)
    answer = DESIGN.evaluate(p, m, "check_work", {"workspace_mode": "managed"}, {}, context(m))
    assert answer["result_status"] == "NEEDS_FACTS"


@pytest.mark.parametrize("change", ["enabled", "schema", "command", "diagnostic", "release_preview", "execute", "parameter", "fact"])
def test_proposal_drift_blocks_instead_of_silently_adopting(change):
    p, m = load()
    if change == "enabled":
        p["runtime_enabled"] = True
    elif change == "schema":
        p["schema_version"] = 99
    elif change == "command":
        p["routes"][0]["command"] = "agentic-kit nonexistent"
    elif change == "diagnostic":
        p["routes"][0]["command"] = "agentic-kit work start"
    elif change == "release_preview":
        p["routes"][-1]["phase"] = "planning"
    elif change == "execute":
        p["routes"][-1]["inputs"]["execute"] = "nonempty_string"
    elif change == "parameter":
        p["routes"][0]["inputs"]["not_a_parameter"] = "positive_integer"
    else:
        p["routes"][0]["when"]["worktree_clean"] = "true"
    assert DESIGN.validate(p, m)


def test_malformed_runtime_inputs_do_not_become_selection_authority():
    p, m = load()
    for facts, inputs in [({"worktree_clean": "true"}, {}), ({"workspace_mode": "managed"}, {"execute": True})]:
        assert DESIGN.evaluate(p, m, "check_work", facts, inputs, context(m))["result_status"] == "INVALID_INPUT"
    assert DESIGN.evaluate(None, m, "check_work", {}, {}, {})["result_status"] == "INVALID_INPUT"


def test_generated_review_matrix_is_current_and_data_bound():
    p, m = load()
    path = ROOT / "docs/reports/task_selection_design_20261026/README.md"
    assert DESIGN.render_matrix(p, m) == path.read_text()
    p["routes"][0]["review_note"] = "Changed review fact"
    assert "Changed review fact" in DESIGN.render_matrix(p, m)


@pytest.mark.parametrize("state", ["prepared", "published", "blocked", "complete"])
def test_fresh_release_intent_never_becomes_implicit_resume(state):
    p, m = load()
    route = next(r for r in p["routes"] if r["task"] == "release_version")
    facts = {**route["when"], "release_state": state}
    answer = DESIGN.evaluate(p, m, "release_version", facts, values(route), context(m))
    assert answer["result_status"] == "BLOCKED"
    assert answer["execution_authorized"] is False
