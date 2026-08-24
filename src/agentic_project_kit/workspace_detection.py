from __future__ import annotations

from pathlib import Path

AGENTIC_PROJECT_MARKERS = (
    ".agentic/config.yaml",
    ".agentic/project.yaml",
    "sentinel.yaml",
    "docs/reference/agentic-kit-commands.json",
    "docs/STATUS.md",
    "docs/TEST_GATES.md",
    "docs/handoff/CURRENT_HANDOFF.md",
)

NON_WORKSPACE_NEXT_STEP = (
    "Run `agentic-kit init NAME` to create a governed project, or "
    "`agentic-kit workspace init --root PATH` to add the operating layer to an existing repository."
)

NON_WORKSPACE_LABEL = "not an Agentic Project Kit workspace"


def has_agentic_project_markers(project_root: Path) -> bool:
    root = Path(project_root)
    return any((root / marker).exists() for marker in AGENTIC_PROJECT_MARKERS)


def is_non_workspace_root(project_root: Path) -> bool:
    return not has_agentic_project_markers(project_root)


def has_generated_project_contract(project_root: Path) -> bool:
    return (Path(project_root) / ".agentic/project.yaml").exists()


def is_agentic_project_kit_development_checkout(project_root: Path) -> bool:
    root = Path(project_root)
    return (
        (root / "src" / "agentic_project_kit").is_dir()
        and (root / "docs" / "reference" / "agentic-kit-commands.json").exists()
        and (root / "pyproject.toml").exists()
    )


def is_external_manifest_workspace(project_root: Path) -> bool:
    root = Path(project_root)
    return (
        (root / ".agentic/config.yaml").exists()
        and not is_agentic_project_kit_development_checkout(root)
    )


def non_workspace_message(project_root: Path) -> str:
    return f"{Path(project_root).resolve()} is {NON_WORKSPACE_LABEL}. {NON_WORKSPACE_NEXT_STEP}"
