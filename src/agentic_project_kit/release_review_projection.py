"""Kit-only review projection refreshed after release manifest synchronization."""
from pathlib import Path

from agentic_project_kit.workspace_detection import is_agentic_project_kit_development_checkout

REVIEW_SCRIPT = "scripts/task_selection_design_check.py"
REVIEW_OUTPUT = "docs/reports/task_selection_design_20261026/README.md"


def review_projection_command(root: Path, python_executable: str) -> list[str] | None:
    """Never execute Kit development generators in consumer workspaces.

    In a Kit checkout the script is required: a missing generator must fail,
    rather than leaving a stale matrix behind a successful release preparation.
    """
    if not is_agentic_project_kit_development_checkout(root):
        return None
    return [python_executable, REVIEW_SCRIPT, "--out", REVIEW_OUTPUT]
