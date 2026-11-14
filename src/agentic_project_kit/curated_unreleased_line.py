"""K8 (owner decision 2026-11-14): in a curated workspace a product PR brings its Unreleased line.

With ``release.changelog_summary: curated`` the Unreleased bullets are the release summary, for the
Kit's own release exactly as for a workspace (K8; ``make-new-kit-release`` passes no summary lines).
A PR whose release-note category is a product category must therefore add or reword at least one
Unreleased bullet against its merge base with ``origin/main``. Otherwise the gap surfaces only in
the release (KIT-CHK-CURATED-SUMMARY). ``work finish`` decides this before the commit
(KIT-CHK-CURATED-UNRELEASED-LINE).

Exempt: non-product categories (Docs, Tests / Gates, Governance, Transfer / Handoff, Release,
Known Issues), the branches of a release run (they consume Unreleased) and a Kit installation
return. Without a readable merge base the check cannot decide and does not block.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from agentic_project_kit.release_changelog import unreleased_bullets

CHECK_ID = "KIT-CHK-CURATED-UNRELEASED-LINE"
PRODUCT_CATEGORIES = frozenset({"Added", "Changed", "Fixed", "Breaking"})
RELEASE_RUN_BRANCH_SUFFIXES = ("", "-doi", "-evidence")
_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")


def category_of(pr_body: str) -> str:
    """The release-note category that work finish put into the PR body (K2), else ''."""
    for line in pr_body.splitlines()[:40]:
        match = re.fullmatch(r"\s*release-note-category\s*:\s*(.*?)\s*", line, re.I)
        if match:
            return match.group(1)
    return ""


def is_commit_sha(text: str) -> bool:
    return bool(_SHA.fullmatch(text.strip()))


def release_run_owning(root: Path, branch: str) -> str:
    """Version of a release run that owns ``branch`` (release, DOI or evidence branch), else ''."""
    from agentic_project_kit.workspace import load_workspace

    try:
        tmp = Path(load_workspace(root, suppress_legacy_profile_warning=True).tmp())
    except (OSError, ValueError, RuntimeError):
        return ""
    tmp = tmp if tmp.is_absolute() else root / tmp
    for state_path in sorted(tmp.glob("release-run-*.json")):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(state, dict) or state.get("kind") != "release_run_state":
            continue
        release_branch = str(state.get("release_branch") or "")
        if release_branch and branch in {release_branch + suffix for suffix in RELEASE_RUN_BRANCH_SUFFIXES}:
            return str(state.get("version") or "")
    return ""


def added_bullets(base_text: str, head_text: str) -> list[str]:
    """Unreleased bullets of ``head_text`` that ``base_text`` does not have (a reworded bullet counts)."""
    remaining = Counter(unreleased_bullets(base_text))
    added: list[str] = []
    for bullet in unreleased_bullets(head_text):
        if remaining[bullet]:
            remaining[bullet] -= 1
        else:
            added.append(bullet)
    return added


def missing_line_reason(category: str, base_text: str, head_text: str) -> str:
    """Why this PR blocks, or '' when it brings an Unreleased line or needs none."""
    if category not in PRODUCT_CATEGORIES or added_bullets(base_text, head_text):
        return ""
    return (
        f"Curated changelog: a {category} PR adds its line to `## Unreleased`; those lines are the "
        "release summary (K8). Add one one-line bullet to CHANGELOG.md and rerun with --path CHANGELOG.md, "
        "or choose a non-product --release-note-category (Docs, Tests / Gates, Governance, "
        "Transfer / Handoff) when nothing user-facing changed."
    )
