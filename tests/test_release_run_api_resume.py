"""Resume the original DOI PR without regeneration or duplicate remote effects."""
import json
from pathlib import Path

import pytest

from agentic_project_kit.release_run_resume import original_doi_subject
from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions
from tests.test_release_run import _state_path, _assert_agentic_argv_options_exist
from tests.test_release_run_recovery import RecoveryRunner, _blocked_state, _run


def _api_failure(root: Path):
    _blocked_state(root, legacy=True)
    evidence = {"returncode": 2, "json": {"result_status": "BLOCKED", "steps": [{"stdout": json.dumps({
        "failed_step": "pr-wait-ci", "pr_number": 20, "expected_head_sha": "doi-head",
        "steps": [{"stdout": "PR readiness outcome: GH_ERROR\nGraphQL: API rate limit already exceeded"}],
    })}]}}
    path = _state_path(root).parent / 'release-run-1.2.3-steps/D4.json'
    path.write_text(json.dumps(evidence))
    return path


class ResumeRunner(RecoveryRunner):
    source_state = "OPEN"
    source_base = "main"
    fail_completion = False
    recheck_head = None

    def __call__(self, argv, cwd):
        if list(argv[:3]) == ["gh", "pr", "view"]:
            self.calls.append(list(argv))
            head = self.source_head
            if self.recheck_head and sum(call[:3] == ["gh", "pr", "view"] for call in self.calls) > 1:
                head = self.recheck_head
            return self._completed(list(argv), json.dumps({"state": self.source_state,
                "headRefOid": head, "headRefName": "codex/release-1.2.3-doi", "baseRefName": self.source_base,
                "mergeCommit": {"oid": "merge-head"}, "mergedAt": "2026-10-09T18:00:00Z" if self.source_state == "MERGED" else None}))
        if list(argv[:3]) == ["git", "merge-base", "--is-ancestor"]:
            self.calls.append(list(argv))
            return self._completed(list(argv), "")
        if "pr-complete" in argv:
            self.calls.append(list(argv))
            if self.fail_completion:
                self.source_state = "MERGED"  # Remote merge succeeded; handoff was interrupted.
                return self._completed(list(argv), json.dumps({"result_status": "BLOCKED"}), rc=2)
            return self._completed(list(argv), json.dumps({"result_status": "PASS"}))
        return super().__call__(argv, cwd)


def _mutations(runner):
    return [c for c in runner.calls if any(x in c for x in ('pr-complete', 'post-merge-complete', '--write', 'commit', 'start', 'push-current', 'pr-create-complete', 'pr-close-superseded'))]


def test_legacy_api_failure_resumes_original_signed_pr_and_preserves_failure_log(tmp_path):
    path = _api_failure(tmp_path)
    before = path.read_bytes()
    runner = ResumeRunner()
    preview = _run(tmp_path, runner)
    assert preview['result_status'] == 'AWAITING_APPROVAL'
    gate = preview['gate']
    assert gate['mode'] == 'resume-existing'
    assert gate['pr_number'] == 20 and gate['source_head'] == 'doi-head'
    assert gate['branch'] == 'codex/release-1.2.3-doi' and gate['base'] == 'main'
    assert gate['version'] == '1.2.3' and gate['tag'] == 'v1.2.3'
    assert not _mutations(runner)
    result = _run(tmp_path, runner, execute=True, expected_signature=gate['approval_signature'])
    assert result['result_status'] == 'PASS' and 'D4' in result['finished_steps']
    mutations = _mutations(runner)
    assert len(mutations) == 1 and 'pr-complete' in mutations[0] and '20' in mutations[0]
    assert '--expected-head-sha' in mutations[0] and 'doi-head' in mutations[0]
    assert '--post-merge-complete' in mutations[0]
    assert path.read_bytes() == before
    for call in runner.calls:
        _assert_agentic_argv_options_exist(call)


def test_wrong_resume_signature_never_mutates(tmp_path):
    _api_failure(tmp_path)
    runner = ResumeRunner()
    result = _run(tmp_path, runner, execute=True, expected_signature='wrong')
    assert result['blockers'] == ['signature-mismatch'] and not _mutations(runner)


@pytest.mark.parametrize('change', ['source_head', 'source_base', 'head'])
def test_resume_subject_drift_never_mutates(tmp_path, change):
    _api_failure(tmp_path)
    runner = ResumeRunner()
    preview = _run(tmp_path, runner)
    setattr(runner, change, 'owner-changed')
    runner.calls.clear()
    result = _run(tmp_path, runner, execute=True, expected_signature=preview['gate']['approval_signature'])
    assert result['result_status'] == 'BLOCKED' and not _mutations(runner)


def test_head_moving_after_approval_is_rechecked_before_completion(tmp_path):
    _api_failure(tmp_path)
    runner = ResumeRunner()
    preview = _run(tmp_path, runner)
    runner.calls.clear()
    runner.recheck_head = 'moved-between-read-and-action'
    result = _run(tmp_path, runner, execute=True, expected_signature=preview['gate']['approval_signature'])
    assert result['blockers'] == ['resume-source-drift-before-completion']
    assert not _mutations(runner)


def test_interrupted_completion_finishes_merged_original_handoff_without_second_merge(tmp_path):
    _api_failure(tmp_path)
    runner = ResumeRunner()
    preview = _run(tmp_path, runner)
    runner.fail_completion = True
    blocked = _run(tmp_path, runner, execute=True, expected_signature=preview['gate']['approval_signature'])
    assert blocked['result_status'] == 'BLOCKED'
    preview = _run(tmp_path, runner)
    assert preview['gate']['source_state'] == 'MERGED'
    runner.calls.clear()
    result = _run(tmp_path, runner, execute=True, expected_signature=preview['gate']['approval_signature'])
    assert result['result_status'] == 'PASS'
    mutations = _mutations(runner)
    assert len(mutations) == 1 and 'post-merge-complete' in mutations[0]
    assert '--after-pr' in mutations[0] and '20' in mutations[0]
    for call in runner.calls:
        _assert_agentic_argv_options_exist(call)


@pytest.mark.parametrize('status,blockers,expected', [
    ('FAIL', ['gh_pr_list_failed'], 'recovery-source-pr-lookup-unavailable'),
    ('BLOCKED', ['multiple_existing_prs_found'], 'recovery-source-pr-not-unique'),
    ('MISS', ['existing_pr_not_found'], 'resume-source-pr-not-found'),
])
def test_lookup_unavailable_ambiguous_and_missing_are_distinct(tmp_path, status, blockers, expected):
    _api_failure(tmp_path)
    class LookupRunner(ResumeRunner):
        def __call__(self, argv, cwd):
            if 'pr-existing-for-branch' in argv:
                self.calls.append(list(argv))
                return self._completed(list(argv), json.dumps({'result_status': status, 'blockers': blockers}), rc=1 if status == 'FAIL' else 2)
            return super().__call__(argv, cwd)
    runner = LookupRunner()
    result = _run(tmp_path, runner)
    assert result['blockers'] == [expected] and not _mutations(runner)


def test_real_ci_failure_keeps_replacement_recovery(tmp_path):
    path = _api_failure(tmp_path)
    path.write_text(path.read_text().replace('GH_ERROR', 'BLOCKED: check failed: test'))
    runner = RecoveryRunner()
    preview = _run(tmp_path, runner)
    assert preview['gate'].get('mode') != 'resume-existing'
    assert preview['gate']['branch'].endswith('-recovery')
    assert original_doi_subject(ReleaseRun(ReleaseRunOptions(version='1.2.3', root=tmp_path))) is None


@pytest.mark.parametrize('payload', ['', '[]', '{"result_status": "PLANNED"}', '{"result_status": "BLOCKED"}'])
def test_zero_exit_without_explicit_completion_pass_cannot_finish_d4(tmp_path, payload):
    _api_failure(tmp_path)
    class FalsePassRunner(ResumeRunner):
        def __call__(self, argv, cwd):
            if 'pr-complete' in argv:
                self.calls.append(list(argv))
                return self._completed(list(argv), payload)
            return super().__call__(argv, cwd)
    runner = FalsePassRunner()
    preview = _run(tmp_path, runner)
    result = _run(tmp_path, runner, execute=True, expected_signature=preview['gate']['approval_signature'])
    assert result['result_status'] == 'BLOCKED' and 'D4' not in result['finished_steps']


def test_merged_original_requires_ancestry_before_handoff(tmp_path):
    _api_failure(tmp_path)
    class WrongAncestryRunner(ResumeRunner):
        source_state = 'MERGED'
        def __call__(self, argv, cwd):
            if list(argv[:3]) == ['git', 'merge-base', '--is-ancestor']:
                self.calls.append(list(argv))
                return self._completed(list(argv), '', rc=1)
            return super().__call__(argv, cwd)
    runner = WrongAncestryRunner()
    result = _run(tmp_path, runner)
    assert result['blockers'] == ['resume-merge-not-on-current-main'] and not _mutations(runner)


def test_malformed_lookup_response_blocks_without_traceback(tmp_path):
    _api_failure(tmp_path)
    class MalformedRunner(ResumeRunner):
        def __call__(self, argv, cwd):
            if 'pr-existing-for-branch' in argv:
                self.calls.append(list(argv))
                return self._completed(list(argv), '["unexpected"]')
            return super().__call__(argv, cwd)
    runner = MalformedRunner()
    result = _run(tmp_path, runner)
    assert result['blockers'] == ['recovery-source-pr-lookup-invalid-response'] and not _mutations(runner)
