#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

STATE_FILE = Path(".agentic/workflow_state")
BRANCH_FILE = Path("tmp/agent-evidence/latest-branch.txt")
EVIDENCE_DIR = Path("tmp/agent-evidence")
TEMP_PREFIX = "temp/workflow-evidence-"
VALID_STATES = {"IDLE", "TEST", "UPLOAD", "CLEANUP"}


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
        raise SystemExit("No workflow evidence file found. Run TEST state first.")
    return files[-1]


def step_test() -> None:
    run(["./tools/local_workflow_cycle.sh"])
    state = read_state()
    if state != "UPLOAD":
        raise SystemExit(f"Expected state UPLOAD after TEST step, got {state}")
    print("Next state: UPLOAD")


def step_upload() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = TEMP_PREFIX + timestamp
    evidence = latest_evidence()
    if current_branch() != "main":
        raise SystemExit("UPLOAD must start from main to keep temporary evidence isolated.")
    run(["git", "switch", "-c", branch])
    run(["git", "add", ".agentic/workflow_state", "docs/reports/CURRENT_WORKFLOW_OUTPUT.md"])
    run(["git", "add", "-f", str(evidence)])
    run(["git", "commit", "-m", "Add temporary workflow evidence"])
    run(["git", "push", "-u", "origin", branch])
    BRANCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRANCH_FILE.write_text(branch + "\n", encoding="utf-8")
    write_state("CLEANUP")
    print(f"Uploaded temporary workflow evidence branch: {branch}")
    print("Next state: CLEANUP")


def step_cleanup() -> None:
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
    write_state("IDLE")
    print("Cleaned temporary workflow evidence.")
    print("Next state: IDLE")


def main() -> int:
    state = read_state()
    print(f"workflow_state={state}")
    if state == "IDLE":
        print("No workflow action requested.")
    elif state == "TEST":
        step_test()
    elif state == "UPLOAD":
        step_upload()
    elif state == "CLEANUP":
        step_cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
