"""K7 (owner plan 2026-11-13): `release run` resumes a B4 that stopped before its release PR.

Release 1.3.0: B4's `work finish` committed `Prepare release 1.3.0`, refreshed the handoff and then
failed to commit it on a locked index. Nothing was pushed. A new run blocked with
`changed-paths-drift`, and KIT-GF-080 applies only to an open release PR, so the release needed a
hand-built recovery order (0074). The B4 gate now plans a signed resume that publishes the existing
commits with `work finish` (K1) after committing the projection files B4 left uncommitted.
"""
import json

import pytest

from agentic_project_kit.release_run_b4_resume import UNPUBLISHED_MODE, covers_approved_paths
from test_release_b4_resume_and_required_checks import BRANCH, PATHS, ResumeRunner, _run, _stopped_b4, handoff_paths
from test_release_run import _assert_agentic_argv_options_exist

PREPARE = ("Prepare release 1.2.3",)


def _unpushed(**extra):
    defaults = {"pr": False, "remote_branch": "", "commits": ("c1",), "subjects": PREPARE}
    return ResumeRunner(**{**defaults, **extra})


def _finishes(runner):
    return [c for c in runner.calls if c[1:3] == ["work", "finish"] and "--execute" in c]


def test_a_b4_stopped_after_the_release_commit_resumes_with_work_finish(tmp_path):
    _stopped_b4(tmp_path)
    runner = _unpushed()
    plan = _run(tmp_path, runner)
    gate = plan["gate"]
    assert plan["result_status"] == "AWAITING_APPROVAL" and plan["current_step"] == "B4"
    assert gate["mode"] == UNPUBLISHED_MODE and gate["target_commit"] == "base-sha" and gate["source_head"] == "c1"
    assert gate["commits"] == [{"sha": "c1", "subject": "Prepare release 1.2.3"}]
    assert gate["remote_head"] == "" and gate["pending_paths"] == []
    # Nothing on the origin: no PR can exist, so no GitHub call is needed (offline resumable).
    assert not any(c[0] == "gh" or "pr-existing-for-branch" in c for c in runner.calls)
    assert not _finishes(runner)
    result = _run(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"])
    assert "B4" in result["finished_steps"], result
    finish, = _finishes(runner)
    assert finish[finish.index("--branch") + 1] == BRANCH
    assert finish[finish.index("--title") + 1] == "Release 1.2.3"
    assert "--path" not in finish   # K1: publish the existing commits
    assert finish[finish.index("--ci-timeout-seconds") + 1] == "900"
    _assert_agentic_argv_options_exist(finish)
    steps = tmp_path / ".agentic/tmp/release-run-1.2.3-steps"
    assert json.loads((steps / "B4.json").read_text())["returncode"] == 2   # evidence of the stop is kept
    assert (steps / "B4-resume-finish.json").is_file()


def test_uncommitted_handoff_files_are_committed_first_with_the_b4_subject(tmp_path):
    _stopped_b4(tmp_path)
    pending = handoff_paths(tmp_path)[3:6]
    runner = _unpushed(status="".join(f" M {path}\n" for path in pending))
    gate = _run(tmp_path, runner)["gate"]
    assert gate["mode"] == UNPUBLISHED_MODE and gate["pending_paths"] == sorted(pending)
    _run(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"])
    finish, = _finishes(runner)
    assert finish[finish.index("--message") + 1] == "Refresh handoff for Release 1.2.3"
    assert [finish[i + 1] for i, a in enumerate(finish) if a == "--path"] == sorted(pending)


def test_a_pushed_branch_without_a_pr_resumes_after_the_lookup(tmp_path):
    _stopped_b4(tmp_path)
    runner = _unpushed(commits=("c1", "c2"), subjects=(*PREPARE, "Refresh handoff for Release 1.2.3"),
                       remote_branch="c1")
    gate = _run(tmp_path, runner)["gate"]
    assert any("pr-existing-for-branch" in c for c in runner.calls)
    assert gate["mode"] == UNPUBLISHED_MODE and gate["remote_head"] == "c1" and gate["source_head"] == "c2"


def test_the_docs_pages_projection_commit_of_the_kit_release_is_accepted(tmp_path):
    _stopped_b4(tmp_path)
    runner = _unpushed(commits=("c1", "c2", "c3"),
                       subjects=(*PREPARE, "Refresh handoff for Release 1.2.3",
                                 "Refresh docs-pages projection for Release 1.2.3"),
                       commit_paths={"c3": ["docs/index.html", "docs/site/commands.html"]})
    gate = _run(tmp_path, runner)["gate"]
    assert gate["mode"] == UNPUBLISHED_MODE and len(gate["commits"]) == 3


@pytest.mark.parametrize("change,blocker", [
    ({"main": "moved-sha"}, "release-resume-base-moved"),
    ({"current_branch": "main"}, "release-resume-not-on-release-branch"),
    ({"remote_branch": "foreign", "pr": False}, "release-resume-remote-diverged"),
    ({"status": " M src/agentic_project_kit/cli.py\n"}, "release-resume-worktree-unexpected"),
    ({"paths": ["CHANGELOG.md"]}, "release-resume-paths-differ"),
    ({"subjects": ("Prepare release 9.9.9",)}, "release-resume-unexpected-commits"),
    ({"commits": ("c1", "c2"), "subjects": (*PREPARE, "Refresh handoff for Release 1.2.3"),
      "commit_paths": {"c2": ["pyproject.toml"]}}, "release-resume-paths-differ"),
    ({"commits": ("c1", "c2"), "subjects": (*PREPARE, "Hand-made fix")}, "release-resume-unexpected-commits"),
    ({"head": "elsewhere"}, "release-resume-unexpected-commits"),
])
def test_a_resume_that_does_not_match_the_approved_release_blocks_before_any_effect(tmp_path, change, blocker):
    _stopped_b4(tmp_path)
    runner = _unpushed(**change)
    result = _run(tmp_path, runner)
    assert result["result_status"] == "BLOCKED" and blocker in result["blockers"], result
    assert not _finishes(runner)


def test_a_stop_before_the_release_commit_keeps_the_ordinary_b4(tmp_path):
    _stopped_b4(tmp_path)
    runner = _unpushed(commits=(), subjects=(), head="base-sha")
    plan = _run(tmp_path, runner)
    assert plan["result_status"] == "AWAITING_APPROVAL" and "mode" not in plan["gate"]


def test_a_head_that_moved_after_the_signed_plan_blocks_the_resume(tmp_path):
    from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions
    from agentic_project_kit.release_run_b4_resume import complete

    _stopped_b4(tmp_path)
    runner = _unpushed()
    gate = _run(tmp_path, runner)["gate"]
    runner.head = "moved"
    run = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert complete(run, gate)["blockers"] == ["release-resume-head-drift"]
    assert not _finishes(runner)


def test_approved_directories_are_covered_by_the_files_committed_under_them():
    approved = [".agentic/state/handoff/reports/", "CHANGELOG.md"]
    assert covers_approved_paths([".agentic/state/handoff/reports/r.md", "CHANGELOG.md"], approved)
    assert not covers_approved_paths(["CHANGELOG.md"], approved)
    assert not covers_approved_paths([".agentic/state/handoff/reports/r.md", "CHANGELOG.md", "x.py"], approved)
    assert not covers_approved_paths([".agentic/state/handoff/reportsX", "CHANGELOG.md"], approved)
    assert not covers_approved_paths([], [])
    assert covers_approved_paths(sorted(PATHS), PATHS)
