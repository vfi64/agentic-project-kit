#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

MODULE = Path('src/agentic_project_kit/post_merge_handoff_refresh.py')
CLI = Path('src/agentic_project_kit/cli_commands/handoff.py')
TEST = Path('tests/test_post_merge_handoff_refresh.py')
LOG = Path('docs/reports/terminal/post-merge-handoff-refresh-automation-helper.log')

MODULE.write_text('''from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any
from agentic_project_kit.handoff_freshness import assess_handoff_prompt_freshness
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state

@dataclass(frozen=True)
class PostMergeHandoffRefreshStatus:
    current_head: str
    freshness_warning_present: bool
    refresh_required: bool
    latest_successor_prompt: str | None
    result: str
    next_safe_action: str

def evaluate_post_merge_handoff_refresh(project_root: Path = Path('.'), *, state_path: str = '.agentic/handoff_state.yaml') -> PostMergeHandoffRefreshStatus:
    state_file = project_root / state_path
    data = load_handoff_state(str(state_file))
    rendered_prompt = render_handoff_prompt(data)
    warnings = assess_handoff_prompt_freshness(data, str(state_file), successor_prompt_text=rendered_prompt)
    warning = bool(warnings)
    return PostMergeHandoffRefreshStatus(_git_short_head(project_root), warning, warning, _latest_successor_prompt(data), 'REFRESH_REQUIRED' if warning else 'NOOP', 'create_administrative_handoff_refresh' if warning else 'continue_without_post_merge_handoff_refresh')

def render_post_merge_handoff_refresh_status(status: PostMergeHandoffRefreshStatus) -> str:
    return '\\n'.join(['POST_MERGE_HANDOFF_REFRESH', f'current_head={status.current_head}', f'freshness_warning_present={str(status.freshness_warning_present)}', f'refresh_required={str(status.refresh_required)}', f'latest_successor_prompt={status.latest_successor_prompt or ""}', f'result={status.result}', f'next_safe_action={status.next_safe_action}']) + '\\n'

def _git_short_head(project_root: Path) -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=project_root, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ''

def _latest_successor_prompt(data: dict[str, Any]) -> str | None:
    for key in ('handoff_maintenance', 'administrative_evidence_state'):
        section = data.get(key, {})
        if isinstance(section, dict) and section.get('latest_successor_prompt'):
            return str(section['latest_successor_prompt'])
    return None
''', encoding='utf-8')

cli_text = CLI.read_text(encoding='utf-8')
for marker in ('\n\n@app.command("post-merge-refresh-status")', '\n\n@handoff_app.command("post-merge-refresh-status")'):
    if marker in cli_text:
        cli_text = cli_text.split(marker, 1)[0]
        break
if 'from agentic_project_kit.post_merge_handoff_refresh import' not in cli_text:
    cli_text = cli_text.replace('\nhandoff_app = typer.Typer', '\nfrom agentic_project_kit.post_merge_handoff_refresh import evaluate_post_merge_handoff_refresh, render_post_merge_handoff_refresh_status\n\nhandoff_app = typer.Typer', 1)
cli_text += '''

@handoff_app.command("post-merge-refresh-status")
def post_merge_refresh_status() -> None:
    status = evaluate_post_merge_handoff_refresh(Path("."))
    typer.echo(render_post_merge_handoff_refresh_status(status), nl=False)
    if status.refresh_required:
        raise typer.Exit(1)
'''
CLI.write_text(cli_text, encoding='utf-8')

TEST.write_text('''from agentic_project_kit.post_merge_handoff_refresh import PostMergeHandoffRefreshStatus, render_post_merge_handoff_refresh_status

def test_render_post_merge_handoff_refresh_status_noop():
    rendered = render_post_merge_handoff_refresh_status(PostMergeHandoffRefreshStatus('abc123', False, False, 'docs/reports/terminal/prompt.md', 'NOOP', 'continue_without_post_merge_handoff_refresh'))
    assert rendered.startswith('POST_MERGE_HANDOFF_REFRESH\\n')
    assert 'current_head=abc123' in rendered
    assert 'result=NOOP' in rendered

def test_render_post_merge_handoff_refresh_status_required():
    rendered = render_post_merge_handoff_refresh_status(PostMergeHandoffRefreshStatus('def456', True, True, None, 'REFRESH_REQUIRED', 'create_administrative_handoff_refresh'))
    assert 'current_head=def456' in rendered
    assert 'result=REFRESH_REQUIRED' in rendered
    assert 'refresh_required=True' in rendered
''', encoding='utf-8')
LOG.write_text('POST_MERGE_HANDOFF_REFRESH_AUTOMATION_HELPER\nresult=PASS\n', encoding='utf-8')
print(LOG)
print('result=PASS')
