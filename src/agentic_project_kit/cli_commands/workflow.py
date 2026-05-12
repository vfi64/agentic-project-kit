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


def _write_state(root: Path, state: str) -> None:
    if state not in VALID_STATES:
        raise typer.BadParameter(f"invalid workflow state: {state}")
    state_path = _rooted(STATE_FILE, root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(state + "\n", encoding="utf-8")


def _run_next_step(root: Path) -> int:
    script = _rooted(NEXT_STEP_SCRIPT, root)
    if not script.exists():
        raise typer.BadParameter(f"missing workflow entrypoint: {NEXT_STEP_SCRIPT}")
    completed = subprocess.run([sys.executable, str(script)], cwd=root.resolve(), check=False)
    return int(completed.returncode)


@workflow_app.command("request")
def workflow_request(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/workflow_state."),
) -> None:
    """Mark the declarative workflow request as ready to run."""
    root = project_root.resolve()
    if not _rooted(WORK_FILE, root).exists():
        raise typer.BadParameter(f"missing declarative workflow file: {WORK_FILE}")
    state = _read_state(root)
    if state not in {"IDLE", "FAILED"}:
        raise typer.BadParameter(f"refusing to request workflow from state: {state}")
    _write_state(root, "REQUESTED")
    typer.echo("workflow_state=REQUESTED")
    typer.echo("Next: agentic-kit workflow run")


@workflow_app.command("run")
def workflow_run(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Run one bounded workflow state-machine step."""
    raise typer.Exit(code=_run_next_step(project_root.resolve()))


@workflow_app.command("status")
def workflow_status(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/workflow_state."),
) -> None:
    """Print the current workflow state and bounded evidence pointers."""
    root = project_root.resolve()
    state = _read_state(root)
    typer.echo(f"workflow_state={state}")
    work_file = _rooted(WORK_FILE, root)
    typer.echo(f"current_work={'present' if work_file.exists() else 'missing'}")
    branch_file = _rooted(BRANCH_FILE, root)
    if branch_file.exists():
        typer.echo(f"evidence_branch={branch_file.read_text(encoding='utf-8').strip()}")
    report_file = _rooted(REPORT_FILE, root)
    if report_file.exists():
        typer.echo(f"current_report={REPORT_FILE}")


@workflow_app.command("cleanup")
def workflow_cleanup(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Cleanup a completed uploaded workflow evidence branch."""
    root = project_root.resolve()
    state = _read_state(root)
    if state not in {"UPLOADED", "CLEANUP"}:
        typer.echo(f"workflow_state={state}")
        typer.echo("No cleanup action available for current state.")
        raise typer.Exit(code=0)
    raise typer.Exit(code=_run_next_step(root))
