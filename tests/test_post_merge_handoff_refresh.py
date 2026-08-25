from agentic_project_kit.post_merge_handoff_refresh import PostMergeHandoffRefreshStatus, evaluate_post_merge_handoff_refresh, render_post_merge_handoff_refresh_status

def test_render_post_merge_handoff_refresh_status_noop():
    rendered = render_post_merge_handoff_refresh_status(PostMergeHandoffRefreshStatus('abc123', False, False, 'docs/reports/terminal/prompt.md', 'NOOP', 'continue_without_post_merge_handoff_refresh'))
    assert rendered.startswith('POST_MERGE_HANDOFF_REFRESH\n')
    assert 'current_head=abc123' in rendered
    assert 'result=NOOP' in rendered

def test_render_post_merge_handoff_refresh_status_required():
    rendered = render_post_merge_handoff_refresh_status(PostMergeHandoffRefreshStatus('def456', True, True, None, 'REFRESH_REQUIRED', 'create_administrative_handoff_refresh'))
    assert 'current_head=def456' in rendered
    assert 'result=REFRESH_REQUIRED' in rendered
    assert 'refresh_required=True' in rendered

def test_evaluate_post_merge_handoff_refresh_passes_current_head_and_subject(tmp_path, monkeypatch):
    state_file = tmp_path / ".agentic" / "handoff_state.yaml"
    state_file.parent.mkdir(parents=True)
    state_file.write_text("schema_version: 1\n", encoding="utf-8")

    calls = {}

    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh.load_handoff_state",
        lambda path: {"handoff_maintenance": {"latest_successor_prompt": "docs/reports/terminal/prompt.md"}},
    )
    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh.render_handoff_prompt",
        lambda data: "fresh successor prompt",
    )

    def fake_assess(data, state_path, **kwargs):
        calls.update(kwargs)
        return []

    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh.assess_handoff_prompt_freshness",
        fake_assess,
    )
    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh._git_short_head",
        lambda project_root: "abc1234",
    )
    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh._git_commit_subject",
        lambda project_root: "Refresh handoff after PR978 (#979)",
    )

    status = evaluate_post_merge_handoff_refresh(tmp_path)

    assert status.result == "NOOP"
    assert status.refresh_required is False
    assert calls["current_head"] == "abc1234"
    assert calls["current_subject"] == "Refresh handoff after PR978 (#979)"
    assert calls["successor_prompt_text"] == "fresh successor prompt"


def test_evaluate_post_merge_handoff_refresh_skips_missing_external_state(tmp_path, monkeypatch):
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "config.yaml").write_text(
        "kit_schema_version: 2\n"
        "project:\n"
        "  name: external-target\n"
        "  type: python\n"
        "profile: python-default\n"
        "modules:\n"
        "  doc_registry: true\n"
        "  release_governance: true\n"
        "  rule_registry: true\n"
        "  transfer: true\n"
        "transfer:\n"
        "  visibility: repo\n"
        "hygiene:\n"
        "  doc_lifecycle: warn\n"
        "  review_budgets:\n"
        "    governance: 180\n"
        "    reference: 365\n"
        "    workflow: 270\n"
        "paths:\n"
        "  docs_root: docs\n"
        "gates:\n"
        "  extra: []\n"
        "  skip: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh._git_short_head",
        lambda project_root: "abc1234",
    )

    status = evaluate_post_merge_handoff_refresh(tmp_path)

    assert status.result == "NOOP"
    assert status.refresh_required is False
    assert status.state_path == ".agentic/state/handoff/handoff_state.yaml"
    assert status.warning == "external_handoff_state_not_required"


def test_evaluate_post_merge_handoff_refresh_missing_self_hosting_state_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agentic_project_kit.post_merge_handoff_refresh._git_short_head",
        lambda project_root: "def5678",
    )

    status = evaluate_post_merge_handoff_refresh(tmp_path)

    assert status.result == "STATE_UNAVAILABLE"
    assert status.refresh_required is True
    assert status.next_safe_action == "restore_or_generate_handoff_state"
    assert status.warning == "handoff_state_missing"
