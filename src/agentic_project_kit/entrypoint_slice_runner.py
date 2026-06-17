from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable, Literal

StepClassification = Literal["PASS", "PENDING", "FAIL"]

FAIL_RE = re.compile(r"### RESULT: (FAIL|NEEDS_HUMAN_REVIEW) ###|STATUS: (FAIL|NEEDS_HUMAN_REVIEW)|RESULT: (FAIL|NEEDS_HUMAN_REVIEW)")
PENDING_RE = re.compile(r"### RESULT: (PENDING|WAIT) ###|STATUS: (PENDING|WAIT)|RESULT: (PENDING|WAIT)")
PASS_RE = re.compile(
    r"### RESULT: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED) ###"
    r"|STATUS: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED)"
    r"|RESULT: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED)"
)


@dataclass(frozen=True)
class CommandStepResult:
    number: int
    command: str
    exit_status: int
    classification: StepClassification
    output: str


def classify_step_output(output: str, exit_status: int) -> StepClassification:
    if FAIL_RE.search(output):
        return "FAIL"
    if PENDING_RE.search(output):
        return "PENDING"
    if PASS_RE.search(output):
        return "PASS"
    return "PASS" if exit_status == 0 else "FAIL"


def load_plan(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"plan file not found: {path}")
    commands: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        commands.append(raw_line)
    return commands


def run_command(repo_root: Path, command: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["sh", "-c", command],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout


def run_steps(repo_root: Path, commands: Iterable[str]) -> tuple[int, list[CommandStepResult]]:
    status = 0
    results: list[CommandStepResult] = []
    for index, command in enumerate(commands, start=1):
        exit_status, output = run_command(repo_root, command)
        classification = classify_step_output(output, exit_status)
        results.append(CommandStepResult(index, command, exit_status, classification, output))
        if classification == "PASS":
            continue
        status = 2 if classification == "PENDING" else 1
        break
    return status, results


def _git(repo_root: Path, args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def render_run(plan_file: Path, results: list[CommandStepResult], final_status: int, branch: str, git_status: str) -> str:
    lines = [
        "",
        "",
        "",
        "--------------------------------------------------------------------------------",
        "--------------------------------------------------------------------------------",
        "--------------------------------------------------------------------------------",
        "",
        "",
        "",
        "NS SLICE RUNNER",
        "",
        "### SAFETY ###",
        "Safety: deterministic sequential runner; advances only after target-state PASS and stops immediately on retryable or failing states.",
        f"plan={plan_file.as_posix()}",
    ]
    for result in results:
        lines.extend(["", f"### STEP {result.number} ###", result.command])
        if result.output:
            lines.append(result.output.rstrip())
        lines.append(f"STEP {result.number} RESULT: {result.classification}")
        if result.classification == "PENDING":
            lines.append("Stopping slice runner at retryable state; no dependent follow-up actions were run.")
        elif result.classification == "FAIL":
            lines.append("Stopping slice runner at first failing step.")
    lines.extend(["", "### FINAL STATE ###", branch])
    if git_status:
        lines.append(git_status)
    if final_status == 0:
        lines.append("\n### RESULT: PASS ###")
    elif final_status == 2:
        lines.append("\n### RESULT: PENDING ###")
    else:
        lines.append("\n### RESULT: FAIL ###")
    return "\n".join(lines)


def run_slice(plan_file: Path, repo_root: Path) -> int:
    try:
        commands = load_plan(plan_file)
    except FileNotFoundError:
        print(f"ERROR: plan file not found: {plan_file}")
        return 1
    status, results = run_steps(repo_root, commands)
    branch_rc, branch = _git(repo_root, ["branch", "--show-current"])
    status_rc, git_status = _git(repo_root, ["status", "--short"])
    final_status = status if branch_rc == 0 and status_rc == 0 else 1
    print(render_run(plan_file, results, final_status, branch, git_status))
    return final_status


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else []
    if not args:
        print("ERROR: missing plan file. Usage: ./ns slice-runner <plan-file>")
        print("Plan format: one shell command per line; blank lines and lines starting with # are ignored.")
        return 1
    return run_slice(Path(args[0]), Path(".").resolve())


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
