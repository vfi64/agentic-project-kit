"""KIT-GF-078: the release run's work finish waited 300 s for CI, the Kit's full CI took 5 to 5.5 min.

Release 1.1.3: D4 stopped after 319 s with `pr-wait-ci` TIMEOUT while the DOI PR's CI was still
pending, and E1 left the green archive PR #2576 open the same way. The DOI PR was regenerated
through D2R (a duplicate PR and CI run) and the archive PR needed a hand-written `pr-complete`.
Now work finish waits 900 s by default, the release run passes the wait explicitly, a D4 TIMEOUT
resumes the unchanged DOI PR, and E1 completes its own open archive PR when the evidence is
byte-identical.
"""
import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.human_workflows import WORK_FINISH_CI_TIMEOUT_SECONDS
from agentic_project_kit.release_run import RELEASE_CI_TIMEOUT_SECONDS, ReleaseRunOptions, run_release
from agentic_project_kit.release_run_evidence import encoded, evidence_path, snapshot_without_archive_approval
from agentic_project_kit.release_run_resume import original_doi_subject
from test_release_run import FakeRunner, _assert_agentic_argv_options_exist, _state_path
from test_release_run_api_resume import ResumeRunner, _mutations
from test_release_run_evidence import prepared
from test_release_run_recovery import _blocked_state, _run


def _completed(argv, stdout='{"result_status": "PASS"}\n', rc=0):
    return subprocess.CompletedProcess(argv, rc, stdout, "")


# --- the wait -----------------------------------------------------------------------------------

def test_work_finish_waits_900_seconds_by_default_and_passes_an_explicit_wait(monkeypatch):
    assert WORK_FINISH_CI_TIMEOUT_SECONDS == RELEASE_CI_TIMEOUT_SECONDS == 900
    calls = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        if "pr-create-complete" in argv:
            return _completed(list(argv), '{"result_status":"PASS","pr_number":7,'
                                          '"post_merge_complete_verified_by_inner_pr_complete":true}\n')
        return _completed(list(argv))

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)
    base = ["work", "finish", "--branch", "codex/x", "--title", "X", "--message", "X", "--path", "a.py", "--execute", "--json"]
    for extra, wanted in (([], "900"), (["--ci-timeout-seconds", "1200"], "1200")):
        calls.clear()
        assert CliRunner().invoke(app, [*base, *extra]).exit_code == 0
        create = next(c for c in calls if "pr-create-complete" in c)
        assert create[create.index("--timeout-seconds") + 1] == wanted
    assert CliRunner().invoke(app, [*base, "--ci-timeout-seconds", "10"]).exit_code != 0


def test_every_release_run_work_finish_passes_the_wait(tmp_path):
    run = prepared(tmp_path)
    options = ReleaseRunOptions(version="1.2.3", root=tmp_path, approved_by="owner", consent_source="work order")
    plan = run_release(options, runner=run.runner)
    run_release(ReleaseRunOptions(**{**options.__dict__, "execute": True,
                                     "expected_signature": plan["gate"]["approval_signature"]}), runner=run.runner)
    run._work_finish("B4", branch=run.branch, paths=["CHANGELOG.md"], execute=False, expected_status="PLANNED")
    run._work_finish("D4", branch=run.doi_branch, paths=["CITATION.cff"], execute=False, expected_status="PLANNED")
    finishes = [c for c in run.runner.calls if "work" in c and "finish" in c]
    assert len(finishes) == 3   # E1, B4, D4
    assert finishes and all(c[c.index("--ci-timeout-seconds") + 1] == "900" for c in finishes)
    for call in finishes:
        _assert_agentic_argv_options_exist(call)


# --- D4: a TIMEOUT resumes the unchanged DOI PR -----------------------------------------------

def _d4_failure(root, outcome):
    _blocked_state(root, legacy=True)
    evidence = {"returncode": 2, "json": {"result_status": "BLOCKED", "steps": [{"stdout": json.dumps({
        "failed_step": "pr-wait-ci", "pr_number": 20, "expected_head_sha": "doi-head",
        "steps": [{"stdout": f"PR readiness outcome: {outcome}\n- pending: test"}],
    })}]}}
    path = _state_path(root).parent / "release-run-1.2.3-steps/D4.json"
    path.write_text(json.dumps(evidence))


def test_a_d4_ci_timeout_resumes_the_existing_doi_pr_with_the_long_wait(tmp_path):
    _d4_failure(tmp_path, "TIMEOUT")
    runner = ResumeRunner()
    gate = _run(tmp_path, runner)["gate"]
    assert gate["mode"] == "resume-existing" and gate["pr_number"] == 20 and gate["source_head"] == "doi-head"
    result = _run(tmp_path, runner, execute=True, expected_signature=gate["approval_signature"])
    assert result["result_status"] == "PASS"
    mutation, = _mutations(runner)
    assert "pr-complete" in mutation and mutation[mutation.index("--timeout-seconds") + 1] == "900"


def test_red_ci_still_regenerates_instead_of_resuming(tmp_path):
    _d4_failure(tmp_path, "BLOCKED")
    from agentic_project_kit.release_run import ReleaseRun

    run = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=FakeRunner())
    assert original_doi_subject(run) is None


# --- E1: completing its own open archive PR -----------------------------------------------------

class ArchiveRunner(FakeRunner):
    def __init__(self, evidence: str, lookup_rc: int = 0):
        super().__init__()
        self.evidence, self.lookup_rc = evidence, lookup_rc

    def __call__(self, argv, cwd):
        command = [str(a) for a in argv]
        if "pr-existing-for-branch" in command:
            self.calls.append(command)
            if self.lookup_rc:
                return self._completed(command, json.dumps({"result_status": "MISS"}), rc=2)
            return self._completed(command, json.dumps({"result_status": "PASS", "pr_number": 31}))
        if command[:3] == ["gh", "pr", "view"]:
            self.calls.append(command)
            return self._completed(command, json.dumps({"headRefOid": "archive-head", "baseRefName": "main",
                                                        "headRefName": "codex/release-1.2.3-evidence", "state": "OPEN"}))
        if command[:2] == ["git", "show"]:
            self.calls.append(command)
            return self._completed(command, self.evidence)
        return super().__call__(argv, cwd)


def _stopped_archive(tmp_path, evidence=None, lookup_rc=0):
    run = prepared(tmp_path)
    run.state["evidence_archive"] = {"started": True, "result_status": "BLOCKED"}
    run._save_state()
    content = encoded(snapshot_without_archive_approval(run)).decode("utf-8")
    return ArchiveRunner(content if evidence is None else evidence, lookup_rc)


def _options(tmp_path, **extra):
    return ReleaseRunOptions(version="1.2.3", root=tmp_path, approved_by="owner", consent_source="work order", **extra)


def test_e1_completes_its_open_archive_pr_with_identical_evidence(tmp_path):
    runner = _stopped_archive(tmp_path)
    plan = run_release(_options(tmp_path), runner=runner)
    gate = plan["gate"]
    assert plan["current_step"] == "E1" and gate["mode"] == "resume-existing-archive"
    assert gate["pr_number"] == 31 and gate["source_head"] == "archive-head"
    assert not any("pr-complete" in c or "finish" in c for c in runner.calls)
    final = run_release(_options(tmp_path, execute=True, expected_signature=gate["approval_signature"]), runner=runner)
    assert final["result_status"] == "PASS"
    complete, = [c for c in runner.calls if "pr-complete" in c]
    assert complete[complete.index("pr-complete") + 1] == "31"
    assert complete[complete.index("--expected-head-sha") + 1] == "archive-head"
    assert complete[complete.index("--timeout-seconds") + 1] == "900"
    assert not any("work" in c and "finish" in c for c in runner.calls)
    assert not (tmp_path / evidence_path("1.2.3")).exists()   # nothing rewritten locally
    _assert_agentic_argv_options_exist(complete)


def test_e1_never_completes_an_archive_pr_with_other_evidence(tmp_path):
    runner = _stopped_archive(tmp_path, evidence="{}\n")
    result = run_release(_options(tmp_path), runner=runner)
    assert result["result_status"] == "BLOCKED" and "archive-resume-pr-evidence-differs" in result["blockers"]
    assert not any("pr-complete" in c for c in runner.calls)


def test_without_an_open_archive_pr_e1_takes_the_ordinary_route(tmp_path):
    runner = _stopped_archive(tmp_path, lookup_rc=2)
    plan = run_release(_options(tmp_path), runner=runner)
    assert plan["result_status"] == "AWAITING_APPROVAL" and "mode" not in plan["gate"]
