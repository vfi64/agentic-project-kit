"""Shared authority, advisory selection, observation boundaries and migration."""

import copy
import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import (
    build_current_reference,
    manifest_identity,
    manifest_sha,
)
from agentic_project_kit.command_selector import select_for_intent, select_for_raw, select_for_task
from agentic_project_kit.site_task_routes import task_navigation, render_task_navigation
from agentic_project_kit.task_routes import task_routes_export
from agentic_project_kit.task_selection_facts import observe_facts


def fixture():
    m = build_current_reference()
    return m, {
        "root": "/fixture",
        "current_root": "/fixture",
        "observed_head": "a" * 40,
        "current_head": "a" * 40,
        "manifest_sha": m["meta"]["manifest_sha"],
        "repository": "owner/repo",
        "pr": {"repository": "owner/repo", "number": 7, "head": "b" * 40},
    }


def sample(row):
    values = {
        "nonempty_string": "fixture",
        "positive_integer": 7,
        "full_commit": "b" * 40,
        "stable_version": "1.2.3",
        "nonempty_string_list": ["file.py"],
    }
    return {k: values[v] for k, v in row["inputs"].items()}


def rehash(m):
    m["meta"]["manifest_sha"] = manifest_identity(m)


@pytest.mark.parametrize("row", task_routes_export()["routes"], ids=lambda r: r["task"])
def test_every_shared_route_and_site_agree_without_execution(row, monkeypatch):
    m, c = fixture()
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: pytest.fail("pure selection performed I/O")
    )
    result = select_for_intent(m, row["task"], row["when"], sample(row), c).payload
    web = next(r for r in task_navigation(m)["routes"] if r["task"] == row["task"])
    assert result["result_status"] == "MATCH", result
    assert result["command"] == web["command"]
    assert result["contract"] == web["contract"]
    assert result["execution_authorized"] is False
    assert "argv" not in result


@pytest.mark.parametrize(
    "change,status",
    [
        ("missing", "NEEDS_FACTS"),
        ("wrong", "BLOCKED"),
        ("inputs", "NEEDS_INPUTS"),
        ("unknown", "UNKNOWN_TASK"),
        ("bad", "INVALID_INPUT"),
        ("head", "NEEDS_FACTS"),
        ("root", "NEEDS_FACTS"),
        ("identity", "INVALID_INPUT"),
    ],
)
def test_closed_failure_states(change, status):
    m, c = fixture()
    task = "finish_work"
    facts = {"workspace_mode": "managed", "branch_role": "work"}
    row = next(r for r in m["task_routes"]["routes"] if r["task"] == task)
    inputs = sample(row)
    if change == "missing":
        facts = {}
    if change == "wrong":
        facts["branch_role"] = "main"
    if change == "inputs":
        inputs = {}
    if change == "unknown":
        task = "invented"
    if change == "bad":
        inputs["execute"] = True
    if change == "head":
        c["current_head"] = "c" * 40
    if change == "root":
        c["current_root"] = "/different"
    if change == "identity":
        c["manifest_sha"] = "other"
    result = select_for_intent(m, task, facts, inputs, c).payload
    assert result["result_status"] == status
    assert result["execution_authorized"] is False


@pytest.mark.parametrize("unknown", [False, True])
def test_ambiguity_and_unresolved_alternative_never_choose_first(unknown):
    m, c = fixture()
    alternative = copy.deepcopy(m["task_routes"]["routes"][0])
    if unknown:
        alternative["when"]["pr_state"] = "open"
    m["task_routes"]["routes"].append(alternative)
    rehash(m)
    c["manifest_sha"] = m["meta"]["manifest_sha"]
    assert select_for_intent(m, "check_work", {"workspace_mode": "managed"}, {}, c).status == (
        "NEEDS_FACTS" if unknown else "AMBIGUOUS"
    )


@pytest.mark.parametrize("change", ["route", "schema", "command", "phase", "consent"])
def test_identity_and_schema_errors_fail_in_both_consumers(change):
    m, c = fixture()
    if change == "route":
        m["task_routes"]["routes"][0]["command"] = "agentic-kit doctor"
    if change == "schema":
        m["task_routes"]["schema_version"] = 99
        rehash(m)
    if change == "command":
        m["task_routes"]["routes"][0]["command"] = "missing"
        rehash(m)
    if change == "phase":
        m["task_routes"]["routes"][-1]["phase"] = "planning"
        rehash(m)
    if change == "consent":
        m["task_routes"]["routes"][-1]["inputs"]["execute"] = "nonempty_string"
        rehash(m)
    c["manifest_sha"] = m["meta"]["manifest_sha"]
    assert select_for_intent(m, "check_work", {}, {}, c).status == "INVALID_INPUT"
    with pytest.raises(ValueError):
        task_navigation(m)


def test_schema2_raw_and_tags_preserved_but_no_intent_downgrade():
    m, c = fixture()
    legacy = copy.deepcopy(m)
    legacy.pop("task_routes")
    legacy["schema_version"] = 2
    rehash(legacy)
    assert manifest_identity(legacy) == manifest_sha(legacy["commands"])
    assert select_for_raw(m, "git push origin main") == select_for_raw(
        legacy, "git push origin main"
    )
    assert select_for_task(m, "transfer") == select_for_task(legacy, "transfer")
    assert select_for_intent(legacy, "check_work", {}, {}, c).status == "INVALID_INPUT"
    assert task_navigation(legacy)["availability"] == "legacy_manifest"


def test_route_hash_and_defensive_export():
    m, _ = fixture()
    old = m["meta"]["manifest_sha"]
    m["task_routes"]["routes"][0]["when"] = {}
    assert manifest_identity(m) != old
    export = task_routes_export()
    export["routes"].clear()
    assert task_routes_export()["routes"]


@pytest.mark.parametrize("change", ["number", "repository", "head", "missing"])
def test_pr_observation_is_identity_bound(change):
    m, c = fixture()
    inputs = {"pr_number": 7, "expected_head_sha": "b" * 40}
    if change == "number":
        c["pr"]["number"] = 8
    if change == "repository":
        c["pr"]["repository"] = "other/repo"
    if change == "head":
        c["pr"]["head"] = "c" * 40
    if change == "missing":
        c.pop("pr")
    assert (
        select_for_intent(
            m, "complete_open_pr", {"workspace_mode": "managed", "pr_state": "open"}, inputs, c
        ).status
        == "NEEDS_FACTS"
    )


def init_repo(root):
    root.mkdir(exist_ok=True)
    for args in (
        ["init", "-b", "trunk"],
        ["config", "user.name", "Fixture"],
        ["config", "user.email", "fixture@example.invalid"],
        ["commit", "--allow-empty", "-m", "fixture"],
        ["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"],
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    (root / ".agentic").mkdir()
    (root / ".agentic/config.yaml").write_text(
        "kit_schema_version: 2\nprofile: generic\npublication: none\nhygiene:\n  doc_lifecycle: warn\n"
    )


def test_local_observation_and_cli_preserve_files(tmp_path):
    init_repo(tmp_path)
    m, _ = fixture()
    before = subprocess.check_output(["git", "-C", str(tmp_path), "status", "--short"])
    facts, c = observe_facts(tmp_path, m, {})
    assert facts["branch_role"] == "main"  # configured default trunk, no main heuristic
    assert facts["workspace_mode"] == "managed"
    assert "pr_state" not in facts
    result = CliRunner().invoke(
        app, ["command-for", "--root", str(tmp_path), "--intent", "check_work", "--json"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["execution_authorized"] is False
    assert subprocess.check_output(["git", "-C", str(tmp_path), "status", "--short"]) == before
    missing = CliRunner().invoke(
        app, ["command-for", "--root", str(tmp_path), "--intent", "complete_open_pr", "--json"]
    )
    assert missing.exit_code == 2
    assert json.loads(missing.output)["result_status"] == "NEEDS_FACTS"


@pytest.mark.parametrize("inputs", ["[]", "bad", '{"execute": true}'])
def test_cli_invalid_inputs_structured(tmp_path, inputs):
    init_repo(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "command-for",
            "--intent",
            "check_work",
            "--root",
            str(tmp_path),
            "--inputs",
            inputs,
            "--json",
        ],
    )
    assert result.exit_code == 2
    assert json.loads(result.output)["result_status"] == "INVALID_INPUT"


def test_nested_root_and_detached_head_do_not_guess(tmp_path):
    init_repo(tmp_path)
    m, _ = fixture()
    nested = tmp_path / "nested"
    nested.mkdir()
    assert observe_facts(nested, m, {})[0] == {}
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "--detach"], check=True, capture_output=True
    )
    assert "branch_role" not in observe_facts(tmp_path, m, {})[0]


def test_existing_release_state_or_tag_blocks_fresh_route(tmp_path):
    init_repo(tmp_path)
    m, c = fixture()
    (tmp_path / ".agentic/tmp").mkdir()
    state = tmp_path / ".agentic/tmp/release-run-1.2.3.json"
    state.write_text("broken")
    facts, c = observe_facts(tmp_path, m, {"version": "1.2.3"})
    assert facts["release_state"] == "prepared"
    assert (
        select_for_intent(m, "release_version", facts, {"version": "1.2.3"}, c).status == "BLOCKED"
    )


def test_explicit_pr_read_pinned_to_origin_and_head(monkeypatch, tmp_path):
    import agentic_project_kit.task_selection_facts as adapter

    init_repo(tmp_path)
    m, _ = fixture()
    real = adapter._read
    calls = []
    monkeypatch.setattr(adapter, "detect_origin_github_repo", lambda root: "owner/repo")

    def read(root, argv):
        if argv[0] != "gh":
            return real(root, argv)
        calls.append(argv)
        return json.dumps(
            {
                "number": 7,
                "state": "OPEN",
                "headRefOid": "b" * 40,
                "url": "https://github.com/owner/repo/pull/7",
            }
        )

    monkeypatch.setattr(adapter, "_read", read)
    inputs = {"pr_number": 7, "expected_head_sha": "b" * 40}
    facts, c = adapter.observe_facts(tmp_path, m, inputs)
    assert calls == [] and "pr_state" not in facts
    facts, c = adapter.observe_facts(tmp_path, m, inputs, observe_pr=True)
    assert calls == [
        ["gh", "pr", "view", "7", "--repo", "owner/repo", "--json", "number,state,headRefOid,url"]
    ]
    assert select_for_intent(m, "complete_open_pr", facts, inputs, c).status == "MATCH"


def test_website_escaping_and_data_binding():
    m, _ = fixture()
    projection = task_navigation(m)
    assert len(projection["routes"]) == 11
    before = render_task_navigation(projection)
    projection["routes"][0]["review_note"] = "<script>bad</script>"
    after = render_task_navigation(projection)
    assert before != after and "<script>" not in after


def test_head_or_worktree_race_invalidates_observation(monkeypatch, tmp_path):
    import agentic_project_kit.task_selection_facts as adapter

    init_repo(tmp_path)
    m, _ = fixture()
    real = adapter._read
    seen = 0

    def read(root, argv):
        nonlocal seen
        if argv[1:] == ["status", "--porcelain", "--untracked-files=all"]:
            seen += 1
            return "" if seen == 1 else " M changed"
        return real(root, argv)

    monkeypatch.setattr(adapter, "_read", read)
    facts, context = adapter.observe_facts(tmp_path, m, {})
    assert select_for_intent(m, "check_work", facts, {}, context).status == "NEEDS_FACTS"


@pytest.mark.parametrize(
    "payload",
    [
        "null",
        "broken",
        '{"number": 8}',
        '{"number": 7, "state": "OPEN", "headRefOid": "short", "url": "https://github.com/owner/repo/pull/7"}',
    ],
)
def test_missing_or_malformed_pr_observation_stays_unknown(monkeypatch, tmp_path, payload):
    import agentic_project_kit.task_selection_facts as adapter

    init_repo(tmp_path)
    m, _ = fixture()
    real = adapter._read
    monkeypatch.setattr(adapter, "detect_origin_github_repo", lambda root: "owner/repo")
    monkeypatch.setattr(
        adapter, "_read", lambda root, argv: payload if argv[0] == "gh" else real(root, argv)
    )
    inputs = {"pr_number": 7, "expected_head_sha": "b" * 40}
    facts, c = adapter.observe_facts(tmp_path, m, inputs, observe_pr=True)
    assert "pr_state" not in facts
    assert select_for_intent(m, "complete_open_pr", facts, inputs, c).status == "NEEDS_FACTS"


def test_text_and_json_carry_same_advisory_payload(tmp_path):
    init_repo(tmp_path)
    args = ["command-for", "--root", str(tmp_path), "--intent", "check_work"]
    json_result = CliRunner().invoke(app, [*args, "--json"])
    text_result = CliRunner().invoke(app, args)
    assert json_result.exit_code == text_result.exit_code == 0
    assert json.loads(text_result.output.split("\n", 1)[1]) == json.loads(json_result.output)


def test_invalid_workspace_and_manifest_contract_are_structured(tmp_path):
    init_repo(tmp_path)
    (tmp_path / ".agentic/config.yaml").write_text("kit_schema_version: 999\n")
    result = CliRunner().invoke(
        app, ["command-for", "--root", str(tmp_path), "--intent", "check_work", "--json"]
    )
    assert result.exit_code == 2
    assert json.loads(result.output)["result_status"] == "INVALID_INPUT"
    m, c = fixture()
    m["commands"][0].pop("surface")
    rehash(m)
    c["manifest_sha"] = m["meta"]["manifest_sha"]
    assert select_for_intent(m, "check_work", {}, {}, c).status == "INVALID_INPUT"


def test_historical_proposal_is_not_a_production_input(monkeypatch):
    from pathlib import Path

    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.name == "TASK_COMMAND_SELECTION_PROPOSAL.yaml":
            pytest.fail("runtime read the archived proposal")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    m, c = fixture()
    assert (
        select_for_intent(m, "check_work", {"workspace_mode": "managed"}, {}, c).status == "MATCH"
    )
    assert task_navigation(m)["routes"]


def test_pre_schema3_consumer_cannot_verify_new_route_identity():
    m, _ = fixture()
    assert manifest_sha(m["commands"]) != m["meta"]["manifest_sha"]
    assert m["schema_version"] == 3
    assert m["meta"]["schema_version"] == 2


def test_website_partition_keeps_unassigned_commands_discoverable():
    m, _ = fixture()
    navigation = task_navigation(m)
    assigned = {r["command"] for r in navigation["routes"]}
    unassigned = set(navigation["unassigned_commands"])
    assert not assigned & unassigned
    assert assigned | unassigned == {c["qualified_name"] for c in m["commands"]}
    assert 'href="index.html"' in render_task_navigation(navigation)
    assert 'href="diagnostics.html"' in render_task_navigation(navigation)
