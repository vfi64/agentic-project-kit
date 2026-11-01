"""Package-owned expand/contract decision; never a workspace or environment option."""

from pathlib import Path

from agentic_project_kit.workspace_detection import is_external_manifest_workspace

EXTERNAL_PROJECTION_V2_ACTIVE = False


def external_projection_contract_version() -> int:
    """The single activation decision, also queried inside target interpreters."""
    return 2 if EXTERNAL_PROJECTION_V2_ACTIVE else 1


def uses_external_projection_v2(root: Path) -> bool:
    return external_projection_contract_version() == 2 and is_external_manifest_workspace(root)
