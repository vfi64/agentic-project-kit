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
OPERATIONAL_FRESHNESS_FILES = [
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
]
SUCCESSOR_HANDOFF_GLOBS = [
    "*successor*handoff*.md",
    "*successor*handoff*.yaml",
    "*successor*handoff*.yml",
]


def assess_handoff_prompt_freshness(
    data: dict[str, Any],
    handoff_path: str | Path = ".agentic/handoff_state.yaml",
    *,
    current_head: str | None = None,
    current_subject: str | None = None,
    successor_prompt_text: str | None = None,
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
    detected_message = (
        current_subject
        if current_subject is not None
        else _git_head_message(project_root)
    )
    expected_commits = _expected_handoff_commits(data)
    admin_refresh_head = bool(
        detected_head
        and expected_commits
        and not _commit_matches(detected_head, expected_commits)
        and (
            is_administrative_evidence_subject(detected_subject)
            or _is_administrative_merge_commit(
                project_root,
                detected_head,
                detected_message,
                expected_commits,
            )
        )
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
    if successor_prompt_text is None:
        prompt_text = successor_prompt_path.read_text(encoding="utf-8")
    else:
        prompt_text = successor_prompt_text
    if marker_commits and not any(commit and commit in prompt_text for commit in marker_commits):
        relative_prompt = _relative_to_project(successor_prompt_path, project_root)
        joined = ", ".join(marker_commits)
        warnings.append(
            "latest successor handoff prompt "
            f"{relative_prompt} does not mention current handoff commit marker(s): {joined}"
        )

    warnings.extend(
        _assess_operational_document_freshness(
            project_root,
            expected_commits,
        )
    )

    return warnings



def _assess_operational_document_freshness(
    project_root: Path,
    marker_commits: list[str],
) -> list[str]:
    """Return warnings when live operational docs do not mention current markers.

    This intentionally reuses the existing handoff-freshness mechanism. It does
    not introduce a new rule layer: STATUS, CURRENT_HANDOFF, chat bootstrap
    prompts, and the active roadmap are human-facing projections of the
    machine-readable handoff state and must mention at least one current
    safe/admin commit marker when they exist. Stable authority sources such as
    PROJECT_DIRECTION.yaml are intentionally excluded; they are required
    context, not per-PR refresh projections.
    """

    markers = [marker for marker in marker_commits if marker]
    if not markers:
        return []

    warnings: list[str] = []
    for relative_path in OPERATIONAL_FRESHNESS_FILES:
        path = project_root / relative_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if any(marker in content for marker in markers):
            continue
        joined = ", ".join(markers)
        warnings.append(
            f"operational handoff document {relative_path} does not mention "
            f"current handoff commit marker(s): {joined}"
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


def _git_head_message(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _git_commit_subject(project_root: Path, commit: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s", commit],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _git_commit_message(project_root: Path, commit: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B", commit],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _is_administrative_merge_message(message: str) -> bool:
    lowered = message.lower()
    if not lowered.startswith("merge pull request #"):
        return False
    administrative_terms = (
        "handoff",
        "successor",
        "closeout",
        "evidence",
        "refresh",
        "freshness",
    )
    return any(term in lowered for term in administrative_terms)


def _git_parent_commits(project_root: Path, commit: str) -> list[str]:
    try:
        parents = subprocess.check_output(
            ["git", "show", "-s", "--pretty=%P", commit],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return []
    return [_short_commit(parent) for parent in parents.split() if parent.strip()]


def _is_administrative_merge_commit(
    project_root: Path,
    detected_head: str,
    detected_message: str,
    expected_commits: list[str],
) -> bool:
    """Return true for GitHub merge commits that only merge administrative handoff/evidence work.

    A normal product merge must still trigger the freshness guard. Therefore the
    check requires both a GitHub-style merge message and administrative wording
    in the full merge message, plus a parent already represented by handoff
    safe/admin state.
    """

    message = detected_message.lower()
    if not _is_administrative_merge_message(message):
        return False
    parents = _git_parent_commits(project_root, detected_head)
    if any(_commit_matches(parent, expected_commits) for parent in parents):
        return True
    return _has_expected_commit_in_first_parent_admin_chain(
        project_root,
        detected_head,
        expected_commits,
    )


def _has_expected_commit_in_first_parent_admin_chain(
    project_root: Path,
    start_commit: str,
    expected_commits: list[str],
    *,
    max_depth: int = 20,
) -> bool:
    """Accept bounded chains of administrative GitHub merge commits.

    This prevents a loop where every administrative merge commit requires a new
    handoff-state refresh. The walk is deliberately first-parent and bounded:
    product merges still warn unless every merge on the path is itself
    administrative and the chain reaches an already represented commit.
    """

    current = start_commit
    for _ in range(max_depth):
        parents = _git_parent_commits(project_root, current)
        if not parents:
            return False
        first_parent = parents[0]
        if _commit_matches(first_parent, expected_commits):
            return True
        subject = _git_commit_subject(project_root, first_parent)
        message = _git_commit_message(project_root, first_parent)
        if not _is_administrative_merge_message(message or subject):
            return False
        current = first_parent
    return False


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
    candidates = sorted(
        candidate
        for pattern in SUCCESSOR_HANDOFF_GLOBS
        for candidate in terminal_dir.glob(pattern)
    )
    if not candidates:
        return None
    return candidates[-1]


def _relative_to_project(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path
