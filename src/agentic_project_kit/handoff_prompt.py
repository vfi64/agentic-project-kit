from __future__ import annotations

from typing import Any

from agentic_project_kit.handoff_state import active_rules

def _bullet_lines(items: list[Any]) -> list[str]:
    return [f"- {item}" for item in items]

def render_handoff_prompt(data: dict[str, Any]) -> str:
    repo = data.get("repo", {})
    safe_state = data.get("safe_state", {})
    release = data.get("release", {})
    if isinstance(data.get("open_items"), dict):
        open_prs = data.get("open_items", {}).get("prs", [])
    else:
        open_prs = []
    lines: list[str] = []
    lines.extend([
        "# Übergabeprompt",
        "",
        "## Repo",
        "",
        f"Local path: `{repo.get('local_path', '')}`",
        f"Remote: `{repo.get('remote', '')}`",
        f"Default branch: `{repo.get('default_branch', 'main')}`",
    ])
    lines.extend([
        "",
        "## Sicherer Stand",
        "",
        f"Branch: `{safe_state.get('branch', '')}`",
        f"Commit: `{safe_state.get('commit', '')}`",
        f"Subject: {safe_state.get('commit_subject', '')}",
    ])
    lines.extend([
        "",
        "## Release",
        "",
        f"Current version: `{release.get('current_version', '')}`",
        f"Tag: `{release.get('tag', '')}`",
        f"Zenodo version DOI: `{release.get('zenodo_version_doi', '')}`",
        f"Post-release check: `{release.get('post_release_check', '')}`",
    ])
    lines.extend(["", "## Offene Punkte", ""])
    if open_prs:
        for pr in open_prs:
            lines.append(f"- PR #{pr.get('number')}: {pr.get('title', '')}")
    else:
        lines.append("- Keine offenen PRs im handoff_state.")
    lines.extend(["", "## Abgeschlossen seit letzter Übergabe", ""])
    lines.extend(_bullet_lines(data.get("completed_since_previous_handoff", [])))
    lines.extend(["", "## Aktive Regeln", ""])
    for rule in active_rules(data):
        lines.append(f"- `{rule.get('id')}`: {rule.get('text')}")
    lines.extend(["", "## Nächste erlaubte Aufgaben", ""])
    for task in data.get("next_allowed_tasks", []):
        if isinstance(task, dict):
            lines.append(f"- {task.get('priority', '?')}. `{task.get('id', '')}` — {task.get('title', '')}")
    lines.extend(["", "## Gesperrte Aufgaben", ""])
    lines.extend(_bullet_lines(data.get("blocked_until_closeout", [])))
    lines.extend(["", "## Erste Arbeitsanweisung", "", data.get("first_instruction", "")])
    return "\n".join(lines).rstrip() + "\n"
