"""KIT-GF-079 and KIT-GF-080, found in the Kit's own release 1.1.4.

079: the required `test` job starts only after the CI shards (`needs:`), so GitHub creates its
check late. `pr wait-ci` saw every visible check green and reported READY_TO_MERGE while `test`
did not exist yet; `merge-if-green` then saw UNSTABLE and refused. Declared
`gates.required_checks` must now be present before readiness passes.

080: B4 had committed, pushed and opened the release PR when it stopped; a new run blocked with
`changed-paths-drift`. B4 now completes its own open release PR when the branch holds the commits
B4 writes on the approved base (the release commit with exactly the approved paths, then projection
commits that touch only their projection; K7 generalised the original "exactly two") and main has
not moved. The stop before the PR is K7 (tests/test_k7_release_b4_resume.py).
"""
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from agentic_project_kit.ci_light_skip import declared_required_checks
from agentic_project_kit.ci_readiness import classify_pr_readiness
from agentic_project_kit.cli import app
from agentic_project_kit.handoff_closeout import handoff_closeout_paths
from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from agentic_project_kit.workspace import load_workspace
from test_release_run import FakeRunner, _assert_agentic_argv_options_exist, _state_path, _workspace

ROOT = Path(__file__).resolve().parents[1]


# --- KIT-GF-079 ---------------------------------------------------------------------------------

def _snapshot(*checks):
    return {"state": "OPEN", "headRefOid": "h", "mergeStateStatus": "CLEAN", "mergeable": "MERGEABLE",
            "statusCheckRollup": [{"name": n, "status": "COMPLETED", "conclusion": c} for n, c in checks]}


SHARDS = [("classify", "SUCCESS"), ("test-shard (0)", "SUCCESS"), ("test-shard (1)", "SUCCESS"),
          ("test-shard (2)", "SUCCESS"), ("pytest-parallel-shadow", "SKIPPED")]


def test_a_required_check_that_does_not_exist_yet_keeps_readiness_waiting():
    early = classify_pr_readiness(_snapshot(*SHARDS), expected_checks=("test",), light_path_skipped=frozenset())
    assert early.outcome == "WAITING" and early.reasons == ("expected check missing: test",)
    done = classify_pr_readiness(_snapshot(*SHARDS, ("test", "SUCCESS")), expected_checks=("test",),
                                 light_path_skipped=frozenset())
    assert done.outcome == "READY_TO_MERGE"


def test_pr_wait_ci_waits_for_the_declared_required_checks(tmp_path, monkeypatch):
    _workspace(tmp_path)
    config = tmp_path / ".agentic/config.yaml"
    config.write_text(config.read_text() + "gates:\n  required_checks:\n    - test\n")
    seen = {}

    def fake_wait(provider, **kwargs):
        seen.update(kwargs)
        raise SystemExit(0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agentic_project_kit.cli_commands.pr.wait_for_pr_readiness", fake_wait)
    CliRunner().invoke(app, ["pr", "wait-ci", "7", "--expected-check", "lint"])
    assert seen["expected_checks"] == ("lint", "test")
    assert declared_required_checks(tmp_path) == ("test",)


@pytest.mark.parametrize("value", ["[test, test]", "['']", "test"])
def test_invalid_required_checks_are_refused(tmp_path, value):
    _workspace(tmp_path)
    config = tmp_path / ".agentic/config.yaml"
    config.write_text(config.read_text() + f"gates:\n  required_checks: {value}\n")
    from agentic_project_kit.workspace import load_workspace

    with pytest.raises(RuntimeError):
        load_workspace(tmp_path, suppress_legacy_profile_warning=True)
    assert declared_required_checks(tmp_path) == ()


def test_the_kit_declares_its_required_test_check():
    gates = yaml.safe_load((ROOT / ".agentic/config.yaml").read_text())["gates"]
    assert gates["required_checks"] == ["test"]


# --- KIT-GF-080 ---------------------------------------------------------------------------------

BRANCH = "codex/release-1.2.3"
PATHS = ["CHANGELOG.md", "pyproject.toml"]


def handoff_paths(root):
    workspace = load_workspace(Path(root), suppress_legacy_profile_warning=True)
    return [workspace.path_text(path) for path in handoff_closeout_paths(workspace)]


class ResumeRunner(FakeRunner):
    """Git and GitHub state after a stopped B4; commits form a linear chain on base-sha."""

    def __init__(self, *, main="base-sha", commits=("c1", "rel-head"), paths=PATHS,
                 subjects=("Prepare release 1.2.3", "Refresh handoff for Release 1.2.3"), pr=True,
                 remote_branch="rel-head", head=None, current_branch=BRANCH, status="", commit_paths=None,
                 parents=None):
        super().__init__()
        self.main, self.commits, self.paths, self.subjects = main, commits, paths, dict(zip(commits, subjects))
        self.pr, self.remote_branch, self.current_branch, self.status = pr, remote_branch, current_branch, status
        self.head = head or (commits[-1] if commits else "base-sha")
        self.commit_paths = commit_paths or {}
        self.parents = parents or dict(zip(commits, ("base-sha", *commits[:-1])))

    def __call__(self, argv, cwd):
        command = [str(a) for a in argv]
        reply, rc = None, 0
        if "pr-existing-for-branch" in command:
            reply = json.dumps({"result_status": "PASS", "pr_number": 40} if self.pr else {"result_status": "MISS"})
            rc = 0 if self.pr else 2
        elif command[:3] == ["gh", "pr", "view"]:
            reply = json.dumps({"headRefOid": "rel-head", "headRefName": BRANCH, "baseRefName": "main", "state": "OPEN"})
        elif command[:2] == ["git", "ls-remote"]:
            lines = [f"{self.remote_branch}\trefs/heads/{BRANCH}"] if self.remote_branch else []
            reply = "\n".join([*lines, f"{self.main}\trefs/heads/main"]) + "\n"
        elif command[:2] == ["git", "rev-list"]:
            reply = "".join(f"{sha} {self.parents[sha]}\n" for sha in self.commits)
        elif command[:3] == ["git", "log", "-1"]:
            reply = self.subjects.get(command[-1], "") + "\n"
        elif command[:2] == ["git", "diff-tree"]:
            sha = command[-1]
            default = self.paths if sha == self.commits[0] else handoff_paths(cwd)
            reply = "\n".join(self.commit_paths.get(sha, default)) + "\n"
        elif command[:2] == ["gh", "api"]:
            reply = self.main + "\n"
        elif command == ["git", "rev-parse", "HEAD"]:
            reply = self.head + "\n"
        elif command == ["git", "branch", "--show-current"]:
            reply = self.current_branch + "\n"
        elif command == ["git", "status", "--porcelain", "--untracked-files=no"]:
            reply = self.status
        elif command == ["git", "status", "--porcelain"]:
            reply = ""   # B4's work finish had committed everything
        if reply is None:
            return super().__call__(argv, cwd)
        self.calls.append(command)
        return self._completed(command, reply, rc=rc)


def _stopped_b4(root):
    _workspace(root)
    path = _state_path(root)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "version": "1.2.3", "finished_steps": ["A1", "A2", "A3", "B1", "B2", "B3"], "b_paths": PATHS,
        "approvals": [{"step_id": "B4", "approved_by": "owner", "consent_source": "work order",
                       "gate": {"gate_id": "B4", "version": "1.2.3", "tag": "v1.2.3", "target_commit": "base-sha"}}],
    }))
    steps = path.parent / "release-run-1.2.3-steps"
    steps.mkdir()
    (steps / "B4.json").write_text(json.dumps({"returncode": 2, "json": {"result_status": "BLOCKED"}}))


def _run(root, runner, **extra):
    return run_release(ReleaseRunOptions(version="1.2.3", root=root, approved_by="owner",
                                         consent_source="work order", **extra), runner=runner)


def test_a_blocked_b4_completes_its_own_release_pr(tmp_path):
    _stopped_b4(tmp_path)
    runner = ResumeRunner()
    plan = _run(tmp_path, runner)
    gate = plan["gate"]
    assert plan["current_step"] == "B4" and plan["result_status"] == "AWAITING_APPROVAL"
    assert gate["mode"] == "resume-existing-release-pr" and gate["pr_number"] == 40
    assert gate["source_head"] == "rel-head" and gate["target_commit"] == "base-sha"
    assert not any("pr-complete" in c or "finish" in c for c in runner.calls)
    result = _run(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"])
    assert "B4" in result["finished_steps"]
    complete, = [c for c in runner.calls if "pr-complete" in c]
    assert complete[complete.index("pr-complete") + 1] == "40"
    assert complete[complete.index("--expected-head-sha") + 1] == "rel-head"
    assert complete[complete.index("--timeout-seconds") + 1] == "900"
    assert not any("work" in c and "finish" in c and "--execute" in c for c in runner.calls)
    _assert_agentic_argv_options_exist(complete)


@pytest.mark.parametrize("change,blocker", [
    ({"main": "moved-sha"}, "release-resume-base-moved"),
    ({"commits": ("c1", "c2", "rel-head")}, "release-resume-unexpected-commits"),
    ({"commit_paths": {"rel-head": ["src/evil.py"]}}, "release-resume-paths-differ"),
    ({"parents": {"c1": "base-sha", "rel-head": "side"}}, "release-resume-unexpected-commits"),
    ({"subjects": ("Prepare release 1.2.3", "Something else")}, "release-resume-unexpected-commits"),
    ({"paths": ["CHANGELOG.md", "src/evil.py"]}, "release-resume-paths-differ"),
])
def test_a_resume_that_does_not_match_the_approved_release_blocks(tmp_path, change, blocker):
    _stopped_b4(tmp_path)
    runner = ResumeRunner(**change)
    result = _run(tmp_path, runner)
    assert result["result_status"] == "BLOCKED" and blocker in result["blockers"]
    assert not any("pr-complete" in c for c in runner.calls)


def test_without_a_failed_b4_the_gate_stays_ordinary(tmp_path):
    _stopped_b4(tmp_path)
    (_state_path(tmp_path).parent / "release-run-1.2.3-steps/B4.json").unlink()
    runner = ResumeRunner()
    plan = _run(tmp_path, runner)
    assert "mode" not in (plan.get("gate") or {})
    assert not any("pr-existing-for-branch" in c for c in runner.calls)
