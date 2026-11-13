"""Validate and render PR metadata before a work-finish side effect."""
from pathlib import Path
import re

from agentic_project_kit.release_notes import RELEASE_NOTE_CATEGORIES


# K2 (V2, release 1.3.0 A2): the category was optional at work finish but mandatory in the release,
# so PRs reached the release as "Unclassified". work finish now always sets one: an explicit value
# or a PR-body marker wins, otherwise the branch kind decides. KIT-CHK-RELEASE-NOTE-CATEGORY.
BRANCH_KIND_CATEGORIES = (
    ("feature/", "Added"),
    ("feat/", "Added"),
    ("fix/", "Fixed"),
    ("bugfix/", "Fixed"),
    ("hotfix/", "Fixed"),
    ("docs/", "Docs"),
    ("doc/", "Docs"),
    ("test/", "Tests / Gates"),
    ("tests/", "Tests / Gates"),
    ("ci/", "Tests / Gates"),
    ("gate/", "Tests / Gates"),
    ("governance/", "Governance"),
    ("release/", "Release"),
    ("transfer/", "Transfer / Handoff"),
    ("handoff/", "Transfer / Handoff"),
)
DEFAULT_RELEASE_NOTE_CATEGORY = "Changed"


def default_release_note_category(branch: str) -> str:
    """Release-note category implied by the branch kind; never empty."""
    lowered = branch.strip().casefold()
    for prefix, category in BRANCH_KIND_CATEGORIES:
        if lowered.startswith(prefix):
            return category
    return DEFAULT_RELEASE_NOTE_CATEGORY


def prepare_work_finish_body(
    title: str, *, body: str = "", body_file: Path | None = None,
    release_note_category: str = "", default_category: str = "",
) -> str:
    if body and body_file is not None:
        raise ValueError("Use either --body or --body-file.")
    text = body_file.read_text(encoding="utf-8") if body_file is not None else body
    text = text or f"Human workflow finish: {title}"
    categories = {
        category.casefold(): category for category in RELEASE_NOTE_CATEGORIES
        if category not in {"Unclassified", "Administrative Handoff Refresh"}
    }

    def normalize(value: str) -> str:
        category = categories.get(value.strip().casefold())
        if category is None:
            raise ValueError("Unsupported release-note category; choose: " + ", ".join(categories.values()))
        return category

    selected = normalize(release_note_category) if release_note_category else ""
    content = []
    for line in text.splitlines():
        marker = re.fullmatch(r"\s*release-note-category\s*:\s*(.*?)\s*", line, re.I)
        if marker:
            category = normalize(marker.group(1))
            if selected and selected != category:
                raise ValueError("Conflicting release-note-category values in PR metadata.")
            selected = category
        else:
            content.append(line)
    if not selected and default_category:
        selected = normalize(default_category)
    rendered = "\n".join(content).strip()
    # The release-notes classifier reads the first 40 lines of a PR body.
    return f"release-note-category: {selected}\n\n{rendered}" if selected else rendered
