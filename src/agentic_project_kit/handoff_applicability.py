"""Resolve the one workspace handoff authority and legitimate virgin state."""

from pathlib import Path
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_external_manifest_workspace


def handoff_applicability(root: Path, explicit_path: str = "") -> dict:
    root = root.resolve()
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    path = root / explicit_path if explicit_path else workspace.handoff_state_path()
    # Only an implicit external authority with no predecessor evidence may be
    # absent. An explicit missing target or a partly lost handoff still fails.
    packages = workspace.handoff_packages_latest()
    predecessor = any(
        (packages / name).exists()
        for name in (
            "execution_contract.json",
            "successor_context.yaml",
            "validation_report.json",
            "source_manifest.json",
        )
    )
    virgin = (
        not explicit_path
        and is_external_manifest_workspace(root)
        and not path.exists()
        and not predecessor
    )
    return {"path": str(path), "state": "NO_PREVIOUS_HANDOFF" if virgin else "HANDOFF_REQUIRED"}
