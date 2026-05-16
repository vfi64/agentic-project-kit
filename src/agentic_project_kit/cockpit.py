from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable


@dataclass(frozen=True)
class CockpitAction:
    action_id: str
    label: str
    category: str
    command: tuple[str, ...]
    safety: str
    description: str


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


READ_ONLY = "read_only"
BOUNDED = "bounded"
DESTRUCTIVE = "destructive"

CommandExecutor = Callable[[tuple[str, ...], Path], subprocess.CompletedProcess[str]]


def cockpit_actions() -> list[CockpitAction]:
    return [
        CockpitAction("git.status", "Git status", "git", ("git", "status", "--short"), READ_ONLY, "Show uncommitted local changes."),
        CockpitAction("workflow.state", "Workflow state", "workflow", ("agentic-kit", "workflow", "state"), READ_ONLY, "Show guided workflow state and recommended next step."),
        CockpitAction("workflow.list", "Workflow items", "workflow", ("agentic-kit", "workflow", "list"), READ_ONLY, "List stored local workflow items."),
        CockpitAction("gate.check-docs", "Documentation gate", "gate", ("agentic-kit", "check-docs"), READ_ONLY, "Run deterministic documentation gates."),
        CockpitAction("gate.doctor", "Doctor", "gate", ("agentic-kit", "doctor"), READ_ONLY, "Run compact project health checks."),
        CockpitAction("audit.doc-mesh", "Document mesh audit", "audit", ("agentic-kit", "doc-mesh-audit"), READ_ONLY, "Audit cross-document state and governance drift."),
        CockpitAction("audit.doc-lifecycle", "Document lifecycle audit", "audit", ("agentic-kit", "doc-lifecycle-audit"), READ_ONLY, "Audit lifecycle metadata for governed planning documents."),
        CockpitAction("release.plan", "Release plan", "release", ("agentic-kit", "release-plan"), READ_ONLY, "Print release preparation checklist."),
        CockpitAction("release.check", "Release check", "release", ("agentic-kit", "release-check"), READ_ONLY, "Validate release state for a target version."),
        CockpitAction("release.post-check", "Post-release check", "release", ("agentic-kit", "post-release-check"), READ_ONLY, "Validate GitHub and Zenodo post-release state."),
        CockpitAction("workflow.go", "Run one bounded workflow step", "workflow", ("agentic-kit", "workflow", "go"), BOUNDED, "Request and run one bounded workflow step."),
    ]


def action_by_id(action_id: str, actions: list[CockpitAction] | None = None) -> CockpitAction | None:
    selected = actions if actions is not None else cockpit_actions()
    for action in selected:
        if action.action_id == action_id:
            return action
    return None


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
        return CockpitActionResult(action_id, False, False, None, "", "", f"Unknown cockpit action: {action_id}")
    if action.safety == DESTRUCTIVE:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked destructive cockpit action: {action.action_id}")
    if action.safety == BOUNDED and not allow_bounded:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked bounded cockpit action without explicit allow flag: {action.action_id}")
    if action.safety not in {READ_ONLY, BOUNDED}:
        return CockpitActionResult(action.action_id, False, False, None, "", "", f"Blocked cockpit action with unknown safety class: {action.safety}")

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


def render_action_inventory(actions: list[CockpitAction] | None = None) -> str:
    selected = actions if actions is not None else cockpit_actions()
    lines = ["Local cockpit actions"]
    for action in selected:
        command = " ".join(action.command)
        lines.append(f"- {action.action_id} [{action.category}/{action.safety}] {command}")
        lines.append(f"  {action.description}")
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


def _run_command(command: tuple[str, ...], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=root, text=True, capture_output=True, check=False)


def _present(value: bool) -> str:
    return "present" if value else "missing"
