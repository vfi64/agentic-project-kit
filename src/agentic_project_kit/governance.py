from __future__ import annotations

from pathlib import Path

from agentic_project_kit.action_specs import built_in_action_specs
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

def governance_check() -> list[str]:
    errors: list[str] = []
    for file_name in CONSTITUTION_FILES:
        if not Path(file_name).exists():
            errors.append(f"missing constitution file: {file_name}")
    try:
        handoff_state = load_handoff_state()
    except (FileNotFoundError, ValueError) as exc:
        errors.append(str(exc))
    else:
        errors.extend(f"handoff: {error}" for error in validate_handoff_state(handoff_state))
    errors.extend(f"work-order: {error}" for error in check_work_orders())
    action_specs = built_in_action_specs()
    for required in ("pr-check-merge", "release-verify", "doi-record", "finalize-release"):
        if required not in action_specs:
            errors.append(f"missing action spec: {required}")
    return errors

def render_governance_check(errors: list[str]) -> str:
    if not errors:
        return "Governance check passed"
    lines = ["Governance check failed"]
    lines.extend(f"[FAIL] {error}" for error in errors)
    return "\n".join(lines)
