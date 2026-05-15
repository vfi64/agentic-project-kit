from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

workflow_app = typer.Typer(help="Run and inspect bounded local workflow handoff states.")

VALID_STATES = {"IDLE", "TEST", "UPLOAD", "CLEANUP", "REQUESTED", "RUNNING", "UPLOADED", "FAILED"}
STATE_FILE = Path(".agentic/workflow_state")
WORK_FILE = Path(".agentic/current_work.yaml")
BRANCH_FILE = Path("tmp/agent-evidence/latest-branch.txt")
REPORT_FILE = Path("docs/reports/CURRENT_WORKFLOW_OUTPUT.md")
NEXT_STEP_SCRIPT = Path("tools/next-step.py")
TEMP_PREFIX = "temp/workflow-evidence-"


def _rooted(path: Path, root: Path) -> Path:
    return root.resolve() / path


def _read_state(root: Path) -> str:
    state_path = _rooted(STATE_FILE, root)
    if not state_path.exists():
        raise typer.BadParameter(f"missing state file: {STATE_FILE}")
    state = state_path.read_text(encoding="utf-8").strip()
    if state not in VALID_STATES:
        raise typer.BadParameter(f"invalid workflow state: {state}")
    return state


def _workflow_request_state(root: Path) -> str:
    work_path = _rooted(WORK_FILE, root)
    if not work_path.exists():
        raise typer.BadParameter(f"missing declarative workflow file: {WORK_FILE}")
    for line in work_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("state:"):
            return stripped.split(":", 1)[1].strip().upper() or "READY"
    return "READY"


def _set_workflow_request_state(root: Path, request_state: str) -> None:
    work_path = _rooted(WORK_FILE, root)
    if not work_path.exists():
        raise typer.BadParameter(f"missing declarative workflow file: {WORK_FILE}")
    normalized = request_state.upper()
    if normalized not in {"READY", "REQUESTED"}:
        raise typer.BadParameter(f"invalid workflow request state: {request_state}")
    lines = work_path.read_text(encoding="utf-8").splitlines()
    replaced = False
    output: list[str] = []
    for line in lines:
        if line.strip().startswith("state:") and not replaced:
            indent = line[: len(line) - len(line.lstrip())]
            output.append(f"{indent}state: {normalized}")
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.insert(1 if output else 0, f"state: {normalized}")
    work_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
    script = _rooted(NEXT_STEP_SCRIPT, root)
    if not script.exists():
        raise typer.BadParameter(f"missing workflow entrypoint: {NEXT_STEP_SCRIPT}")
    completed = subprocess.run([sys.executable, str(script), *(extra_args or [])], cwd=root.resolve(), check=False)
    return int(completed.returncode)


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root.resolve(), text=True, capture_output=True, check=False)


def _is_git_repository(root: Path) -> bool:
    result = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"




def _working_tree_dirty(root: Path) -> bool:
    if not _is_git_repository(root):
        return False
    result = _run_git(root, ["status", "--porcelain"])
    return result.returncode == 0 and bool(result.stdout.strip())


def _status_interpretation(state: str, work_state: str | None, dirty: bool) -> tuple[list[str], list[str]]:
    interpretation: list[str] = []
    recommendation: list[str] = []
    if dirty:
        interpretation.append("Working tree has uncommitted changes.")
        recommendation.append("Run: git status --short")
        recommendation.append("Do not start workflow automation until the working tree is clean or intentionally staged.")
        return interpretation, recommendation
    if work_state == "REQUESTED":
        interpretation.append("A workflow request is pending.")
        recommendation.append("Run: agentic-kit workflow run")
    elif state == "UPLOADED":
        interpretation.append("Workflow evidence was uploaded and cleanup is pending.")
        recommendation.append("Run: agentic-kit workflow cleanup")
    elif state == "FAILED":
        interpretation.append("The last workflow step failed.")
        recommendation.append("Run: agentic-kit workflow fail-report")
        recommendation.append("Inspect docs/reports/CURRENT_WORKFLOW_OUTPUT.md and git status before cleanup or retry.")
        recommendation.append("Do not rerun workflow automation until the failure cause is understood.")
    elif state == "IDLE" and work_state in {None, "READY"}:
        interpretation.append("No active workflow request.")
        recommendation.append("Define one concrete slice before requesting workflow automation.")
        recommendation.append("Run: agentic-kit workflow request")
        recommendation.append("Then run: agentic-kit workflow run")
    else:
        interpretation.append("Workflow state requires manual review.")
        recommendation.append("Inspect workflow status and evidence before changing state.")
    return interpretation, recommendation


def _print_status_explanation(root: Path, state: str, work_state: str | None, report_present: bool) -> None:
    dirty = _working_tree_dirty(root)
    interpretation, recommendation = _status_interpretation(state, work_state, dirty)
    typer.echo("")
    typer.echo("Safety:")
    typer.echo("- This command is read-only.")
    if report_present:
        typer.echo("- current_report points to the latest local workflow-output summary.")
    typer.echo("")
    typer.echo("Interpretation:")
    for line in interpretation:
        typer.echo(f"- {line}")
    typer.echo("")
    typer.echo("Recommended next step:")
    for line in recommendation:
        typer.echo(f"- {line}")
    typer.echo("")
    typer.echo("Optional checks:")
    typer.echo("- agentic-kit doctor")
    typer.echo("- agentic-kit check-docs")

def _safe_temp_branch(branch: str) -> str | None:
    normalized = branch.strip()
    if not normalized.startswith(TEMP_PREFIX):
        return None
    if ".." in normalized or normalized.endswith("/"):
        return None
    return normalized


def _local_temp_branches(root: Path) -> list[str]:
    result = _run_git(root, ["branch", "--list", f"{TEMP_PREFIX}*"])
    if result.returncode != 0:
        raise typer.BadParameter(result.stderr.strip() or "failed to list local workflow evidence branches")
    branches: list[str] = []
    for line in result.stdout.splitlines():
        branch = _safe_temp_branch(line.replace("*", "", 1).strip())
        if branch is not None:
            branches.append(branch)
    return branches


def _remote_temp_branches(root: Path) -> list[str]:
    result = _run_git(root, ["ls-remote", "--heads", "origin", f"{TEMP_PREFIX}*"])
    if result.returncode != 0:
        return []
    branches: list[str] = []
    for line in result.stdout.splitlines():
        ref = line.split()[-1] if line.split() else ""
        prefix = "refs/heads/"
        branch = ref[len(prefix) :] if ref.startswith(prefix) else ref
        safe = _safe_temp_branch(branch)
        if safe is not None:
            branches.append(safe)
    return branches


def _cleanup_stale_temp_branches(root: Path) -> int:
    if not _is_git_repository(root):
        return 0
    local_branches = _local_temp_branches(root)
    remote_branches = _remote_temp_branches(root)
    branches = sorted(set(local_branches + remote_branches))
    if not branches:
        return 0
    for branch in branches:
        if branch in local_branches:
            _run_git(root, ["branch", "-D", branch])
            typer.echo(f"Deleted local stale workflow evidence branch: {branch}")
        if branch in remote_branches:
            _run_git(root, ["push", "origin", "--delete", branch])
            typer.echo(f"Deleted remote stale workflow evidence branch: {branch}")
    return len(branches)


@workflow_app.command("request")
def workflow_request(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/current_work.yaml."),
) -> None:
    """Request the configured declarative workflow without running it."""
    root = project_root.resolve()
    state = _read_state(root)
    if state != "IDLE":
        raise typer.BadParameter(f"refusing to request workflow from state: {state}")
    _workflow_request_state(root)
    _set_workflow_request_state(root, "REQUESTED")
    typer.echo(f"Current workflow request file: {WORK_FILE}")
    typer.echo("Workflow request state: REQUESTED")
    typer.echo("Next state: IDLE")


@workflow_app.command("run")
def workflow_run(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Run one bounded workflow state-machine step."""
    raise typer.Exit(code=_run_next_step(project_root.resolve()))


@workflow_app.command("status")
def workflow_status(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/workflow_state."),
    explain: bool = typer.Option(False, "--explain", help="Explain the current state and recommend a safe next step."),
) -> None:
    """Print the current workflow state and bounded evidence pointers."""
    root = project_root.resolve()
    state = _read_state(root)
    typer.echo(f"workflow_state={state}")
    work_file = _rooted(WORK_FILE, root)
    typer.echo(f"current_work={'present' if work_file.exists() else 'missing'}")
    work_state: str | None = None
    if work_file.exists():
        work_state = _workflow_request_state(root)
        typer.echo(f"current_work_state={work_state}")
    branch_file = _rooted(BRANCH_FILE, root)
    if branch_file.exists():
        typer.echo(f"evidence_branch={branch_file.read_text(encoding='utf-8').strip()}")
    report_file = _rooted(REPORT_FILE, root)
    report_present = report_file.exists()
    if report_present:
        typer.echo(f"current_report={REPORT_FILE}")
    if explain:
        _print_status_explanation(root, state, work_state, report_present)


@workflow_app.command("fail-report")
def workflow_fail_report(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Upload preserved FAILED workflow evidence without cleanup or retry."""
    root = project_root.resolve()
    state = _read_state(root)
    if state != "FAILED":
        raise typer.BadParameter(f"fail-report requires FAILED state, got {state}")
    raise typer.Exit(code=_run_next_step(root, ["--fail-report"]))


@workflow_app.command("cleanup")
def workflow_cleanup(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Cleanup completed or stale temporary workflow evidence branches."""
    root = project_root.resolve()
    state = _read_state(root)
    if state in {"UPLOADED", "CLEANUP"}:
        raise typer.Exit(code=_run_next_step(root))
    stale_count = _cleanup_stale_temp_branches(root)
    typer.echo(f"workflow_state={state}")
    if stale_count:
        typer.echo(f"Cleaned stale workflow evidence branches: {stale_count}")
    else:
        typer.echo("No cleanup action available for current state.")
    raise typer.Exit(code=0)
