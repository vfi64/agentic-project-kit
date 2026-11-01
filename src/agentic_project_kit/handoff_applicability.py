"""Resolve the one workspace handoff authority and legitimate virgin state."""

from pathlib import Path
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_external_manifest_workspace


def external_first_cycle_without_handoff(root: Path) -> bool:
    """Init renders content authority but has not performed a runtime handoff."""
    if not is_external_manifest_workspace(root):
        return False
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    if workspace.handoff_state_path().exists():
        return False
    packages = workspace.handoff_packages_latest()
    predecessor = any((packages / name).exists() for name in (
        "execution_contract.json", "successor_context.yaml", "validation_report.json", "source_manifest.json",
    ))
    if not predecessor:
        return True
    from agentic_project_kit.external_handoff_projection import RUNTIME_PATH, check_projection
    # Any runtime evidence (even invalid) prevents treating a lost state as a
    # pristine init. Partial/corrupt projections also remain HANDOFF_REQUIRED.
    from agentic_project_kit.external_projection_policy import uses_external_projection_v2
    return uses_external_projection_v2(root) and not (root / RUNTIME_PATH).exists() and check_projection(root)["status"] == "PASS"


def handoff_applicability(root: Path, explicit_path: str = "") -> dict:
    root = root.resolve()
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    path = root / explicit_path if explicit_path else workspace.handoff_state_path()
    # Only an implicit external authority with no predecessor evidence may be
    # absent. An explicit missing target or a partly lost handoff still fails.
    virgin = (
        not explicit_path
        and is_external_manifest_workspace(root)
        and not path.exists()
        and external_first_cycle_without_handoff(root)
    )
    return {"path": str(path), "state": "NO_PREVIOUS_HANDOFF" if virgin else "HANDOFF_REQUIRED"}
