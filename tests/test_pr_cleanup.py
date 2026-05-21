from agentic_project_kit.pr_cleanup import PullRequestInfo, classify_pr, parse_prs, render_classification


def pr(head, mergeable="MERGEABLE", draft=False):
    return PullRequestInfo(
        number=1,
        head=head,
        base="main",
        mergeable=mergeable,
        is_draft=draft,
        author="bot",
        updated_at="2026-01-01T00:00:00Z",
        title="Example PR",
    )


def test_classifies_dependabot_pr():
    result = classify_pr(pr("dependabot/pip/example"))
    assert result.pr_class == "DEPENDABOT_PR"
    assert result.action == "review_dependency_update"


def test_classifies_stale_docs_finalization_candidate():
    result = classify_pr(pr("docs/finalize-v0.3.36-state"))
    assert result.pr_class == "STALE_DOCS_FINALIZATION_CANDIDATE"
    assert result.action == "run_finalize_guard_before_closing_or_recreating"


def test_classifies_release_prep_pr():
    result = classify_pr(pr("release/prepare-v0.3.37"))
    assert result.pr_class == "RELEASE_PREP_PR"
    assert result.action == "verify_release_state_before_merge_or_close"


def test_classifies_conflicting_relevant_pr():
    result = classify_pr(pr("feature/x", mergeable="CONFLICTING"))
    assert result.pr_class == "CONFLICTING_RELEVANT_PR"
    assert result.action == "human_review_required"


def test_classifies_conflicting_docs_finalization():
    result = classify_pr(pr("docs/record-v0.3.36-doi", mergeable="CONFLICTING"))
    assert result.pr_class == "SUPERSEDED_OR_CONFLICTING_DOCS_FINALIZATION"
    assert result.action == "run_finalize_guard_then_human_decide_safe_close"


def test_draft_overrides_action():
    result = classify_pr(pr("feature/x", draft=True))
    assert result.pr_class == "ACTIVE_FEATURE_PR"
    assert result.action == "draft_review_required"


def test_parse_prs_accepts_gh_json_payload():
    payload = '[{"number": 7, "headRefName": "feature/x", "baseRefName": "main", "mergeable": "UNKNOWN", "isDraft": false, "author": {"login": "alice"}, "updatedAt": "2026-01-01T00:00:00Z", "title": "Hello"}]'
    parsed = parse_prs(payload)
    assert parsed[0].number == 7
    assert parsed[0].head == "feature/x"
    assert parsed[0].author == "alice"


def test_render_reports_zero_open_prs():
    text = render_classification([], branch="main", status="")
    assert "open_pr_count=0" in text
    assert "No open PRs found." in text
    assert "### RESULT: PASS ###" in text
