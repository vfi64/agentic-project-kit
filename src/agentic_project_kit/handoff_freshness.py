from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from agentic_project_kit.handoff_state import is_administrative_evidence_subject

FRESHNESS_GUARD_FILES = [
    "docs/STATUS.md",
    ".agentic/handoff_state.yaml",
    "docs/handoff/CURRENT_HANDOFF.md",
]


def assess_handoff_prompt_freshness(
    data: dict[str, Any],
    handoff_path: str | Path = ".agentic/handoff_state.yaml",
    *,
    current_head: str | None = None,
    current_subject: str | None = None,
) -> list[str]:
    """Return warnings when a successor handoff prompt may be stale.

    The guard is intentionally warning-based. A stale repository still needs to
    render a repairable prompt; it must not silently present that prompt as
    authoritative.
    """

    state_path = Path(handoff_path)
    project_root = _project_root_for_handoff_path(state_path)
    warnings: list[str] = []

    for relative_path in FRESHNESS_GUARD_FILES:
        if not (project_root / relative_path).exists():
            warnings.append(f"required handoff freshness file missing: {relative_path}")

    detected_head = _short_commit(current_head) if current_head else _git_short_head(project_root)
    detected_subject = current_subject if current_subject is not None else _git_head_subject(project_root)
    expected_commits = _expected_handoff_commits(data)
    admin_refresh_head = bool(
        detected_head
        and expected_commits
        and not _commit_matches(detected_head, expected_commits)
        and is_administrative_evidence_subject(detected_subject)
    )
    if (
        detected_head
        and expected_commits
        and not _commit_matches(detected_head, expected_commits)
        and not admin_refresh_head
    ):
        joined = ", ".join(expected_commits)
        warnings.append(
            "current git HEAD "
            f"{detected_head} is not represented by handoff safe/admin state ({joined})"
        )

    successor_prompt_path = _latest_successor_prompt_path(data, project_root)
    if successor_prompt_path is None:
        warnings.append("no successor handoff prompt was found under docs/reports/terminal")
        return warnings

    if not successor_prompt_path.exists():
        relative_prompt = _relative_to_project(successor_prompt_path, project_root)
        warnings.append(f"latest successor handoff prompt is missing: {relative_prompt}")
        return warnings

    marker_commits = expected_commits if admin_refresh_head else ([detected_head] if detected_head else expected_commits)
    prompt_text = successor_prompt_path.read_text(encoding="utf-8")
    if marker_commits and not any(commit and commit in prompt_text for commit in marker_commits):
        relative_prompt = _relative_to_project(successor_prompt_path, project_root)
        joined = ", ".join(marker_commits)
        warnings.append(
            "latest successor handoff prompt "
            f"{relative_prompt} does not mention current handoff commit marker(s): {joined}"
        )

    return warnings


def render_freshness_guard(warnings: list[str]) -> str:
    if not warnings:
        return ""
    lines = [
        "## Handoff Freshness Guard",
        "",
        "WARNING: this successor handoff prompt may be stale.",
        "Refresh `docs/STATUS.md`, `.agentic/handoff_state.yaml`, "
        "`docs/handoff/CURRENT_HANDOFF.md`, and the successor prompt before treating "
        "this prompt as authoritative.",
        "",
    ]
    lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines).rstrip() + "\n"


def _short_commit(value: Any) -> str:
    return str(value or "").strip()[:7]


def _project_root_for_handoff_path(path: Path) -> Path:
    if path.name == "handoff_state.yaml" and path.parent.name == ".agentic":
        return path.parent.parent
    return Path.cwd()


def _git_short_head(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _git_head_subject(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _expected_handoff_commits(data: dict[str, Any]) -> list[str]:
    commits: list[str] = []
    safe_state = data.get("safe_state", {})
    if isinstance(safe_state, dict):
        safe_commit = _short_commit(safe_state.get("commit"))
        if safe_commit:
            commits.append(safe_commit)
    admin_state = data.get("administrative_evidence_state", {})
    if isinstance(admin_state, dict):
        admin_commit = _short_commit(admin_state.get("current_head"))
        if admin_commit and admin_commit not in commits:
            commits.append(admin_commit)
    return commits


def _commit_matches(candidate: str, expected: list[str]) -> bool:
    candidate = _short_commit(candidate)
    return any(
        candidate.startswith(commit) or commit.startswith(candidate)
        for commit in expected
        if commit
    )


def _configured_successor_prompt_path(data: dict[str, Any], project_root: Path) -> Path | None:
    handoff_maintenance = data.get("handoff_maintenance", {})
    if isinstance(handoff_maintenance, dict):
        configured = handoff_maintenance.get("latest_successor_prompt")
        if configured:
            return project_root / str(configured)
    return None


def _latest_successor_prompt_path(data: dict[str, Any], project_root: Path) -> Path | None:
    configured = _configured_successor_prompt_path(data, project_root)
    if configured is not None:
        return configured
    terminal_dir = project_root / "docs" / "reports" / "terminal"
    if not terminal_dir.exists():
        return None
    candidates = sorted(terminal_dir.glob("*successor*handoff*.md"))
    if not candidates:
        return None
    return candidates[-1]


def _relative_to_project(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path