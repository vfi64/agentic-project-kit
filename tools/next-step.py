#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

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
    branch = TEMP_PREFIX + timestamp
    evidence = latest_evidence()
    run(["git", "switch", "-c", branch])
    run(["git", "add", ".agentic/workflow_state", "docs/reports/CURRENT_WORKFLOW_OUTPUT.md"])
    run(["git", "add", "-f", str(evidence)])
    run(["git", "commit", "-m", "Add temporary workflow evidence"])
    run(["git", "push", "-u", "origin", branch])
    BRANCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRANCH_FILE.write_text(branch + "\n", encoding="utf-8")
    write_state(next_state)
    return branch


def step_test() -> None:
    run(["./tools/local_workflow_cycle.sh"])
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
    run(["git", "restore", ".agentic/workflow_state"], check=False)
    run(["git", "switch", "main"])
    run(["git", "pull", "--ff-only"])
    run(["git", "branch", "-D", branch], check=False)
    run(["git", "push", "origin", "--delete", branch], check=False)
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
        run(["git", "switch", control_branch], check=False)
        write_current_report(evidence, "Declarative workflow failed. Evidence preserved for diagnosis.")
        write_state("FAILED")
        print("Next state: FAILED")
        return
    run(["git", "switch", control_branch])
    set_workflow_request_state("READY")
    write_current_report(evidence, "Declarative workflow completed and evidence was uploaded for handoff.")
    branch = create_evidence_branch("UPLOADED")
    print(f"Uploaded temporary workflow evidence branch: {branch}")
    print("Next state: UPLOADED")


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
