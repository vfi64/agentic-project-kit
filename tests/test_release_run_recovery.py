from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from tests.test_release_run import FakeRunner, _workspace, _state_path, _assert_agentic_argv_options_exist


class RecoveryRunner(FakeRunner):
    def __init__(self) -> None:
        super().__init__()
        self.branch = "main"
        self.head = "main-head"
        self.dirty = ""
        self.source_head = "doi-head"
        self.fail_push = False

    def __call__(self, argv, cwd):
        command = list(argv)
        self.calls.append(command)
        if command[:3] == ["git", "branch", "--show-current"]:
            return self._completed(command, self.branch + "\n")
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return self._completed(command, self.head + "\n")
        if command[:3] == ["git", "status", "--porcelain"]:
            return self._completed(command, self.dirty)
        if command[:2] == ["git", "show-ref"]:
            return self._completed(command, "", rc=1)
        if command[:2] == ["git", "ls-remote"]:
            return self._completed(command, "")
        if command[:3] == ["gh", "pr", "view"]:
            return self._completed(command, json.dumps({"state": "OPEN", "headRefOid": self.source_head, "headRefName": "codex/release-1.2.3-doi", "baseRefName": "main"}))
        if "pr-existing-for-branch" in command:
            payload = {"result_status": "PASS", "pr_number": 20}
        elif "post-release-doi-closeout" in command:
            if "--write" in command:
                self.dirty = " M CHANGELOG.md\n"
            payload = {"result_status": "PASS", "changed_paths": ["CHANGELOG.md"], "expected_paths": ["CHANGELOG.md"], "version_doi": "10.5281/zenodo.123", "concept_doi": "10.5281/zenodo.456"}
        elif "work" in command and "start" in command:
            self.branch = command[command.index("--branch") + 1]
            payload = {"result_status": "PASS"}
        elif "commit" in command:
            self.dirty = ""
            self.head = "repair-head"
            payload = {"result_status": "PASS"}
        elif "acknowledge" in command:
            payload = {"written": True, "path": ".agentic/rule_ack/current.json"}
        elif "push-current" in command and self.fail_push:
            payload = {"result_status": "BLOCKED"}
        elif "pr-create-complete" in command:
            self.branch = "main"
            payload = {"result_status": "PASS", "pr_number": 21}
        else:
            payload = self._payload_for(command)
        return self._completed(command, json.dumps(payload))


def _blocked_state(root: Path, *, legacy: bool = False) -> None:
    _workspace(root)
    path = _state_path(root)
    path.parent.mkdir(parents=True)
    state = {"version": "1.2.3", "finished_steps": ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3"]}
    if legacy:
        steps = path.parent / "release-run-1.2.3-steps"
        steps.mkdir()
        (steps / "D4.json").write_text(json.dumps({"returncode": 2, "json": {"result_status": "BLOCKED"}}))
    else:
        state["doi_recovery_required"] = True
    path.write_text(json.dumps(state))


def _run(root, runner, **kwargs):
    return run_release(ReleaseRunOptions(version="1.2.3", root=root, **kwargs), runner=runner)


def test_blocked_d4_legacy_state_offers_signed_d2r_and_finishes_using_kit_routes(tmp_path: Path) -> None:
    _blocked_state(tmp_path, legacy=True)
    runner = RecoveryRunner()
    preview = _run(tmp_path, runner)
    assert preview["result_status"] == "AWAITING_APPROVAL"
    assert preview["current_step"] == "D2R"
    assert preview["gate"]["pr_number"] == 20
    assert preview["gate"]["paths"] == ["CHANGELOG.md"]
    assert not any("--write" in call or "--execute" in call or "commit" in call for call in runner.calls)
    runner.calls.clear()
    result = _run(tmp_path, runner, execute=True, expected_signature=preview["gate"]["approval_signature"])
    assert result["result_status"] == "PASS"
    assert "D2R" in result["finished_steps"] and "D4" in result["finished_steps"]
    mutations = [call for call in runner.calls if call[0].endswith("agentic-kit") and any(value in call for value in ("start", "--write", "acknowledge", "commit", "push-current", "pr-create-complete", "pr-close-superseded"))]
    assert [next(value for value in ("start", "--write", "acknowledge", "commit", "push-current", "pr-create-complete", "pr-close-superseded") if value in call) for call in mutations] == ["start", "--write", "acknowledge", "commit", "push-current", "pr-create-complete", "pr-close-superseded"]
    assert "--post-merge-complete" in mutations[-2]
    assert "--replacement-pr" in mutations[-1] and "21" in mutations[-1]
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "close"] for call in runner.calls)
    for call in runner.calls:
        _assert_agentic_argv_options_exist(call)


def test_d2r_wrong_signature_has_no_mutations(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    runner = RecoveryRunner()
    result = _run(tmp_path, runner, execute=True, expected_signature="wrong")
    assert result["result_status"] == "BLOCKED"
    assert result["blockers"] == ["signature-mismatch"]
    assert not any("--write" in call or "--execute" in call or "start" in call or "commit" in call for call in runner.calls)


def test_d2r_stale_source_head_signature_is_refused(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    runner = RecoveryRunner()
    preview = _run(tmp_path, runner)
    runner.source_head = "another-owner-commit"
    result = _run(tmp_path, runner, execute=True, expected_signature=preview["gate"]["approval_signature"])
    assert result["blockers"] == ["signature-mismatch"]
    assert not any("--write" in call for call in runner.calls)


def test_d2r_resumes_after_failed_push_without_regeneration_or_commit(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    runner = RecoveryRunner()
    preview = _run(tmp_path, runner)
    runner.fail_push = True
    blocked = _run(tmp_path, runner, execute=True, expected_signature=preview["gate"]["approval_signature"])
    assert blocked["result_status"] == "BLOCKED"
    assert not any("pr-create-complete" in call for call in runner.calls)
    runner.fail_push = False
    fresh = _run(tmp_path, runner)
    runner.calls.clear()
    result = _run(tmp_path, runner, execute=True, expected_signature=fresh["gate"]["approval_signature"])
    assert result["result_status"] == "PASS"
    assert not any("--write" in call or "commit" in call for call in runner.calls)


def test_d2r_dirty_start_blocks_before_work_start(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    runner = RecoveryRunner()
    runner.dirty = " M owner-file.md\n"
    result = _run(tmp_path, runner)
    assert result["result_status"] == "BLOCKED"
    assert result["blockers"] == ["recovery-requires-clean-start"]
    assert not any("start" in call for call in runner.calls)


def test_d2r_preserves_unrelated_dirty_paths_after_write(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    class DirtyWriteRunner(RecoveryRunner):
        def __call__(self, argv, cwd):
            result = super().__call__(argv, cwd)
            if "--write" in argv:
                self.dirty += " M owner-file.md\n"
            return result
    runner = DirtyWriteRunner()
    preview = _run(tmp_path, runner)
    result = _run(tmp_path, runner, execute=True, expected_signature=preview["gate"]["approval_signature"])
    assert result["blockers"] == ["recovery-changed-paths-outside-approved-scope"]
    assert not any("commit" in call or "push-current" in call for call in runner.calls)


def test_d2r_recovers_local_doi_branch_without_an_open_pr(tmp_path: Path) -> None:
    _blocked_state(tmp_path)
    class BranchOnlyRunner(RecoveryRunner):
        def __call__(self, argv, cwd):
            if "pr-existing-for-branch" in argv:
                self.calls.append(list(argv))
                return self._completed(list(argv), json.dumps({"result_status": "MISS"}), rc=2)
            if list(argv[:3]) == ["git", "rev-parse", "--verify"]:
                self.calls.append(list(argv))
                return self._completed(list(argv), "doi-head\n")
            return super().__call__(argv, cwd)
    runner = BranchOnlyRunner()
    preview = _run(tmp_path, runner)
    assert preview["result_status"] == "AWAITING_APPROVAL"
    assert preview["gate"]["pr_number"] is None
    result = _run(tmp_path, runner, execute=True, expected_signature=preview["gate"]["approval_signature"])
    assert result["result_status"] == "PASS"
    assert not any("pr-close-superseded" in call for call in runner.calls)
