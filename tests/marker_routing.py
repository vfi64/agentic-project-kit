from __future__ import annotations

from pathlib import Path


REPO_STATE_PATTERNS = (
    "AGENTS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "docs/",
    ".agentic/",
    "pyproject.toml",
    "git ",
    "subprocess.run",
    "build_current_reference(",
    "load_manifest(Path(\".\")",
    "load_workspace(Path(\".\")",
    "CliRunner().invoke(app",
)


def marker_names_for_file(path: Path) -> set[str]:
    markers: set[str] = set()
    if path.name == "test_gui_cockpit.py":
        markers.add("gui")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return markers
    if any(pattern in text for pattern in REPO_STATE_PATTERNS):
        markers.add("repo_state")
    return markers
