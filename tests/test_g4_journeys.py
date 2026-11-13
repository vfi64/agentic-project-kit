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

from agentic_project_kit.greenfield_retest import check_route
from agentic_project_kit.greenfield_retest_release_check import release_effects
from agentic_project_kit.journey_contracts import JOURNEY_IDS, approvals, journey_effects, load, validate

from test_external_rule_registry import installed_kit as installed_kit

PENDING = {"J2", "J4", "J5"}  # ratchet: shrinks only when a journey becomes a contract


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
    with pytest.raises(ValueError, match="PASS or PLANNED"):
        validate(journey)


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
