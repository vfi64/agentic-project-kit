"""External workspaces use v2; older installed Kits retain their own v1 policy."""

from pathlib import Path

from agentic_project_kit.workspace_detection import is_external_manifest_workspace

def external_projection_contract_version() -> int:
    """The current package's external projection contract."""
    return 2


def uses_external_projection_v2(root: Path) -> bool:
    return is_external_manifest_workspace(root)
