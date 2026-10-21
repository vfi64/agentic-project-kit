"""KIT-GF-070 and KIT-GF-077: executable external retests and declared remote-next push effects.

A consumer could only re-implement the Kit's fixtures or accept returncode 0 as proof, because
the retest catalog carried prose expectations and no execution class. The installed wheel now
runs machine contracts in a temporary workspace and never reports PASS for a retest it did not
prove.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentic_project_kit.greenfield_retest import (
    check_route,
    execution_class,
    json_path,
    run_machine,
    validate_machine,
)
from agentic_project_kit.greenfield_status import CATALOG, build, validate
from test_external_rule_registry import installed_kit as installed_kit

ROOT = Path(__file__).resolve().parents[1]
PILOT = ["KIT-GF-001", "KIT-GF-066", "KIT-GF-070", "KIT-GF-072", "KIT-GF-074", "KIT-GF-075", "KIT-GF-076", "KIT-GF-077"]
# external-retest-machine-contracts c1 (2026-10-21): local retests still without a machine contract.
# The set may only shrink; a new local finding needs its contract in the same slice.
LOCAL_WITHOUT_CONTRACT = {f"KIT-GF-{n}" for n in ("014", "015", "021", "026", "032", "036", "037", "042", "045",
                                                   "060", "063", "064", "067")}


def _catalog():
    return json.loads((ROOT / CATALOG).read_text())


def _finding(data, finding_id):
    return next(f for f in data["findings"] if f["id"] == finding_id)


def _retest(installed_kit, cwd, *args):
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}
    result = subprocess.run([sys.executable, "-m", "agentic_project_kit.cli", "greenfield", "retest", *args],
                            cwd=cwd, env=env, capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)


# --- the installed wheel ------------------------------------------------------------------------

def _contract_ids():
    return sorted(f["id"] for f in _catalog()["findings"] if "machine" in f["external_retest"])


@pytest.mark.parametrize("finding_id", _contract_ids())
def test_every_machine_contract_passes_with_the_installed_wheel(installed_kit, tmp_path, finding_id):
    rc, result = _retest(installed_kit, tmp_path, "--id", finding_id, "--json")
    record, = result["results"]
    assert rc == 0 and record["result"] == "PASS", (record.get("failures"), record.get("steps", [])[-1:])
    assert record["covers"] and record["steps"]


def test_only_the_named_local_retests_lack_a_contract():
    records = {f["id"]: f["external_retest"] for f in build(ROOT)["findings"]}
    missing = {i for i, r in records.items() if r["execution_class"] == "local" and "machine" not in r}
    assert missing == LOCAL_WITHOUT_CONTRACT


def test_every_pilot_contract_passes_with_the_installed_wheel_and_leaves_the_cwd_alone(installed_kit, tmp_path):
    cwd = tmp_path / "consumer"
    cwd.mkdir()
    rc, result = _retest(installed_kit, cwd, *[a for i in PILOT for a in ("--id", i)], "--json")
    assert rc == 0 and result["result_status"] == "PASS", [r for r in result["results"] if r["result"] != "PASS"]
    assert [r["id"] for r in result["results"]] == PILOT
    assert all(r["covers"] and r["steps"] for r in result["results"])
    assert result["executed_from"].startswith(str(installed_kit))
    assert list(cwd.iterdir()) == []


def test_unproved_retests_are_incomplete_never_pass(installed_kit, tmp_path):
    rc, result = _retest(installed_kit, tmp_path, "--id", "KIT-GF-014", "--id", "KIT-GF-073", "--id", "KIT-GF-055", "--json")
    assert rc == 3 and result["result_status"] == "INCOMPLETE"
    assert [r["result"] for r in result["results"]] == ["NO_MACHINE_CONTRACT", "NOT_RUN_LOCALLY", "NOT_RUN_LOCALLY"]
    assert [r["execution_class"] for r in result["results"]] == ["local", "owner_remote", "kit_release"]
    assert result["counts"]["PASS"] == 0


@pytest.mark.parametrize("args", [["--json"], ["--id", "KIT-GF-999", "--json"], ["--id", "KIT-GF-001", "--all", "--json"]])
def test_bad_selection_is_blocked(installed_kit, tmp_path, args):
    rc, result = _retest(installed_kit, tmp_path, *args)
    assert rc == 2 and result["result_status"] == "BLOCKED"


# --- the runner ---------------------------------------------------------------------------------

def test_a_wrong_expectation_fails_and_names_the_step():
    machine = copy.deepcopy(_finding(_catalog(), "KIT-GF-001")["external_retest"]["machine"])
    machine["steps"][2]["expect"]["json"]["status"] = "FAIL"
    result = run_machine(machine)
    assert result["result"] == "FAIL" and result["steps"][-1]["index"] == 2
    assert result["failures"] == ['status="PASS" != "FAIL"']


def test_a_missing_replace_text_fails_instead_of_passing_silently():
    machine = {"fixture": "external_manifest", "covers": "x", "steps": [
        {"replace": {"path": ".agentic/config.yaml", "old": "no such line", "new": "y"}}]}
    assert run_machine(machine)["result"] == "FAIL"


def test_the_runner_isolates_the_os_temp_root_and_names_the_kit_interpreter(tmp_path):
    # KIT-GF-028 and KIT-GF-021: a contract never sees other programs' temp files and may declare
    # the interpreter of the Kit that runs it.
    from agentic_project_kit.greenfield_retest import _environment

    env = _environment(tmp_path)
    assert env["TMPDIR"] == str(tmp_path / "os-tmp") and (tmp_path / "os-tmp").is_dir()
    machine = {"fixture": "git_repository", "covers": "x", "steps": [
        {"run": ["git", "config", "--global", "retest.python", "{kit_python}"]},
        {"run": ["git", "config", "--global", "retest.python"], "expect": {"stdout_equals": sys.executable}}]}
    assert run_machine(machine)["result"] == "PASS"
    retest = _finding(_catalog(), "KIT-GF-074")["external_retest"]
    validate_machine("KIT-GF-074", {**retest, "machine": {
        **retest["machine"], "steps": [*machine["steps"], *retest["machine"]["steps"]]}})
    with pytest.raises(ValueError, match="capture name"):
        validate_machine("KIT-GF-074", {**retest, "machine": {**retest["machine"], "steps": [
            {**retest["machine"]["steps"][0], "capture": {"kit_python": "result_status"}}]}})


def test_json_paths():
    document = {"a": [{"b": 1}], "c": {"d": "x"}}
    assert json_path(document, "a[0].b") == 1 and json_path(document, "c.d") == "x"
    for path in ("a[1].b", "c.e", "a.b"):
        with pytest.raises(KeyError):
            json_path(document, path)


# --- catalog validation -------------------------------------------------------------------------

def _invalid(change):
    data = _catalog()
    retest = _finding(data, "KIT-GF-074")["external_retest"]
    steps = retest["machine"]["steps"]
    if change == "unknown_route":
        retest["commands"] = ["agentic-kit transfer communication-context-status --json"]
    if change == "unknown_option":
        retest["commands"] = ["agentic-kit check --frobnicate"]
    if change == "remote_step":
        steps.append({"run": ["agentic-kit", "pr", "status", "1", "--json"]})
    if change == "foreign_program":
        steps.append({"run": ["bash", "-c", "true"]})
    if change == "unbound":
        steps.append({"run": ["git", "show", "{nothing}"]})
    if change == "self":
        steps.append({"run": ["agentic-kit", "greenfield", "retest", "--id", "KIT-GF-074", "--json"]})
    if change == "all":
        steps.append({"run": ["agentic-kit", "greenfield", "retest", "--all", "--json"]})
    if change == "escape":
        steps.append({"write": {"path": "../outside.txt", "text": "x"}})
    if change == "covers":
        retest["machine"]["covers"] = ""
    if change == "no_retest_route":
        retest["machine"]["steps"] = [{"run": ["git", "status"]}]
    if change == "remote_contract":
        _finding(data, "KIT-GF-073")["external_retest"]["machine"] = copy.deepcopy(retest["machine"])
    if change == "expectation_on_edit":
        steps.append({"write": {"path": "x", "text": "y"}, "expect": {"returncode": 0}})
    return data


@pytest.mark.parametrize("change", ["unknown_route", "unknown_option", "remote_step", "foreign_program", "unbound",
                                    "self", "all", "escape", "covers", "no_retest_route", "remote_contract",
                                    "expectation_on_edit"])
def test_invalid_contracts_are_rejected(change):
    with pytest.raises(ValueError):
        validate(_invalid(change), ROOT)


def test_a_hand_written_execution_class_must_match_the_manifest():
    data = _catalog()
    _finding(data, "KIT-GF-073")["external_retest"]["execution_class"] = "local"
    with pytest.raises(ValueError, match="execution class"):
        validate(data, ROOT)


def test_classes_are_derived_from_declared_effects():
    records = {f["id"]: f["external_retest"] for f in build(ROOT)["findings"]}
    assert records["KIT-GF-075"]["execution_class"] == "local"
    assert records["KIT-GF-073"]["execution_class"] == "owner_remote"
    assert records["KIT-GF-055"]["execution_class"] == "kit_release"
    assert all(r["execution_class"] == "local" for r in records.values() if "machine" in r)
    assert execution_class({"commands": ["agentic-kit release-publish --version 1.0.0 --dry-run --json"],
                            "workspace_kind": "external_manifest"})[0] == "owner_remote"
    validate_machine("KIT-GF-001", records["KIT-GF-001"])


# --- KIT-GF-077 ---------------------------------------------------------------------------------

def test_remote_next_and_remote_work_start_declare_their_push():
    assert check_route("agentic-kit transfer remote-next b --json")["remote_effects"] == ["fetch", "push"]
    assert check_route("agentic-kit transfer remote-work-start b")["remote_effects"] == ["fetch", "push"]
    entry = check_route("agentic-kit greenfield retest --id KIT-GF-001 --json")
    assert entry["remote_effects"] == ["none"] and entry["safety"] == "READ_ONLY"
