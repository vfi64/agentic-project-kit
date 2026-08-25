from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any
from agentic_project_kit.handoff_freshness import assess_handoff_prompt_freshness
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_external_manifest_workspace

DEFAULT_HANDOFF_STATE_PATH = ".agentic/handoff_state.yaml"

@dataclass(frozen=True)
class PostMergeHandoffRefreshStatus:
    current_head: str
    freshness_warning_present: bool
    refresh_required: bool
    latest_successor_prompt: str | None
    result: str
    next_safe_action: str
    state_path: str = ""
    warning: str = ""

def evaluate_post_merge_handoff_refresh(project_root: Path = Path('.'), *, state_path: str = DEFAULT_HANDOFF_STATE_PATH) -> PostMergeHandoffRefreshStatus:
    state_file = _resolve_state_file(project_root, state_path)
    state_path_text = _path_text(project_root, state_file)
    current_head = _git_short_head(project_root)
    if not state_file.exists():
        if is_external_manifest_workspace(project_root):
            return PostMergeHandoffRefreshStatus(
                current_head,
                False,
                False,
                None,
                'NOOP',
                'continue_without_post_merge_handoff_refresh',
                state_path_text,
                'external_handoff_state_not_required',
            )
        return PostMergeHandoffRefreshStatus(
            current_head,
            True,
            True,
            None,
            'STATE_UNAVAILABLE',
            'restore_or_generate_handoff_state',
            state_path_text,
            'handoff_state_missing',
        )
    data = load_handoff_state(str(state_file))
    rendered_prompt = render_handoff_prompt(data)
    current_subject = _git_commit_subject(project_root)
    warnings = assess_handoff_prompt_freshness(
        data,
        str(state_file),
        current_head=current_head,
        current_subject=current_subject,
        successor_prompt_text=rendered_prompt,
    )
    warning = bool(warnings)
    return PostMergeHandoffRefreshStatus(current_head, warning, warning, _latest_successor_prompt(data), 'REFRESH_REQUIRED' if warning else 'NOOP', 'create_administrative_handoff_refresh' if warning else 'continue_without_post_merge_handoff_refresh', state_path_text, '')

def render_post_merge_handoff_refresh_status(status: PostMergeHandoffRefreshStatus) -> str:
    lines = ['POST_MERGE_HANDOFF_REFRESH', f'current_head={status.current_head}', f'freshness_warning_present={str(status.freshness_warning_present)}', f'refresh_required={str(status.refresh_required)}', f'latest_successor_prompt={status.latest_successor_prompt or ""}', f'result={status.result}', f'next_safe_action={status.next_safe_action}']
    if status.state_path:
        lines.append(f'state_path={status.state_path}')
    if status.warning:
        lines.append(f'warning={status.warning}')
    return '\n'.join(lines) + '\n'

def _resolve_state_file(project_root: Path, state_path: str) -> Path:
    root = Path(project_root)
    if state_path != DEFAULT_HANDOFF_STATE_PATH:
        return root / state_path
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    return workspace.handoff_state_path()

def _path_text(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()

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
