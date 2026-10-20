"""KIT-GF-081: `release abandon` gives up a stopped, unpublished release run through a Kit route.

Found when the first attempt of release 1.1.4 stopped in B4 (KIT-GF-079): the release branch had to
be deleted with transfer branch-delete and the run state moved aside by hand.
"""
import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_run import ReleaseRunOptions
from agentic_project_kit.release_run_abandon import abandon_release
from test_release_run import _assert_agentic_argv_options_exist, _state_path, _workspace

BRANCH = "codex/release-1.2.3"


class AbandonRunner:
    def __init__(self, **facts):
        self.facts = {"current": "main", "dirty": "", "local_tag": "", "remote_tag": "", "release_rc": 1,
                      "remote_head": "rel-head", "local_head": "rel-head",
                      "prs": [{"number": 40, "state": "OPEN"}], "pr_view": "closed\tnone", **facts}
        self.calls: list[list[str]] = []

    def __call__(self, argv, cwd):
        command = [str(a) for a in argv]
        self.calls.append(command)
        f = self.facts
        if command[:3] == ["git", "tag", "-l"]:
            return self._done(command, f["local_tag"])
        if command[:3] == ["git", "ls-remote", "--tags"]:
            return self._done(command, f["remote_tag"])
        if command[:3] == ["git", "ls-remote", "--heads"]:
            return self._done(command, f"{f['remote_head']}\trefs/heads/{BRANCH}" if f["remote_head"] else "")
        if command[:2] == ["git", "rev-parse"]:
            return self._done(command, f["local_head"], rc=0 if f["local_head"] else 1)
        if command[:3] == ["git", "branch", "--show-current"]:
            return self._done(command, f["current"])
        if command[:2] == ["git", "status"]:
            return self._done(command, f["dirty"])
        if command[:2] == ["gh", "api"] and "releases/tags" in command[2]:
            rc = f["release_rc"]
            return self._done(command, "123" if rc == 0 else "", "" if rc == 0 else f.get("release_err", "gh: Not Found (HTTP 404)"), rc)
        if command[:2] == ["gh", "api"] and "/pulls/" in command[2]:
            return self._done(command, f["pr_view"])
        if "pr-existing-for-branch" in command:
            prs = f["prs"]
            status = "PASS" if len(prs) == 1 else ("MISS" if not prs else "BLOCKED")
            blockers = ["multiple_existing_prs_found"] if len(prs) > 1 else []
            return self._done(command, json.dumps({"result_status": status, "prs": prs, "blockers": blockers,
                                                   "pr_number": prs[0]["number"] if len(prs) == 1 else None}),
                              rc=0 if status == "PASS" else 2)
        if "branch-delete" in command:
            return self._done(command, json.dumps({"result_status": f.get("delete_status", "PASS")}))
        raise AssertionError(command)

    @staticmethod
    def _done(command, stdout="", stderr="", rc=0):
        return subprocess.CompletedProcess(command, rc, stdout + ("\n" if stdout else ""), stderr)


def _stopped_run(root: Path, *, approvals=("B4",), finished=("A1", "A2", "A3", "B1", "B2", "B3")) -> Path:
    _workspace(root)
    path = _state_path(root)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version": "1.2.3", "finished_steps": list(finished),
                                "approvals": [{"step_id": step, "gate": {}} for step in approvals]}))
    steps = path.parent / "release-run-1.2.3-steps"
    steps.mkdir()
    (steps / "B4.json").write_text("{}")
    path.with_suffix(".log").write_text("{}\n")
    return path


def _abandon(root, runner, **extra):
    return abandon_release(ReleaseRunOptions(version="1.2.3", root=root, **extra), runner=runner, sleep=lambda _: None)


def test_the_plan_names_branch_pr_and_archive_and_changes_nothing_remote(tmp_path):
    state = _stopped_run(tmp_path)
    runner = AbandonRunner()
    plan = _abandon(tmp_path, runner)
    gate = plan["gate"]
    assert plan["result_status"] == "AWAITING_APPROVAL" and plan["blockers"] == []
    assert (gate["branch"], gate["pr_number"], gate["remote_head"], gate["local_head"]) == (BRANCH, 40, "rel-head", "rel-head")
    assert gate["archive"].startswith(".agentic/tmp/release-run-archive/1.2.3-")
    assert not any("branch-delete" in c for c in runner.calls) and state.is_file()
    assert "--expected-signature " + gate["approval_signature"] in plan["next_action"]


def test_execute_deletes_the_branch_checks_the_pr_and_archives_the_state(tmp_path):
    state = _stopped_run(tmp_path)
    runner = AbandonRunner()
    gate = _abandon(tmp_path, runner)["gate"]
    result = _abandon(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"],
                      approved_by="owner", consent_source="owner decision")
    assert result["result_status"] == "PASS", result
    deletes = [c for c in runner.calls if "branch-delete" in c]
    assert [c[c.index("branch-delete") + 1:] for c in deletes] == [[BRANCH, "--remote", "--json"], [BRANCH, "--force", "--json"]]
    for call in deletes:
        _assert_agentic_argv_options_exist(call)
    archive = tmp_path / result["archive"]
    assert sorted(p.name for p in archive.iterdir()) == ["abandon.json", "release-run-1.2.3-steps", "release-run-1.2.3.json",
                                                          "release-run-1.2.3.log"]
    record = json.loads((archive / "abandon.json").read_text())
    assert (record["approved_by"], record["consent_source"], record["gate"]["pr_number"]) == ("owner", "owner decision", 40)
    assert not state.exists() and not (state.parent / "release-run-1.2.3-steps").exists()
    assert _abandon(tmp_path, runner)["blockers"] == ["release-run-state-missing"]   # a new run starts fresh


@pytest.mark.parametrize("facts,state_kwargs,blocker", [
    ({"local_tag": "v1.2.3"}, {}, "release-already-tagged"),
    ({"remote_tag": "abc\trefs/tags/v1.2.3"}, {}, "release-already-tagged"),
    ({"release_rc": 0}, {}, "release-already-published"),
    ({"release_err": "HTTP 502"}, {}, "github-release-check-unavailable"),
    ({}, {"approvals": ("B4", "C2")}, "release-publication-started"),
    ({}, {"finished": ("A1", "B4", "C1", "C2")}, "release-publication-started"),
    ({"prs": [{"number": 40, "state": "MERGED"}]}, {}, "release-pr-merged"),
    ({"prs": [{"number": 40, "state": "OPEN"}, {"number": 41, "state": "OPEN"}]}, {}, "multiple-open-release-prs"),
    ({"current": BRANCH}, {}, "release-branch-checked-out"),
    ({"dirty": " M pyproject.toml"}, {}, "worktree-not-clean"),
    ({"remote_head": ""}, {}, "release-pr-open-without-branch"),
])
def test_an_abandon_that_may_touch_something_published_blocks(tmp_path, facts, state_kwargs, blocker):
    _stopped_run(tmp_path, **state_kwargs)
    runner = AbandonRunner(**facts)
    plan = _abandon(tmp_path, runner)
    assert plan["result_status"] == "BLOCKED" and blocker in plan["blockers"], plan["blockers"]
    signature = (plan["gate"] or {}).get("approval_signature", "")
    executed = _abandon(tmp_path, runner, execute=True, expected_signature=signature, approved_by="o", consent_source="c")
    assert executed["result_status"] == "BLOCKED"
    assert not any("branch-delete" in c for c in runner.calls)


def test_a_closed_older_pr_does_not_block_and_no_pr_means_branch_only(tmp_path):
    _stopped_run(tmp_path)
    runner = AbandonRunner(prs=[{"number": 39, "state": "CLOSED"}])
    plan = _abandon(tmp_path, runner)
    assert plan["result_status"] == "AWAITING_APPROVAL" and plan["gate"]["pr_number"] is None


def test_execute_needs_the_signature_and_an_attributed_consent(tmp_path):
    _stopped_run(tmp_path)
    runner = AbandonRunner()
    gate = _abandon(tmp_path, runner)["gate"]
    wrong = _abandon(tmp_path, runner, execute=True, expected_signature="0" * 24, approved_by="o", consent_source="c")
    unattributed = _abandon(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"])
    assert wrong["blockers"] == ["approval-signature-mismatch"]
    assert unattributed["blockers"] == ["approval-attribution-missing"]
    assert not any("branch-delete" in c for c in runner.calls)


def test_a_pr_that_stays_open_stops_before_the_state_is_archived(tmp_path):
    state = _stopped_run(tmp_path)
    runner = AbandonRunner(pr_view="open\tnone")
    gate = _abandon(tmp_path, runner)["gate"]
    result = _abandon(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"],
                      approved_by="o", consent_source="c")
    assert result["blockers"] == ["release-pr-still-open"] and state.is_file()
    assert not any("--force" in c for c in runner.calls)


def test_without_a_run_there_is_nothing_to_abandon(tmp_path):
    _workspace(tmp_path)
    assert _abandon(tmp_path, AbandonRunner())["blockers"] == ["release-run-state-missing"]


def test_the_cli_route_is_registered_as_a_destructive_orchestrator(tmp_path, monkeypatch):
    from agentic_project_kit.command_manifest import build_reference_from_app

    command = next(c for c in build_reference_from_app(app)["commands"] if c["qualified_name"] == "agentic-kit release abandon")
    assert (command["safety"], command["surface"]) == ("DESTRUCTIVE", "orchestrator")
    assert command["remote_effects"] == ["delete_remote", "network_read", "push"]
    _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["release", "abandon", "--version", "1.2.3", "--json"])
    assert result.exit_code == 2 and json.loads(result.stdout)["blockers"] == ["release-run-state-missing"]
