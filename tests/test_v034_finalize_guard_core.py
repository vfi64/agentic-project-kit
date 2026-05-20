from agentic_project_kit.finalize_guard import FinalizeGuardStatus, classify_finalize_guard_state, main, render_finalize_guard_decision


def classify(**overrides):
    state = dict(
        marker_requested=False,
        marker_on_main=False,
        local_branch_exists=True,
        remote_branch_exists=False,
        commits_ahead_of_main=1,
        merge_conflict=False,
    )
    state.update(overrides)
    return classify_finalize_guard_state(**state)


def test_marker_already_on_main_with_zero_ahead_passes_idempotently():
    decision = classify(marker_requested=True, marker_on_main=True, commits_ahead_of_main=0, merge_conflict=None)
    assert decision.status == FinalizeGuardStatus.PASS_ALREADY_ON_MAIN
    assert decision.result == "PASS"
    assert not decision.needs_pr
    assert not decision.needs_human_review


def test_missing_branch_is_noop_pass():
    decision = classify(local_branch_exists=False, remote_branch_exists=False, commits_ahead_of_main=None, merge_conflict=None)
    assert decision.status == FinalizeGuardStatus.PASS_NOOP_BRANCH
    assert decision.result == "PASS"


def test_branch_with_zero_ahead_commits_is_noop_pass():
    decision = classify(commits_ahead_of_main=0, merge_conflict=None)
    assert decision.status == FinalizeGuardStatus.PASS_NOOP_BRANCH
    assert decision.result == "PASS"


def test_branch_ahead_and_mergeable_needs_pr():
    decision = classify(commits_ahead_of_main=2, merge_conflict=False)
    assert decision.status == FinalizeGuardStatus.PASS_NEEDS_PR
    assert decision.result == "PASS"
    assert decision.needs_pr


def test_branch_ahead_and_conflicting_fails_relevant():
    decision = classify(commits_ahead_of_main=2, merge_conflict=True)
    assert decision.status == FinalizeGuardStatus.FAIL_CONFLICT_RELEVANT
    assert decision.result == "FAIL"
    assert decision.needs_human_review


def test_missing_ahead_information_requires_human_review():
    decision = classify(commits_ahead_of_main=None, merge_conflict=False)
    assert decision.status == FinalizeGuardStatus.FAIL_NEEDS_HUMAN_REVIEW
    assert decision.result == "FAIL"
    assert decision.needs_human_review


def test_missing_merge_conflict_information_requires_human_review():
    decision = classify(commits_ahead_of_main=2, merge_conflict=None)
    assert decision.status == FinalizeGuardStatus.FAIL_NEEDS_HUMAN_REVIEW
    assert decision.result == "FAIL"
    assert decision.needs_human_review


def test_conflicting_branch_with_marker_on_main_is_superseded():
    decision = classify(marker_requested=True, marker_on_main=True, commits_ahead_of_main=2, merge_conflict=True)
    assert decision.status == FinalizeGuardStatus.PASS_SUPERSEDED
    assert decision.result == "PASS"
    assert not decision.needs_human_review


def test_marker_on_main_with_no_branch_is_already_on_main():
    decision = classify(marker_requested=True, marker_on_main=True, local_branch_exists=False, remote_branch_exists=False, commits_ahead_of_main=None, merge_conflict=None)
    assert decision.status == FinalizeGuardStatus.PASS_NOOP_BRANCH
    assert decision.result == "PASS"


def test_render_finalize_guard_decision_contract():
    decision = classify(commits_ahead_of_main=2, merge_conflict=False)
    rendered = render_finalize_guard_decision(decision)
    assert "STATUS: PASS_NEEDS_PR" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_finalize_guard_cli_returns_zero_for_pass(capsys):
    code = main([
        "--marker-requested", "true",
        "--marker-on-main", "true",
        "--local-branch-exists", "true",
        "--remote-branch-exists", "false",
        "--commits-ahead-of-main", "2",
        "--merge-conflict", "true",
    ])
    assert code == 0
    assert "STATUS: PASS_SUPERSEDED" in capsys.readouterr().out


def test_finalize_guard_cli_returns_one_for_fail(capsys):
    code = main([
        "--marker-requested", "false",
        "--marker-on-main", "false",
        "--local-branch-exists", "true",
        "--remote-branch-exists", "false",
        "--commits-ahead-of-main", "2",
        "--merge-conflict", "true",
    ])
    assert code == 1
    assert "STATUS: FAIL_CONFLICT_RELEVANT" in capsys.readouterr().out

