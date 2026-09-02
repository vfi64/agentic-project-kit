from __future__ import annotations

from pathlib import Path

from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_external_manifest_workspace
from agentic_project_kit.action_specs import (
    built_in_action_specs,
    validate_current_handoff_action_surfaces,
)
from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state
from agentic_project_kit.work_orders import check_work_orders

CONSTITUTION_FILES = (
    ".agentic/project.yaml",
    "sentinel.yaml",
    "AGENTS.md",
    "README.md",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/architecture/ARCHITECTURE_CONTRACT.md",
    "docs/DOCUMENTATION_COVERAGE.yaml",
    "docs/workflow/HANDOFF_STATE.md",
    "docs/workflow/WORK_ORDERS.md",
    "docs/workflow/PARAMETERIZED_ACTIONS.md",
)

EXTERNAL_WORKSPACE_CONSTITUTION_FILES = (
    ".agentic/config.yaml",
    ".agentic/DOC_LIFECYCLE.md",
    ".agentic/registries/documentation.yaml",
    ".agentic/registries/rules.yaml",
    ".agentic/rules/README.md",
    ".agentic/state/status.md",
    ".agentic/state/handoff/README.md",
    ".agentic/transfer/inbox",
    ".agentic/transfer/outbox",
)


def governance_check(project_root: Path = Path(".")) -> list[str]:
    root = Path(project_root)
    if is_external_manifest_workspace(root):
        return _external_workspace_governance_check(root)

    errors: list[str] = []
    for file_name in CONSTITUTION_FILES:
        if not (root / file_name).exists():
            errors.append(f"missing constitution file: {file_name}")
    try:
        handoff_state = load_handoff_state(str(root / ".agentic/handoff_state.yaml"))
    except (FileNotFoundError, ValueError) as exc:
        errors.append(str(exc))
    else:
        errors.extend(f"handoff: {error}" for error in validate_handoff_state(handoff_state))
    errors.extend(f"work-order: {error}" for error in check_work_orders(root))
    action_specs = built_in_action_specs()
    required_actions = (
        "pr-check-merge",
        "release-verify",
        "release-prepare",
        "doi-record",
        "finalize-release",
    )
    for required in required_actions:
        if required not in action_specs:
            errors.append(f"missing action spec: {required}")
    errors.extend(
        f"action-spec: {error}" for error in validate_current_handoff_action_surfaces(action_specs)
    )
    return errors


def _external_workspace_governance_check(project_root: Path) -> list[str]:
    root = Path(project_root)
    errors: list[str] = []
    for file_name in EXTERNAL_WORKSPACE_CONSTITUTION_FILES:
        if not (root / file_name).exists():
            errors.append(f"missing external workspace file: {file_name}")
    try:
        load_workspace(root, suppress_legacy_profile_warning=True)
    except RuntimeError as exc:
        errors.append(f"invalid workspace manifest: {exc}")
    return errors

def render_governance_check(errors: list[str]) -> str:
    if not errors:
        return "Governance check passed"
    lines = ["Governance check failed"]
    lines.extend(f"[FAIL] {error}" for error in errors)
    return "\n".join(lines)
