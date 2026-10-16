#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = Path(".agentic/workflow_state")
WORKFLOW_FILE = Path(os.environ.get("AGENTIC_WORKFLOW_FILE", ".agentic/current_work.yaml"))
BRANCH_FILE = Path("tmp/agent-evidence/latest-branch.txt")
EVIDENCE_DIR = Path("tmp/agent-evidence")
REPORT_FILE = Path("docs/reports/CURRENT_WORKFLOW_OUTPUT.md")
TEMP_PREFIX = "temp/workflow-evidence-"
VALID_STATES = {"IDLE", "TEST", "UPLOAD", "CLEANUP", "REQUESTED", "RUNNING", "UPLOADED", "FAILED"}
REQUIRED_VENV_TOOLS = (Path(".venv/bin/ruff"), Path(".venv/bin/agentic-kit"))


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(args))
    return subprocess.run(args, text=True, check=check)


def workflow_python() -> str:
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def ensure_project_environment() -> None:
    venv_python = Path(".venv/bin/python")
    if not venv_python.exists():
        run([sys.executable, "-m", "venv", ".venv"])
    if any(not path.exists() for path in REQUIRED_VENV_TOOLS):
        run([str(venv_python), "-m", "pip", "install", "-e", ".[dev]"])


def read_state() -> str:
    if not STATE_FILE.exists():
        raise SystemExit("Missing .agentic/workflow_state")
    state = STATE_FILE.read_text(encoding="utf-8").strip()
    if state not in VALID_STATES:
        raise SystemExit(f"Invalid workflow state: {state}")
    return state


def write_state(state: str) -> None:
    if state not in VALID_STATES:
        raise SystemExit(f"Invalid workflow state: {state}")
    STATE_FILE.write_text(state + "\n", encoding="utf-8")


def current_branch() -> str:
    result = subprocess.run(["git", "branch", "--show-current"], text=True, check=True, capture_output=True)
    return result.stdout.strip()


def kit_repo_actions() -> ModuleType:
    """Return the Kit's governed git mutation primitives, or stop when the Kit is not importable."""
    try:
        from agentic_project_kit import transfer_repo_actions
    except ImportError as exc:
        raise SystemExit(f"BLOCKED: agentic_project_kit is not importable ({exc}); run through agentic-kit workflow.")
    return transfer_repo_actions


def require_kit_action(result: object, what: str) -> None:
    if getattr(result, "result_status", "") != "PASS":
        detail = (getattr(result, "stderr", "") or getattr(result, "stdout", "") or "").strip()
        raise SystemExit(f"BLOCKED: {what} failed through the Kit primitive: {detail}")


def validated_branch_name(branch: str) -> str:
    from agentic_project_kit.safe_push import validate_branch_name

    try:
        return validate_branch_name(branch)
    except ValueError as exc:
        raise SystemExit(f"BLOCKED: {exc}")


def git_lines(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"BLOCKED: git {' '.join(args)} failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def require_evidence_commit_preconditions() -> None:
    """Fail closed before the evidence commit can carry anything but workflow evidence.

    The evidence branch is pushed to origin, so it must start from a commit that is already
    published and the index must not hold changes staged by someone else.
    """
    staged = git_lines(["diff", "--cached", "--name-only"])
    if staged:
        raise SystemExit("BLOCKED: the index already holds staged changes: " + ", ".join(staged))
    unpublished = git_lines(["rev-list", "HEAD", "--not", "--remotes"])
    if unpublished:
        raise SystemExit(
            f"BLOCKED: HEAD has {len(unpublished)} commit(s) not on any remote; "
            "the evidence branch would publish them."
        )


def latest_evidence() -> Path:
    files = sorted(EVIDENCE_DIR.glob("workflow-output-*.md"))
    if not files:
        raise SystemExit("No workflow evidence file found. Run TEST or REQUESTED state first.")
    return files[-1]


def timestamped_evidence_path() -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return EVIDENCE_DIR / f"workflow-output-{timestamp}.md"


def write_current_report(evidence: Path, purpose: str) -> None:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        "# Current workflow output\n\n"
        f"Date: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Branch: {current_branch()}\n\n"
        "## Purpose\n\n"
        f"{purpose}\n\n"
        "## Evidence file\n\n"
        f"{evidence}\n",
        encoding="utf-8",
    )


def create_evidence_branch(next_state: str) -> str:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = validated_branch_name(TEMP_PREFIX + timestamp)
    evidence = latest_evidence()
    actions = kit_repo_actions()
    from agentic_project_kit.workspace_lock import workspace_mutation_lock

    evidence_paths = [STATE_FILE.as_posix(), REPORT_FILE.as_posix(), evidence.as_posix()]
    with workspace_mutation_lock(Path("."), "workflow_evidence_commit"):
        require_evidence_commit_preconditions()
        run(["git", "switch", "-c", branch])
        run(["git", "add", "--", STATE_FILE.as_posix(), REPORT_FILE.as_posix()])
        run(["git", "add", "-f", "--", evidence.as_posix()])
        unexpected = sorted(set(git_lines(["diff", "--cached", "--name-only"])) - set(evidence_paths))
        if unexpected:
            raise SystemExit("BLOCKED: refusing to commit non-evidence paths: " + ", ".join(unexpected))
        run(["git", "commit", "-m", "Add temporary workflow evidence"])
    require_kit_action(actions.push_current(required_branch=branch), f"push of {branch}")
    BRANCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRANCH_FILE.write_text(branch + "\n", encoding="utf-8")
    write_state(next_state)
    return branch


def step_test() -> None:
    run(["./.venv/bin/python", "tools/workflow_runner.py", "go"])
    state = read_state()
    if state != "UPLOAD":
        raise SystemExit(f"Expected state UPLOAD after TEST step, got {state}")
    print("Next state: UPLOAD")


def step_upload() -> None:
    if current_branch() != "main":
        raise SystemExit("UPLOAD must start from main to keep temporary evidence isolated.")
    branch = create_evidence_branch("CLEANUP")
    print(f"Uploaded temporary workflow evidence branch: {branch}")
    print("Next state: CLEANUP")


def step_cleanup(next_state: str = "IDLE") -> None:
    if not BRANCH_FILE.exists():
        raise SystemExit("Missing tmp/agent-evidence/latest-branch.txt")
    branch = BRANCH_FILE.read_text(encoding="utf-8").strip()
    if not branch.startswith(TEMP_PREFIX):
        raise SystemExit(f"Refusing to clean unsafe branch name: {branch}")
    branch = validated_branch_name(branch)
    actions = kit_repo_actions()
    run(["git", "restore", "--", STATE_FILE.as_posix()], check=False)
    require_kit_action(actions.branch_switch("main", pull=True), "switch to main with fast-forward pull")
    for result in (
        actions.branch_delete(branch, force=True),
        actions.branch_delete(branch, remote=True),
    ):
        if result.result_status != "PASS":
            print(f"Branch cleanup step did not complete: {' '.join(result.command)}: {result.stderr.strip()}")
    for path in EVIDENCE_DIR.glob("workflow-output-*.md"):
        path.unlink()
    BRANCH_FILE.unlink(missing_ok=True)
    write_state(next_state)
    print("Cleaned temporary workflow evidence.")
    print(f"Next state: {next_state}")


def step_requested() -> None:
    if not WORKFLOW_FILE.exists():
        raise SystemExit("Missing .agentic/current_work.yaml")
    control_branch = current_branch()
    write_state("RUNNING")
    evidence = timestamped_evidence_path()
    try:
        run([workflow_python(), "tools/workflow_runner.py", str(WORKFLOW_FILE), str(evidence)])
    except subprocess.CalledProcessError:
        return_to_control_branch(control_branch, check=False)
        write_current_report(evidence, "Declarative workflow failed. Evidence preserved for diagnosis.")
        write_state("FAILED")
        print("Next state: FAILED")
        return
    return_to_control_branch(control_branch)
    set_workflow_request_state("READY")
    write_current_report(evidence, "Declarative workflow completed and evidence was uploaded for handoff.")
    branch = create_evidence_branch("UPLOADED")
    print(f"Uploaded temporary workflow evidence branch: {branch}")
    print("Next state: UPLOADED")


def return_to_control_branch(control_branch: str, check: bool = True) -> None:
    """Return locally to the branch the workflow started on; never creates or publishes refs."""
    if current_branch() == control_branch:
        return
    if not check:
        try:
            from agentic_project_kit.safe_push import validate_branch_name

            control_branch = validate_branch_name(control_branch)
        except (ImportError, ValueError) as exc:
            print(f"Not returning to control branch {control_branch!r}: {exc}")
            return
        run(["git", "switch", "--", control_branch], check=False)
        return
    run(["git", "switch", "--", validated_branch_name(control_branch)])


def step_running() -> None:
    print("Previous workflow is marked RUNNING.")
    print("No new workflow will be started automatically. Inspect local output and set FAILED or recover explicitly.")


def step_failed() -> None:
    print("Previous workflow failed. Evidence is preserved if it could be written.")
    print("No automatic cleanup is performed from FAILED.")


def step_fail_report() -> None:
    state = read_state()
    if state != "FAILED":
        raise SystemExit(f"fail-report requires FAILED state, got {state}")
    write_current_report(latest_evidence(), "Declarative workflow failed. Evidence uploaded for diagnosis without cleanup or retry.")
    branch = create_evidence_branch("UPLOADED")
    print(f"Uploaded failure workflow evidence branch: {branch}")
    print("Next state: UPLOADED")


def step_upload_output() -> None:
    state = read_state()
    if state in {"UPLOADED", "CLEANUP"}:
        raise SystemExit(f"upload-output requires local evidence before upload cleanup, got {state}")
    evidence = latest_evidence()
    write_current_report(evidence, "Bounded local workflow output uploaded for review without pasted terminal output.")
    branch = create_evidence_branch("UPLOADED")
    print(f"Uploaded workflow output evidence branch: {branch}")
    print("Next state: UPLOADED")


def workflow_request_state() -> str:
    if not WORKFLOW_FILE.exists():
        return "MISSING"
    for line in WORKFLOW_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("state:"):
            return stripped.split(":", 1)[1].strip().upper() or "READY"
    return "READY"


def set_workflow_request_state(request_state: str) -> None:
    if not WORKFLOW_FILE.exists():
        raise SystemExit(f"Missing workflow request file: {WORKFLOW_FILE}")
    normalized = request_state.upper()
    if normalized not in {"READY", "REQUESTED"}:
        raise SystemExit(f"Invalid workflow request state: {request_state}")
    lines = WORKFLOW_FILE.read_text(encoding="utf-8").splitlines()
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
    WORKFLOW_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")


def request_workflow() -> None:
    set_workflow_request_state("REQUESTED")
    print(f"Current workflow request file: {WORKFLOW_FILE}")
    print("Workflow request state: REQUESTED")
    print("Next state: IDLE")


def step_idle() -> None:
    request_state = workflow_request_state()
    if request_state != "REQUESTED":
        if request_state == "MISSING":
            print("No workflow action requested.")
        else:
            print(f"Current workflow request file: {WORKFLOW_FILE}")
            print(f"Workflow request state: {request_state}")
            print("No active workflow request.")
        print("Next state: IDLE")
        return
    print(f"Current workflow request file: {WORKFLOW_FILE}")
    print("workflow_state=IDLE + current_work.state=REQUESTED -> REQUESTED")
    write_state("REQUESTED")
    step_requested()


def main() -> int:
    os.chdir(REPO_ROOT)
    if sys.argv[1:] == ["--request"]:
        request_workflow()
        return 0
    if sys.argv[1:] == ["--fail-report"]:
        ensure_project_environment()
        step_fail_report()
        return 0
    if sys.argv[1:] == ["--upload-output"]:
        ensure_project_environment()
        step_upload_output()
        return 0
    if sys.argv[1:]:
        raise SystemExit("Usage: next-step.py [--request|--fail-report|--upload-output]")
    ensure_project_environment()
    state = read_state()
    print(f"workflow_state={state}")
    if state == "IDLE":
        step_idle()
    elif state == "TEST":
        step_test()
    elif state == "UPLOAD":
        step_upload()
    elif state == "CLEANUP":
        step_cleanup()
    elif state == "REQUESTED":
        step_requested()
    elif state == "RUNNING":
        step_running()
    elif state == "UPLOADED":
        step_cleanup()
    elif state == "FAILED":
        step_failed()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
