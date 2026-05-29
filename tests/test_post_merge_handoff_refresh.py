from agentic_project_kit.post_merge_handoff_refresh import PostMergeHandoffRefreshStatus, render_post_merge_handoff_refresh_status

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
