#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

STATE_FILE = Path(".agentic/workflow_state")
WORKFLOW_FILE = Path(".agentic/current_work.yaml")
BRANCH_FILE = Path("tmp/agent-evidence/latest-branch.txt")
EVIDENCE_DIR = Path("tmp/agent-evidence")
REPORT_FILE = Path("docs/reports/CURRENT_WORKFLOW_OUTPUT.md")
TEMP_PREFIX = "temp/workflow-evidence-"
VALID_STATES = {"IDLE", "TEST", "UPLOAD", "CLEANUP", "REQUESTED", "RUNNING", "UPLOADED", "FAILED"}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(args))
    return subprocess.run(args, text=True, check=check)


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
        run([sys.executable, "tools/workflow_runner.py", str(WORKFLOW_FILE), str(evidence)])
    except subprocess.CalledProcessError:
        run(["git", "switch", control_branch], check=False)
        write_current_report(evidence, "Declarative workflow failed. Evidence preserved for diagnosis.")
        write_state("FAILED")
        print("Next state: FAILED")
        return
    run(["git", "switch", control_branch])
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


def step_idle() -> None:
    if not WORKFLOW_FILE.exists():
        print("No workflow action requested.")
        print("Chat reply after completion: done or d")
        return
    print(f"Current workflow request file: {WORKFLOW_FILE}")
    print("workflow_state=IDLE -> REQUESTED")
    write_state("REQUESTED")
    step_requested()


def main() -> int:
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
