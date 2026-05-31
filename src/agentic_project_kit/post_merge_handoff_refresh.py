from __future__ import annotations
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
    current_head = _git_short_head(project_root)
    current_subject = _git_commit_subject(project_root)
    warnings = assess_handoff_prompt_freshness(
        data,
        str(state_file),
        current_head=current_head,
        current_subject=current_subject,
        successor_prompt_text=rendered_prompt,
    )
    warning = bool(warnings)
    return PostMergeHandoffRefreshStatus(current_head, warning, warning, _latest_successor_prompt(data), 'REFRESH_REQUIRED' if warning else 'NOOP', 'create_administrative_handoff_refresh' if warning else 'continue_without_post_merge_handoff_refresh')

def render_post_merge_handoff_refresh_status(status: PostMergeHandoffRefreshStatus) -> str:
    return '\n'.join(['POST_MERGE_HANDOFF_REFRESH', f'current_head={status.current_head}', f'freshness_warning_present={str(status.freshness_warning_present)}', f'refresh_required={str(status.refresh_required)}', f'latest_successor_prompt={status.latest_successor_prompt or ""}', f'result={status.result}', f'next_safe_action={status.next_safe_action}']) + '\n'

def _git_short_head(project_root: Path) -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=project_root, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ''

def _git_commit_subject(project_root: Path) -> str:
    try:
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%s'], cwd=project_root, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def _latest_successor_prompt(data: dict[str, Any]) -> str | None:
    for key in ('handoff_maintenance', 'administrative_evidence_state'):
        section = data.get(key, {})
        if isinstance(section, dict) and section.get('latest_successor_prompt'):
            return str(section['latest_successor_prompt'])
    return None
