"""Validate and render PR metadata before a work-finish side effect."""
from pathlib import Path
import re

from agentic_project_kit.release_notes import RELEASE_NOTE_CATEGORIES


def prepare_work_finish_body(
    title: str, *, body: str = "", body_file: Path | None = None,
    release_note_category: str = "",
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
    rendered = "\n".join(content).strip()
    # The release-notes classifier reads the first 40 lines of a PR body.
    return f"release-note-category: {selected}\n\n{rendered}" if selected else rendered
