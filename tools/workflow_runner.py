from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ALLOWED_SIMPLE_STEPS = {
    "git_fetch",
    "git_switch_main",
    "git_switch_work_branch",
    "git_pull_ff_only",
    "ruff_check",
    "check_docs",
    "doctor",
}


class WorkflowFailure(RuntimeError):
    pass


class WorkflowTimeout(WorkflowFailure):
    pass


def load_workflow(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorkflowFailure(f"Missing workflow request: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise WorkflowFailure("Workflow request must be a YAML mapping")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise WorkflowFailure("Workflow request must contain a non-empty steps list")
    return data


def _step_command(step: Any, workflow: dict[str, Any]) -> list[str]:
    if isinstance(step, str):
        if step not in ALLOWED_SIMPLE_STEPS:
            raise WorkflowFailure(f"Unsupported workflow step: {step}")
        if step == "git_fetch":
            return ["git", "fetch", "origin"]
        if step == "git_switch_main":
            return ["git", "switch", str(workflow.get("base_branch", "main"))]
        if step == "git_switch_work_branch":
            branch = workflow.get("work_branch")
            if not isinstance(branch, str) or not branch:
                raise WorkflowFailure("git_switch_work_branch requires work_branch")
            return ["git", "switch", branch]
        if step == "git_pull_ff_only":
            return ["git", "pull", "--ff-only"]
        if step == "ruff_check":
            return ["ruff", "check", "."]
        if step == "check_docs":
            return ["agentic-kit", "check-docs"]
        if step == "doctor":
            return ["agentic-kit", "doctor"]
    if isinstance(step, dict) and len(step) == 1:
        name, config = next(iter(step.items()))
        if name == "gh_pr_checks":
            number = _required_int(config, "number")
            return ["gh", "pr", "checks", str(number)]
        if name == "gh_pr_view":
            number = _required_int(config, "number")
            fields = _required_str_list(config, "fields")
            return ["gh", "pr", "view", str(number), "--json", ",".join(fields)]
    raise WorkflowFailure(f"Unsupported workflow step shape: {step!r}")


def _required_int(config: Any, key: str) -> int:
    if not isinstance(config, dict) or not isinstance(config.get(key), int):
        raise WorkflowFailure(f"Step requires integer field: {key}")
    return int(config[key])


def _required_str_list(config: Any, key: str) -> list[str]:
    value = config.get(key) if isinstance(config, dict) else None
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise WorkflowFailure(f"Step requires non-empty string list field: {key}")
    return list(value)


def run_workflow(workflow_path: Path, output_path: Path) -> int:
    workflow = load_workflow(workflow_path)
    timeout_seconds = int(workflow.get("timeout_seconds", 600))
    deadline = time.monotonic() + timeout_seconds
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        out.write("# Declarative workflow output\n\n")
        out.write(f"Workflow: {workflow.get('name', 'unnamed')}\n\n")
        for step in workflow["steps"]:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                out.write("\nTIMEOUT: workflow deadline reached before next step\n")
                raise WorkflowTimeout("workflow deadline reached")
            cmd = _step_command(step, workflow)
            out.write("\n## Step\n\n")
            out.write("```text\n")
            out.write("+ " + " ".join(cmd) + "\n")
            out.flush()
            try:
                completed = subprocess.run(
                    cmd,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=remaining,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                partial = exc.stdout or ""
                if isinstance(partial, bytes):
                    partial = partial.decode("utf-8", errors="replace")
                out.write(partial)
                out.write("\nTIMEOUT\n```\n")
                raise WorkflowTimeout("workflow command timed out") from exc
            out.write(completed.stdout or "")
            out.write(f"\nexit_code={completed.returncode}\n")
            out.write("```\n")
            out.flush()
            if completed.returncode != 0:
                raise WorkflowFailure(f"workflow step failed: {' '.join(cmd)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: workflow_runner.py WORKFLOW_YAML OUTPUT_MD")
    try:
        raise SystemExit(run_workflow(Path(sys.argv[1]), Path(sys.argv[2])))
    except WorkflowFailure as exc:
        print(f"WORKFLOW_FAILED: {exc}")
        raise SystemExit(1) from exc
