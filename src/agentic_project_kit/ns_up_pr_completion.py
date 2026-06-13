from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


def run_command(repo_root: Path, args: list[str], allow_failure: bool = False) -> CommandResult:
    completed = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout.strip()
    if output:
        print(output)
    if completed.returncode != 0 and not allow_failure:
        return CommandResult(completed.returncode, output)
    return CommandResult(completed.returncode, output)


def local_python(repo_root: Path) -> str:
    candidate = repo_root / ".venv" / "bin" / "python"
    return str(candidate) if candidate.exists() else "python3"


def local_agentic_kit(repo_root: Path) -> str:
    candidate = repo_root / ".venv" / "bin" / "agentic-kit"
    return str(candidate) if candidate.exists() else "agentic-kit"


def print_header() -> None:
    print("\n\n\n")
    print("--------------------------------------------------------------------------------")
    print("-------------------------------------------------------------------------------")
    print("--------------------------------------------------------------------------------")
    print("\n\n")
    print("NS UP PR COMPLETION CYCLE\n")
    print("\n### SAFETY ###")
    print("Safety: bounded PR completion cycle; waits for checks, squash-merges the current PR only, updates main only after a successful merge, and runs local gates.")


def run_ns_up(repo_root: Path) -> int:
    status = 0
    merged = False
    print_header()

    print("\n### BRANCH / STATUS ###")
    branch_result = run_command(repo_root, ["git", "branch", "--show-current"])
    branch = branch_result.output.splitlines()[-1] if branch_result.output else ""
    print(f"branch={branch}")
    if run_command(repo_root, ["git", "status", "--short"]).returncode != 0:
        status = 1
    if branch == "main":
        print("ERROR: PR completion must run from a PR branch, not main.")
        status = 1

    porcelain = run_command(repo_root, ["git", "status", "--porcelain"], allow_failure=True)
    if porcelain.output:
        print("ERROR: working tree is dirty. Commit or restore changes before PR completion.")
        print("Hint: run ./ns clean-evidence if the dirtiness is only workflow evidence under tmp/agent-evidence or docs/reports/CURRENT_WORKFLOW_OUTPUT.md.")
        print("Then rerun the bounded PR-completion command after reviewing git status --short.")
        status = 1

    print("\n### NO-OP BRANCH CHECK ###")
    if branch and branch != "main":
        base_diff = run_command(repo_root, ["git", "rev-list", "--count", f"main..{branch}"], allow_failure=True)
        ahead = base_diff.output if base_diff.returncode == 0 and base_diff.output else "unknown"
        print(f"commits_ahead_of_main={ahead}")
        if ahead == "0":
            print("Branch has no commits ahead of main; treating as idempotent no-op completion.")
            if run_command(repo_root, ["git", "switch", "main"]).returncode != 0:
                status = 1
            if run_command(repo_root, ["git", "pull", "--ff-only", "origin", "main"]).returncode != 0:
                status = 1
            print("\n### VERIFY MAIN ###")
            if run_command(repo_root, ["./ns", "dev"]).returncode != 0:
                status = 1
            py = local_python(repo_root)
            if run_command(repo_root, [py, "-m", "agentic_project_kit.cli", "pr-hygiene"]).returncode != 0:
                status = 1
            print_final_state(repo_root)
            print("\n### RESULT: PASS ###" if status == 0 else "\n### RESULT: FAIL ###")
            return status

    print("\n### IDENTIFY CURRENT PR ###")
    pr_number = ""
    if status == 0:
        pr = run_command(repo_root, ["gh", "pr", "view", "--json", "number", "--jq", ".number"])
        if pr.returncode == 0 and pr.output:
            pr_number = pr.output.splitlines()[-1]
            print(f"PR_NUMBER={pr_number}")
        else:
            print("ERROR: no current PR found for this branch.")
            status = 1

    if status == 0:
        print("\n### PR VIEW ###")
        if run_command(repo_root, ["gh", "pr", "view", pr_number, "--json", "number,title,state,mergeable,headRefName,baseRefName,statusCheckRollup"]).returncode != 0:
            status = 1
        pr_state = run_command(repo_root, ["gh", "pr", "view", pr_number, "--json", "state", "--jq", ".state"])
        mergeable = run_command(repo_root, ["gh", "pr", "view", pr_number, "--json", "mergeable", "--jq", ".mergeable"])
        state_value = pr_state.output.splitlines()[-1] if pr_state.output else ""
        mergeable_value = mergeable.output.splitlines()[-1] if mergeable.output else ""
        print(f"state={state_value}")
        print(f"mergeable={mergeable_value}")
        if state_value == "MERGED":
            print("PR is already merged; treating this as an idempotent completion state.")
            merged = True
        elif mergeable_value != "MERGEABLE":
            print("ERROR: PR is not mergeable. Resolve conflicts or wait for GitHub to compute mergeability before PR completion.")
            status = 1

    if status == 0:
        print("\n### PR CHECKS SNAPSHOT ###")
        run_command(repo_root, ["gh", "pr", "checks", pr_number], allow_failure=True)

    if status == 0 and not merged:
        print("\n### WAIT FOR GREEN CHECKS AND MERGE ###")
        head = run_command(repo_root, ["gh", "pr", "view", pr_number, "--json", "headRefOid", "--jq", ".headRefOid"])
        expected_head_sha = head.output.splitlines()[-1] if head.returncode == 0 and head.output else ""
        if not expected_head_sha:
            print("ERROR: could not resolve PR head SHA before guarded merge.")
            status = 1
        else:
            kit = local_agentic_kit(repo_root)
            waited = run_command(
                repo_root,
                [
                    kit,
                    "pr",
                    "wait-ci",
                    pr_number,
                    "--expected-head-sha",
                    expected_head_sha,
                    "--timeout-seconds",
                    "300",
                    "--interval-seconds",
                    "10",
                ],
            )
            if waited.returncode == 0:
                merged_result = run_command(
                    repo_root,
                    [
                        kit,
                        "pr",
                        "merge-if-green",
                        pr_number,
                        "--expected-head-sha",
                        expected_head_sha,
                        "--main-branch",
                        "main",
                        "--merge-method",
                        "squash",
                    ],
                )
                if merged_result.returncode == 0:
                    merged = True
                else:
                    status = 1
            else:
                status = 1

    if merged:
        print("\n### UPDATE MAIN ###")
        if run_command(repo_root, ["git", "switch", "main"]).returncode != 0:
            status = 1
        if run_command(repo_root, ["git", "pull", "--ff-only", "origin", "main"]).returncode != 0:
            status = 1
        print("\n### VERIFY MAIN ###")
        if run_command(repo_root, ["./ns", "dev"]).returncode != 0:
            status = 1
        py = local_python(repo_root)
        if run_command(repo_root, [py, "-m", "agentic_project_kit.cli", "pr-hygiene"]).returncode != 0:
            status = 1
    else:
        print("\n### UPDATE MAIN SKIPPED ###")
        print("Main update skipped because PR merge did not complete successfully.")

    print_final_state(repo_root)
    print("\n### RESULT: PASS ###" if status == 0 else "\n### RESULT: FAIL ###")
    return status


def print_final_state(repo_root: Path) -> None:
    print("\n### FINAL STATE ###")
    run_command(repo_root, ["git", "branch", "--show-current"], allow_failure=True)
    run_command(repo_root, ["git", "log", "--oneline", "-8"], allow_failure=True)
    run_command(repo_root, ["git", "status", "--short"], allow_failure=True)


def main() -> int:
    return run_ns_up(Path(".").resolve())


if __name__ == "__main__":
    raise SystemExit(main())
