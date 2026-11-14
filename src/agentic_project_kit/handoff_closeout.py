"""The handoff projection files that ``work finish`` commits after its handoff refresh.

``work finish`` writes them in its ``handoff-commit`` step (``Refresh handoff for <title>``). The
release run's B4 resume (KIT-GF-080, K7) reads the same list to accept such a commit on the release
branch, so both use this one definition.
"""
from __future__ import annotations

from pathlib import Path

HANDOFF_CLOSEOUT_PROMPTS = (
    "START_NEW_CHAT_PROMPT.md",
    "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "NEXT_CHAT_BOOTSTRAP.md",
)
HANDOFF_CLOSEOUT_PACKAGE_FILES = (
    "execution_contract.json",
    "source_manifest.json",
    "successor_context.yaml",
    "successor_prompt.md",
    "validation_report.json",
)


def handoff_closeout_paths(workspace) -> list[Path]:
    """Paths of the handoff projections, resolved against ``workspace`` (a loaded Workspace)."""
    return [
        *(workspace.handoff_file(name) for name in HANDOFF_CLOSEOUT_PROMPTS),
        *(workspace.package_file(name) for name in HANDOFF_CLOSEOUT_PACKAGE_FILES),
    ]
