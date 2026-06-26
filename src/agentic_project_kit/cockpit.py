from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import Callable


@dataclass(frozen=True)
class CockpitAction:
    action_id: str
    label: str
    category: str
    command: tuple[str, ...]
    safety: str
    description: str
    short_description: str


@dataclass(frozen=True)
class CockpitStatus:
    project_root: Path
    git_branch: str
    git_dirty: bool
    workflow_state: str
    current_work_present: bool
    current_work_state: str | None


@dataclass(frozen=True)
class CockpitActionResult:
    action_id: str
    allowed: bool
    executed: bool
    returncode: int | None
    stdout: str
    stderr: str
    message: str
    result_status: str = "PENDING"
    safety: str = "unknown"
    terminal_log: str | None = None
    command_report: str | None = None
    dirty_state: str = "unknown"
    next_allowed_actions: tuple[str, ...] = ()


READ_ONLY = "read_only"
BOUNDED = "bounded"
DESTRUCTIVE = "destructive"

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_PENDING = "PENDING"
RESULT_HARD_FAIL = "HARD-FAIL"

CommandExecutor = Callable[[tuple[str, ...], Path], subprocess.CompletedProcess[str]]


def cockpit_actions() -> list[CockpitAction]:
    return [
        CockpitAction(
            "git.status",
            "Git status",
            "git",
            ("git", "status", "--short"),
            READ_ONLY,
            "Show uncommitted local changes.",
            "Show local uncommitted changes",
        ),
        CockpitAction(
            "workflow.state",
            "Workflow state",
            "workflow",
            ("agentic-kit", "workflow", "state"),
            READ_ONLY,
            "Show guided workflow state and recommended next step.",
            "Show current state and recommended next step",
        ),
        CockpitAction(
            "dialog.rn",
            "Run Next Work Order",
            "dialog",
            ("agentic-kit", "rn"),
            BOUNDED,
            "Synchronize main and run the next typed work order.",
            "Run the next queued work order",
        ),
        CockpitAction(
            "dialog.rnc",
            "Close Out Last Run",
            "dialog",
            ("agentic-kit", "rnc"),
            BOUNDED,
            "Commit and push the expected closeout paths from the last remote-next run.",
            "Commit and push the last run's closeout paths",
        ),
        CockpitAction(
            "workflow.list",
            "Workflow items",
            "workflow",
            ("agentic-kit", "workflow", "list"),
            READ_ONLY,
            "List stored local workflow items.",
            "List queued workflow items",
        ),
        CockpitAction(
            "gate.check-docs",
            "Documentation gate",
            "gate",
            ("agentic-kit", "check-docs"),
            READ_ONLY,
            "Run deterministic documentation gates.",
            "Run documentation checks",
        ),
        CockpitAction(
            "gate.doctor",
            "Doctor",
            "gate",
            ("agentic-kit", "doctor"),
            READ_ONLY,
            "Run compact project health checks.",
            "Run project health checks",
        ),
        CockpitAction(
            "audit.doc-mesh",
            "Document mesh audit",
            "audit",
            ("agentic-kit", "doc-mesh-audit"),
            READ_ONLY,
            "Audit cross-document state and governance drift.",
            "Audit cross-document drift",
        ),
        CockpitAction(
            "audit.doc-lifecycle",
            "Document lifecycle audit",
            "audit",
            ("agentic-kit", "doc-lifecycle-audit"),
            READ_ONLY,
            "Audit lifecycle metadata for governed planning documents.",
            "Audit document lifecycle metadata",
        ),
        CockpitAction(
            "audit.pr-hygiene",
            "PR hygiene",
            "audit",
            ("agentic-kit", "pr-hygiene"),
            READ_ONLY,
            "Diagnose stale, duplicate, or empty pull-request and branch hygiene signals.",
            "Inspect pull-request hygiene",
        ),
        CockpitAction(
            "rules.communication-refresh",
            "Communication Rules Refresh",
            "rules",
            ("agentic-kit", "rules", "communication-refresh", "--publish", "--json"),
            BOUNDED,
            "Generate the communication rule capsule and d2 pending state.",
            "Refresh communication rules (writes files)",
        ),
        CockpitAction(
            "rules.handoff-refresh",
            "Handoff Rules Refresh",
            "rules",
            ("agentic-kit", "rules", "handoff-refresh"),
            BOUNDED,
            "Generate the repo-backed handoff rules refresh file for d3.",
            "Refresh handoff rules (writes files)",
        ),
        CockpitAction(
            "handoff.successor-prompt",
            "Successor Handoff Package",
            "handoff",
            ("agentic-kit", "transfer", "chat-switch-complete", "--render-prompt"),
            BOUNDED,
            "Render the copy-and-paste successor chat prompt through the guarded transfer command.",
            "Render the successor handoff prompt",
        ),
        CockpitAction(
            "release.plan",
            "Release plan",
            "release",
            ("agentic-kit", "release-plan"),
            READ_ONLY,
            "Print release preparation checklist.",
            "Show the release preparation checklist",
        ),
        CockpitAction(
            "release.check",
            "Release check",
            "release",
            ("agentic-kit", "release-check"),
            READ_ONLY,
            "Validate release state for a target version.",
            "Validate release readiness",
        ),
        CockpitAction(
            "release.post-check",
            "Post-release check",
            "release",
            ("agentic-kit", "post-release-check"),
            READ_ONLY,
            "Validate GitHub and Zenodo post-release state.",
            "Validate post-release state",
        ),
        CockpitAction(
            "workflow.go",
            "Run one bounded workflow step",
            "workflow",
            ("agentic-kit", "workflow", "go"),
            BOUNDED,
            "Request and run one bounded workflow step.",
            "Run one guarded workflow step",
        ),
    ]


def action_by_id(action_id: str, actions: list[CockpitAction] | None = None) -> CockpitAction | None:
    selected = actions if actions is not None else cockpit_actions()
    for action in selected:
        if action.action_id == action_id:
            return action
    return None




def validate_cockpit_action_registry(actions: list[CockpitAction] | None = None) -> list[str]:
    selected = actions if actions is not None else cockpit_actions()
    errors: list[str] = []
    seen: set[str] = set()
    allowed_safety = {READ_ONLY, BOUNDED, DESTRUCTIVE}
    for action in selected:
        if not action.action_id.strip():
            errors.append('empty action_id')
        if action.action_id in seen:
            errors.append(f'duplicate action_id: {action.action_id}')
        seen.add(action.action_id)
        if action.safety not in allowed_safety:
            errors.append(f'invalid safety for {action.action_id}: {action.safety}')
        if not action.command:
            errors.append(f'empty command for {action.action_id}')
        if any(not part for part in action.command):
            errors.append(f'empty command part for {action.action_id}')
        if not action.category.strip():
            errors.append(f'empty category for {action.action_id}')
        if not action.label.strip():
            errors.append(f'empty label for {action.action_id}')
        if not action.description.strip():
            errors.append(f'empty description for {action.action_id}')
        if not action.short_description.strip():
            errors.append(f'empty short_description for {action.action_id}')
    return errors


def cockpit_registry_contract_as_json_data(actions: list[CockpitAction] | None = None) -> dict[str, object]:
    selected = actions if actions is not None else cockpit_actions()
    errors = validate_cockpit_action_registry(selected)
    return {
        'schema_version': 1,
        'registry_only': True,
        'valid': not errors,
        'errors': errors,
        'allowed_action_ids': [action.action_id for action in selected],
        'allowed_safety_classes': [READ_ONLY, BOUNDED, DESTRUCTIVE],
    }

def run_cockpit_action(
    action_id: str,
    project_root: Path,
    *,
    allow_bounded: bool = False,
    actions: list[CockpitAction] | None = None,
    executor: CommandExecutor | None = None,
) -> CockpitActionResult:
    action = action_by_id(action_id, actions)
    if action is None:
        return CockpitActionResult(action_id, False, False, None, "", "", f"Unknown cockpit action: {action_id}", RESULT_FAIL, "unknown", next_allowed_actions=("cockpit.actions",))
    if action.safety == DESTRUCTIVE:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked destructive cockpit action: {action.action_id}", RESULT_HARD_FAIL, action.safety, next_allowed_actions=("cockpit.actions",))
    if action.safety == BOUNDED and not allow_bounded:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked bounded cockpit action without explicit allow flag: {action.action_id}", RESULT_PENDING, action.safety, next_allowed_actions=("cockpit.actions",))
    if action.safety not in {READ_ONLY, BOUNDED}:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked cockpit action with unknown safety class: {action.safety}", RESULT_HARD_FAIL, action.safety, next_allowed_actions=("cockpit.actions",))

    runner = executor if executor is not None else _run_command
    completed = runner(action.command, project_root.resolve())

    return CockpitActionResult(
        action.action_id,
        True,
        True,
        completed.returncode,
        completed.stdout.strip(),
        completed.stderr.strip(),
        "Cockpit action executed.",
        RESULT_PASS if completed.returncode == 0 else RESULT_FAIL,
        action.safety,
        next_allowed_actions=("cockpit.actions",),
    )


def build_cockpit_status(project_root: Path) -> CockpitStatus:
    root = project_root.resolve()
    workflow_state = _read_text(root / ".agentic" / "workflow_state", "missing").strip() or "missing"
    current_work_path = root / ".agentic" / "current_work.yaml"
    return CockpitStatus(
        project_root=root,
        git_branch=_git_stdout(root, ["branch", "--show-current"], "unknown"),
        git_dirty=bool(_git_stdout(root, ["status", "--porcelain"], "").strip()),
        workflow_state=workflow_state,
        current_work_present=current_work_path.exists(),
        current_work_state=_read_current_work_state(current_work_path) if current_work_path.exists() else None,
    )


def render_cockpit_status(status: CockpitStatus) -> str:
    lines = [
        "Local cockpit status",
        f"project_root={status.project_root}",
        f"git_branch={status.git_branch}",
        f"git_dirty={str(status.git_dirty).lower()}",
        f"workflow_state={status.workflow_state}",
        f"current_work={_present(status.current_work_present)}",
    ]
    if status.current_work_state is not None:
        lines.append(f"current_work_state={status.current_work_state}")
    lines.extend([
        "",
        "Safety:",
        "- This command is read-only.",
        "- Cockpit action execution allows read-only actions only by default.",
        "",
        "Next:",
        "- Use cockpit actions to inspect the available action inventory.",
    ])
    return "\n".join(lines)


def action_inventory_as_json_data(actions: list[CockpitAction] | None = None) -> dict[str, object]:
    selected = actions if actions is not None else cockpit_actions()
    return {
        "schema_version": 1,
        "actions": [
            {
                "action_id": action.action_id,
                "label": action.label,
                "category": action.category,
                "safety": action.safety,
                "command": list(action.command),
                "description": action.description,
                "short_description": action.short_description,
            }
            for action in selected
        ],
    }





def action_result_as_json_data(result: CockpitActionResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "action_id": result.action_id,
        "result_status": result.result_status,
        "allowed": result.allowed,
        "executed": result.executed,
        "returncode": result.returncode,
        "safety": result.safety,
        "dirty_state": result.dirty_state,
        "terminal_log": result.terminal_log,
        "command_report": result.command_report,
        "next_allowed_actions": list(result.next_allowed_actions),
        "message": result.message,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def render_action_inventory(actions: list[CockpitAction] | None = None) -> str:
    selected = actions if actions is not None else cockpit_actions()
    lines = ["Local cockpit actions"]
    for action in selected:
        command = " ".join(action.command)
        lines.append(f"- {action.action_id} [{action.category}/{action.safety}] {command}")
        lines.append(f"  {action.description}")
    return "\n".join(lines)


def render_action_selection(actions: list[CockpitAction] | None = None) -> str:
    selected = actions if actions is not None else cockpit_actions()
    lines = [
        "Local cockpit action selection",
        "Safety: selection is inspect-only; no action is executed.",
        "",
    ]
    for index, action in enumerate(selected, start=1):
        command = " ".join(action.command)
        lines.append(f"{index:2d}) {action.action_id} [{action.category}/{action.safety}]")
        lines.append(f"    label: {action.label}")
        lines.append(f"    command: {command}")
        lines.append(f"    {action.description}")
    lines.extend([
        "",
        "Next:",
        "- Run read-only actions explicitly with: agentic-kit cockpit run <action-id>",
        "- Bounded actions remain blocked unless the run command receives an explicit allow flag.",
    ])
    return "\n".join(lines)


def _read_text(path: Path, default: str) -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def _read_current_work_state(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("state:"):
            return stripped.split(":", 1)[1].strip().upper() or "READY"
    return "READY"


def _git_stdout(root: Path, args: list[str], default: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return default
    return completed.stdout.strip() or default


def _resolve_command(command: tuple[str, ...], root: Path) -> list[str]:
    if not command:
        return []
    first, *rest = command
    if first != "agentic-kit":
        return list(command)

    candidates: list[Path] = [
        root / ".venv" / "bin" / "agentic-kit",
        root / ".venv" / "Scripts" / "agentic-kit.exe",
    ]
    if sys.executable:
        executable = Path(sys.executable)
        candidates.append(executable.with_name("agentic-kit"))
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate), *rest]

    found = shutil.which("agentic-kit")
    if found:
        return [found, *rest]

    # Keep the original command. _run_command catches FileNotFoundError and
    # returns a structured failure instead of leaking a Tkinter callback traceback.
    return list(command)


def _completed_process_for_missing_command(
    command: tuple[str, ...],
    error: FileNotFoundError,
) -> subprocess.CompletedProcess[str]:
    missing = str(error.filename or (command[0] if command else "<empty>"))
    return subprocess.CompletedProcess(
        list(command),
        127,
        "",
        (
            "Command executable not found: "
            + missing
            + ". Start the GUI from the project virtual environment or keep "
            + ".venv/bin/agentic-kit available for cockpit actions."
        ),
    )


def _run_command(command: tuple[str, ...], root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            _resolve_command(command, root),
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        return _completed_process_for_missing_command(command, exc)


def _present(value: bool) -> str:
    return "present" if value else "missing"
