from __future__ import annotations

import subprocess
import sys

def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=capture, check=False)

def emit_result(status: int) -> int:
    if status == 0:
        print("\n### RESULT: PASS ###")
    else:
        print("\n### RESULT: FAIL ###")
    return status

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    title = args[0] if len(args) >= 1 else ""
    body = args[1] if len(args) >= 2 else ""
    base = args[2] if len(args) >= 3 else "main"
    print("\n\n\n" + "-" * 80)
    print("-" * 79)
    print("-" * 80)
    print("\n\n\nNS PR CREATE OR SKIP\n")
    if not title:
        print("ERROR: missing title argument.")
        print("Usage: python -m agentic_project_kit.pr_create_or_skip TITLE BODY [BASE]")
        return emit_result(1)
    status = 0
    branch_result = run(["git", "branch", "--show-current"], capture=True)
    if branch_result.returncode != 0:
        status = 1
    branch = branch_result.stdout.strip()
    print("\n### BRANCH / STATUS ###")
    print(f"branch={branch}")
    if run(["git", "status", "--short"]).returncode != 0:
        status = 1
    if branch == base:
        print(f"No PR needed: current branch is base branch {base}.")
        return emit_result(0)
    print("\n### CHECK BRANCH DELTA ###")
    if run(["git", "fetch", "origin", base]).returncode != 0:
        status = 1
    delta_result = run(["git", "rev-list", "--count", f"origin/{base}..HEAD"], capture=True)
    if delta_result.returncode != 0:
        status = 1
    delta = delta_result.stdout.strip() if delta_result.stdout.strip() else "0"
    print(f"commits_ahead_of_{base}={delta}")
    if status == 0 and delta == "0":
        print(f"No PR needed: branch has no commits ahead of origin/{base}.")
        print("This is an idempotent already-completed state, not a failure.")
        return emit_result(0)
    print("\n### EXISTING PR CHECK ###")
    existing = run(["gh", "pr", "view", "--json", "number,title,state,url"])
    if existing.returncode == 0:
        print("Existing PR found for current branch.")
    else:
        print("\n### CREATE PR ###")
        if run(["gh", "pr", "create", "--base", base, "--title", title, "--body", body]).returncode != 0:
            status = 1
    print("\n### PR STATUS ###")
    if run(["gh", "pr", "status"]).returncode != 0:
        status = 1
    print("\n### FINAL STATE ###")
    for cmd in (["git", "branch", "--show-current"], ["git", "log", "--oneline", "-6"], ["git", "status", "--short"]):
        if run(cmd).returncode != 0:
            status = 1
    return emit_result(status)

if __name__ == "__main__":
    raise SystemExit(main())
