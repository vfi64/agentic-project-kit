from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import typer

workflow_app = typer.Typer(help="Run and inspect bounded local workflow handoff states.")

VALID_STATES = {"IDLE", "TEST", "UPLOAD", "CLEANUP", "REQUESTED", "RUNNING", "UPLOADED", "FAILED"}
STATE_FILE = Path(".agentic/workflow_state")
WORK_FILE = Path(".agentic/current_work.yaml")
WORK_ITEMS_DIR = Path(".agentic/work_items")
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



def _work_items_dir(root: Path) -> Path:
    return _rooted(WORK_ITEMS_DIR, root)


def _safe_work_item_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise typer.BadParameter("missing workflow item name")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if any(char not in allowed for char in normalized):
        raise typer.BadParameter(f"unsafe workflow item name: {name}")
    if normalized in {".", ".."}:
        raise typer.BadParameter(f"unsafe workflow item name: {name}")
    return normalized


def _work_item_path(root: Path, name: str) -> Path:
    return _work_items_dir(root) / f"{_safe_work_item_name(name)}.yaml"


def _available_work_items(root: Path) -> list[str]:
    directory = _work_items_dir(root)
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("*.yaml"))


def _copy_work_item_to_temp_run_file(root: Path, name: str) -> Path:
    source = _work_item_path(root, name)
    if not source.exists():
        raise typer.BadParameter(f"unknown workflow item: {_safe_work_item_name(name)}")
    target = _rooted(Path("tmp/agent-evidence") / f"run-{_safe_work_item_name(name)}.yaml", root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _workflow_request_state(root: Path) -> str:
    work_path = _rooted(WORK_FILE, root)
    if not work_path.exists():
        raise typer.BadParameter(f"missing declarative workflow file: {WORK_FILE}")
    for line in work_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("state:"):
            return stripped.split(":", 1)[1].strip().upper() or "READY"
    return "READY"


def _set_workflow_file_request_state(work_path: Path, request_state: str) -> None:
    if not work_path.exists():
        raise typer.BadParameter(f"missing declarative workflow file: {work_path}")
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


def _set_workflow_request_state(root: Path, request_state: str) -> None:
    _set_workflow_file_request_state(_rooted(WORK_FILE, root), request_state)


def _run_next_step(root: Path, extra_args: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    script = _rooted(NEXT_STEP_SCRIPT, root)
    if not script.exists():
        raise typer.BadParameter(f"missing workflow entrypoint: {NEXT_STEP_SCRIPT}")
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    completed = subprocess.run([sys.executable, str(script), *(extra_args or [])], cwd=root.resolve(), env=run_env, check=False)
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
        recommendation.append("Run: agentic-kit workflow go")
        recommendation.append("For explicit two-step control: agentic-kit workflow request, then agentic-kit workflow run")
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
        typer.echo("- current_report points to the latest workflow-output summary, not necessarily uploadable local evidence.")
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
    name: str | None = typer.Argument(None, help="Optional stored workflow item name to set before running."),
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Run the current workflow, or set a stored workflow item and run it."""
    root = project_root.resolve()
    if name is None:
        raise typer.Exit(code=_run_next_step(root))
    state = _read_state(root)
    if state != "IDLE":
        raise typer.BadParameter(f"refusing to run workflow item from state: {state}")
    run_file = _copy_work_item_to_temp_run_file(root, name)
    _set_workflow_file_request_state(run_file, "REQUESTED")
    typer.echo(f"Workflow item selected: {_safe_work_item_name(name)}")
    typer.echo(f"Workflow run file: {run_file.relative_to(root.resolve())}")
    typer.echo("Workflow request state: REQUESTED")
    try:
        exit_code = _run_next_step(root, env={"AGENTIC_WORKFLOW_FILE": str(run_file)})
    finally:
        run_file.unlink(missing_ok=True)
    raise typer.Exit(code=exit_code)

@workflow_app.command("state")
def workflow_state(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/workflow_state."),
) -> None:
    """Show guided workflow state; shortcut for workflow status --explain."""
    workflow_status(project_root=project_root, explain=True)


@workflow_app.command("list")
def workflow_list(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/work_items."),
) -> None:
    """List stored local workflow items."""
    root = project_root.resolve()
    items = _available_work_items(root)
    typer.echo(f"work_items_dir={WORK_ITEMS_DIR}")
    if not items:
        typer.echo("No stored workflow items found.")
        return
    for item in items:
        typer.echo(f"- {item}")


@workflow_app.command("show")
def workflow_show(
    name: str | None = typer.Argument(None, help="Optional stored workflow item name."),
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/current_work.yaml."),
) -> None:
    """Show the current workflow request or one stored workflow item."""
    root = project_root.resolve()
    path = _rooted(WORK_FILE, root) if name is None else _work_item_path(root, name)
    if not path.exists():
        if name is None:
            raise typer.BadParameter(f"missing current workflow file: {WORK_FILE}")
        raise typer.BadParameter(f"unknown workflow item: {_safe_work_item_name(name)}")
    shown_path = WORK_FILE if name is None else WORK_ITEMS_DIR / f"{_safe_work_item_name(name)}.yaml"
    typer.echo(f"workflow_file={shown_path}")
    typer.echo(path.read_text(encoding="utf-8").rstrip())

@workflow_app.command("go")
def workflow_go(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/current_work.yaml and tools/next-step.py."),
) -> None:
    """Request the configured workflow and run one bounded step."""
    root = project_root.resolve()
    state = _read_state(root)
    if state != "IDLE":
        raise typer.BadParameter(f"refusing to start workflow from state: {state}")
    _workflow_request_state(root)
    _set_workflow_request_state(root, "REQUESTED")
    typer.echo(f"Current workflow request file: {WORK_FILE}")
    typer.echo("Workflow request state: REQUESTED")
    typer.echo("Running one bounded workflow step.")
    raise typer.Exit(code=_run_next_step(root))


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


@workflow_app.command("upload-output")
@workflow_app.command("upload")
def workflow_upload(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Alias for upload-output."""
    workflow_upload_output(project_root=project_root)

def workflow_upload_output(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
) -> None:
    """Upload the latest bounded local workflow output evidence for review."""
    root = project_root.resolve()
    state = _read_state(root)
    if state == "UPLOADED":
        raise typer.BadParameter("output evidence is already uploaded; run workflow cleanup after review")
    if state == "CLEANUP":
        raise typer.BadParameter("workflow cleanup is already pending")
    typer.echo("Uploading latest bounded workflow output evidence.")
    raise typer.Exit(code=_run_next_step(root, ["--upload-output"]))


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
