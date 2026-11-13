"""G4 (owner plan 2026-11-13): fixed workflows run as machine contracts against the installed Kit.

A journey is a machine contract in ``reference/journeys.json`` that walks one standard path in a
disposable workspace with a local bare origin, using the retest runner of KIT-GF-070. Two measures
per journey:

- blocked: every Kit step expects PASS or PLANNED, so a BLOCKED fails the contract (baseline 0);
- approvals: owner consents the journey needs, i.e. Kit steps whose route declares effects beyond
  none/fetch/push. Such a step runs here as its dry run; the declared baseline must match exactly.

Offline the journeys stop at the GitHub boundary: ``work finish`` runs as dry run (PLANNED). The
catalog rule (``release_effects``) is unchanged; only journeys treat a dry-run work finish as local.
"""
from __future__ import annotations

import json
import shlex
from importlib.resources import files
from typing import Any

from agentic_project_kit.greenfield_retest import LOCAL_EFFECTS, check_route, run_machine, validate_machine
from agentic_project_kit.greenfield_retest_release_check import release_effects

JOURNEY_IDS = ("J1", "J2", "J3", "J4", "J5")


def load() -> dict[str, Any]:
    return json.loads(files("agentic_project_kit.reference").joinpath("journeys.json").read_text("utf-8"))


def journey_effects(command, entry, fixture=None) -> list[str]:
    argv = shlex.split(command) if isinstance(command, str) else list(command)
    if tuple(entry["path"]) == ("work", "finish") and "--execute" not in argv:
        return ["fetch"]  # dry run: plan plus `git ls-remote origin HEAD`
    return release_effects(argv, entry, fixture)


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
            status = step.get("expect", {}).get("json", {}).get("result_status")
            if status not in {"PASS", "PLANNED"}:
                raise ValueError(f"{journey['id']}: every Kit step expects result_status PASS or PLANNED")


def approvals(journey: dict[str, Any], routes=None) -> int:
    fixture = journey["machine"]["fixture"]
    return sum(
        bool(set(release_effects(argv, check_route(argv, routes), fixture)) - LOCAL_EFFECTS)
        for argv in _kit_steps(journey)
    )


def run_journey(journey_id: str) -> dict[str, Any]:
    journey = next(j for j in load()["journeys"] if j["id"] == journey_id)
    validate(journey)
    return {"id": journey_id, **run_machine(journey["machine"])}
