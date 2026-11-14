"""G4 (owner plan 2026-11-13): the whole path is tested.

Journeys from reference/journeys.json run as machine contracts against the built wheel. A BLOCKED
Kit step fails the contract; the approval count must equal the declared baseline; pending journeys
can only leave the pending list by becoming contracts.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from agentic_project_kit.greenfield_retest import check_route, validate_machine
from agentic_project_kit.greenfield_retest_adoption import FIXTURE as ADOPTION, adoption_version, guard_adoption_index
from agentic_project_kit.greenfield_retest_release_check import release_effects
from agentic_project_kit.journey_contracts import (
    JOURNEY_IDS, approvals, journey_effects, load, needs_consent, validate,
)

from test_external_rule_registry import installed_kit as installed_kit

PENDING = {"J5"}  # ratchet: shrinks only when a journey becomes a contract


def _journeys():
    return {journey["id"]: journey for journey in load()["journeys"]}


def test_every_planned_journey_is_a_contract_or_pending_with_a_reason():
    pending = {entry["id"]: entry["reason"] for entry in load()["pending"]}
    assert set(_journeys()) | set(pending) == set(JOURNEY_IDS)
    assert not set(_journeys()) & set(pending)
    assert set(pending) == PENDING, "update PENDING when a journey becomes a contract"
    assert all(reason.strip() for reason in pending.values())


@pytest.mark.parametrize("journey_id", sorted(_journeys()))
def test_every_journey_contract_is_valid_and_matches_its_approval_baseline(journey_id):
    journey = _journeys()[journey_id]
    validate(journey)
    assert approvals(journey) == journey["approvals"], "G4: approval count changed; a rise is a regression"


def test_only_journeys_treat_a_dry_run_finish_as_local():
    dry = ["agentic-kit", "work", "finish", "--branch", "b", "--title", "t", "--message", "m", "--json"]
    entry = check_route(dry)
    assert journey_effects(dry, entry) == ["fetch"]
    assert set(release_effects(dry, entry)) >= {"merge", "pull_request"}  # catalog rule unchanged
    assert set(journey_effects([*dry, "--execute"], entry)) >= {"merge", "pull_request"}


def test_a_journey_step_that_may_block_is_rejected():
    journey = json.loads(json.dumps(_journeys()["J1"]))
    journey["machine"]["steps"][0]["expect"] = {"returncode": 0}
    with pytest.raises(ValueError, match="PASS, PLANNED or AWAITING_APPROVAL"):
        validate(journey)


def test_a_step_without_result_status_must_expect_exactly_returncode_zero():
    journey = json.loads(json.dumps(_journeys()["J2"]))
    ack = next(step for step in journey["machine"]["steps"] if step["run"][1:3] == ["rules", "acknowledge"])
    ack["expect"] = {"returncode_nonzero": True}
    with pytest.raises(ValueError, match="exactly returncode 0"):
        validate(journey)


def test_consent_is_a_signed_execution_or_an_effect_beyond_local_and_network_read():
    """Owner decision 2026-11-13: a read-only plan is no consent; a signed execution is one."""
    plan = ["agentic-kit", "kit", "update", "--version", "1.3.0.post1", "--json"]
    signed = [*plan[:-1], "--execute", "--expected-signature", "abc", "--json"]
    finish = ["agentic-kit", "work", "finish", "--branch", "b", "--title", "t", "--message", "m", "--json"]
    assert release_effects(plan, check_route(plan)) == ["network_read"]
    assert not needs_consent(plan)
    assert needs_consent(signed)
    assert needs_consent(finish)  # dry run here, but it plans push, PR and merge
    assert not needs_consent(["agentic-kit", "release", "ready", "--version", "0.1.1", "--json"])


def test_approval_baselines_are_one_per_finish_plus_one_per_signed_adoption():
    assert {jid: journey["approvals"] for jid, journey in _journeys().items()} == {"J1": 1, "J2": 2, "J3": 1, "J4": 1}


def test_only_the_adoption_fixture_treats_an_exact_kit_update_as_local():
    update = ["agentic-kit", "kit", "update", "--version", "1.3.0.post1", "--execute",
              "--expected-signature", "abc", "--json"]
    entry = check_route(update)
    assert journey_effects(update, entry, ADOPTION) == ["none"]
    assert journey_effects(update, entry, "external_manifest") == ["network_read"]
    assert journey_effects([*update[:3], "--latest", "--json"], entry, ADOPTION) == ["network_read"]
    assert journey_effects([*update, "--root", "elsewhere"], entry, ADOPTION) == ["network_read"]
    assert release_effects(update, entry, ADOPTION) == ["network_read"]  # catalog rule unchanged


def test_the_catalog_rejects_a_kit_update_execute_outside_journeys():
    journey = json.loads(json.dumps(_journeys()["J2"]))
    retest = {"commands": [" ".join(s["run"]) for s in journey["machine"]["steps"] if s["run"][0] == "agentic-kit"],
              "workspace_kind": "external", "execution_class": "local", "machine": journey["machine"]}
    with pytest.raises(ValueError, match="needs a remote service"):
        validate_machine("J2", retest)


def test_adoption_version_is_the_next_post_release():
    assert adoption_version("1.3.0") == "1.3.0.post1"
    assert adoption_version("1.3.0.post1") == "1.3.0.post2"
    with pytest.raises(ValueError):
        adoption_version("1.4.0rc1")


def test_the_adoption_guard_refuses_a_changed_index_binding_or_open_arguments(tmp_path):
    (tmp_path / ".agentic").mkdir()
    config = tmp_path / ".agentic/config.yaml"
    variables = {"kit_python": "/w/.venv/bin/python", "adoption_index_url": "http://127.0.0.1:1/simple"}
    config.write_text("kit:\n  interpreter: /w/.venv/bin/python\n  index_url: http://127.0.0.1:1/simple\n")
    guard_adoption_index(tmp_path, variables, ["agentic-kit", "kit", "update", "--version", "1.0.0", "--json"])
    with pytest.raises(ValueError, match="arguments_refused"):
        guard_adoption_index(tmp_path, variables, ["agentic-kit", "kit", "update", "--latest", "--json"])
    config.write_text("kit:\n  interpreter: /w/.venv/bin/python\n  index_url: https://pypi.org/simple\n")
    with pytest.raises(ValueError, match="binding_changed"):
        guard_adoption_index(tmp_path, variables, ["agentic-kit", "release", "ready", "--json"])


def test_a_release_run_is_local_only_in_the_release_fixture_of_a_journey():
    """J4: the runner confines the release fixture's remotes; the catalog rule stays remote."""
    plan = ["agentic-kit", "release", "run", "--version", "1.0.1", "--json"]
    signed = [*plan[:-1], "--execute", "--expected-signature", "abc", "--json"]
    entry = check_route(plan)
    assert journey_effects(plan, entry, "external_release") == ["push"]
    assert journey_effects(signed, entry, "external_release") == ["push"]
    assert set(journey_effects(plan, entry, "external_manifest")) >= {"merge", "release_publish"}
    assert set(journey_effects([*plan[:-1], "--root", "x", "--json"], entry, "external_release")) >= {"merge"}
    assert set(release_effects(signed, entry, "external_release")) >= {"merge", "release_publish"}  # catalog unchanged
    retest = {"commands": [" ".join(plan)], "workspace_kind": "external", "execution_class": "local",
              "machine": _journeys()["J4"]["machine"]}
    with pytest.raises(ValueError, match="needs a remote service"):
        validate_machine("J4", retest)


def test_a_release_run_asks_for_consent_only_through_a_signed_execution():
    plan = ["agentic-kit", "release", "run", "--version", "1.0.1", "--json"]
    assert not needs_consent(plan)
    assert needs_consent([*plan[:-1], "--execute", "--expected-signature", "abc", "--json"])


@pytest.mark.parametrize("change,message", [
    (lambda j: j["interruption"].update(step=0), "signed release run"),
    (lambda j: j["interruption"].update(blocked_step="C2"), "exactly BLOCKED"),
    (lambda j: j["interruption"].pop("cause"), "names step, blocked_step and cause"),
    (lambda j: j.pop("interruption"), "PASS, PLANNED or AWAITING_APPROVAL"),
    (lambda j: j["machine"]["steps"][6]["expect"]["json"].update(result_status="BLOCKED"),
     "PASS, PLANNED or AWAITING_APPROVAL"),
])
def test_only_the_declared_interruption_may_block(change, message):
    journey = json.loads(json.dumps(_journeys()["J4"]))
    change(journey)
    with pytest.raises(ValueError, match=message):
        validate(journey)


def test_the_release_fixture_refuses_a_remote_outside_the_run_root(tmp_path):
    import subprocess as sp

    from agentic_project_kit.greenfield_retest_release import guard_local_origin

    def run(argv, cwd, env):
        return sp.run(argv, cwd=cwd, env=env, capture_output=True, text=True)

    root = tmp_path / "workspace"
    root.mkdir()
    env = {**os.environ}
    sp.run(["git", "init", "-q"], cwd=root, check=True)
    sp.run(["git", "remote", "add", "origin", str(tmp_path / "origin.git")], cwd=root, check=True)
    guard_local_origin(root, tmp_path, env, run)
    sp.run(["git", "remote", "set-url", "--push", "origin", str(tmp_path / "origin.git.unreachable")], cwd=root, check=True)
    guard_local_origin(root, tmp_path, env, run)
    for url in ("https://github.com/vfi64/x.git", "git@github.com:vfi64/x.git", "/elsewhere/origin.git"):
        sp.run(["git", "remote", "set-url", "--push", "origin", url], cwd=root, check=True)
        with pytest.raises(ValueError, match="local_origin"):
            guard_local_origin(root, tmp_path, env, run)


def test_the_retest_environment_drops_gh_repository_overrides(tmp_path, monkeypatch):
    from agentic_project_kit.greenfield_retest import _environment

    monkeypatch.setenv("GH_REPO", "vfi64/agentic-project-kit")
    monkeypatch.setenv("GH_HOST", "github.com")
    env = _environment(tmp_path)
    assert "GH_REPO" not in env and "GH_HOST" not in env


@pytest.mark.parametrize("journey_id", sorted(_journeys()))
def test_every_journey_passes_with_the_installed_wheel(installed_kit, tmp_path, journey_id):
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}
    code = ("import json, sys; from agentic_project_kit.journey_contracts import run_journey; "
            "print(json.dumps(run_journey(sys.argv[1])))")
    done = subprocess.run([sys.executable, "-c", code, journey_id], cwd=tmp_path, env=env,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-2000:]
    record = json.loads(done.stdout)
    assert record["result"] == "PASS", json.dumps(record, indent=2, sort_keys=True)
