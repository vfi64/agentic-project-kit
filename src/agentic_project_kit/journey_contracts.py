"""G4 (owner plan 2026-11-13): fixed workflows run as machine contracts against the installed Kit.

A journey is a machine contract in ``reference/journeys.json`` that walks one standard path in a
disposable workspace with a local bare origin, using the retest runner of KIT-GF-070. Two measures
per journey:

- blocked: every Kit step expects PASS, PLANNED or AWAITING_APPROVAL, so a BLOCKED fails the
  contract (baseline 0);
- approvals: owner consents the journey needs (owner decision 2026-11-13): a Kit step counts when
  it executes a signed plan (``--execute`` with ``--expected-signature``) or when its catalog
  effects go beyond none/fetch/push/network_read; a read-only plan is no consent. A step with remote
  effects runs here as its dry run; the declared baseline must match exactly.

Offline the journeys stop at the GitHub boundary: ``work finish`` runs as dry run (PLANNED). The
catalog rule (``release_effects``) is unchanged; only journeys treat a dry-run work finish, and an
exact ``kit update`` against the adoption fixture's loopback index (J2), as local.
"""
from __future__ import annotations

import json
import shlex
from importlib.resources import files
from typing import Any

from agentic_project_kit.greenfield_retest import LOCAL_EFFECTS, check_route, run_machine, validate_machine
from agentic_project_kit.greenfield_retest_adoption import adoption_effects
from agentic_project_kit.greenfield_retest_release_check import release_effects

JOURNEY_IDS = ("J1", "J2", "J3", "J4", "J5")
STEP_STATUSES = frozenset({"PASS", "PLANNED", "AWAITING_APPROVAL"})
CONSENT_FREE_EFFECTS = LOCAL_EFFECTS | {"network_read"}
# Routes whose output is a record without result_status; such a step must exit 0.
NO_STATUS_ROUTES = frozenset({("rules", "acknowledge")})


def load() -> dict[str, Any]:
    return json.loads(files("agentic_project_kit.reference").joinpath("journeys.json").read_text("utf-8"))


def journey_effects(command, entry, fixture=None) -> list[str]:
    argv = shlex.split(command) if isinstance(command, str) else list(command)
    if tuple(entry["path"]) == ("work", "finish") and "--execute" not in argv:
        return ["fetch"]  # dry run: plan plus `git ls-remote origin HEAD`
    local = adoption_effects(argv, entry, fixture)
    return local if local is not None else release_effects(argv, entry, fixture)


def _kit_steps(journey: dict[str, Any]) -> list[list[str]]:
    return [step["run"] for step in journey["machine"]["steps"] if step.get("run", [""])[0] == "agentic-kit"]


def validate(journey: dict[str, Any], routes=None) -> None:
    commands = [shlex.join(argv) for argv in _kit_steps(journey)]
    if not commands:
        raise ValueError(f"{journey['id']}: a journey runs Kit routes")
    retest = {"commands": commands, "workspace_kind": "external", "execution_class": "local",
              "machine": journey["machine"]}
    validate_machine(journey["id"], retest, routes, effects=journey_effects)
    for step in journey["machine"]["steps"]:
        if step.get("run", [""])[0] == "agentic-kit":
            if tuple(check_route(step["run"], routes)["path"]) in NO_STATUS_ROUTES:
                if step.get("expect") != {"returncode": 0}:
                    raise ValueError(f"{journey['id']}: a step without result status expects exactly returncode 0")
                continue
            status = step.get("expect", {}).get("json", {}).get("result_status")
            if status not in STEP_STATUSES:
                raise ValueError(
                    f"{journey['id']}: every Kit step expects result_status PASS, PLANNED or AWAITING_APPROVAL"
                )


def needs_consent(argv: list[str], routes=None, fixture=None) -> bool:
    if "--execute" in argv and "--expected-signature" in argv:
        return True
    return bool(set(release_effects(argv, check_route(argv, routes), fixture)) - CONSENT_FREE_EFFECTS)


def approvals(journey: dict[str, Any], routes=None) -> int:
    fixture = journey["machine"]["fixture"]
    return sum(needs_consent(argv, routes, fixture) for argv in _kit_steps(journey))


def run_journey(journey_id: str) -> dict[str, Any]:
    journey = next(j for j in load()["journeys"] if j["id"] == journey_id)
    validate(journey)
    return {"id": journey_id, **run_machine(journey["machine"])}
