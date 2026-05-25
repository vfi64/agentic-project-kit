from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.next_turn_result import publish_local_evidence, render_summary


@dataclass(frozen=True)
class EvidencePublishPlan:
    run_id: str
    local_terminal_log: str
    work_result: str
    files_to_stage: tuple[str, ...]
    commit_message: str
    branch: str
    push_command: str


def _run_git(args: list[str], *, root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def current_branch(root: Path | str = ".") -> str:
    return _run_git(["branch", "--show-current"], root=Path(root))


def build_evidence_publish_plan(
    *,
    run_id: str,
    local_terminal_log: str,
    work_result: str,
    root: Path | str = ".",
) -> EvidencePublishPlan:
    root_path = Path(root)
    branch = current_branch(root_path)
    files = (
        f"docs/reports/terminal/{run_id}.log",
        f"docs/reports/command_runs/{run_id}.json",
        "docs/reports/command_runs/next-turn-latest.json",
    )
    return EvidencePublishPlan(
        run_id=run_id,
        local_terminal_log=local_terminal_log,
        work_result=work_result,
        files_to_stage=files,
        commit_message=f"Record {run_id} evidence",
        branch=branch,
        push_command=f"git push -u origin {branch}",
    )


def publish_and_stage_evidence(
    *,
    run_id: str,
    local_terminal_log: str,
    work_result: str,
    root: Path | str = ".",
) -> EvidencePublishPlan:
    root_path = Path(root)
    result = publish_local_evidence(
        run_id=run_id,
        local_terminal_log=local_terminal_log,
        work_result=work_result,  # type: ignore[arg-type]
        root=root_path,
    )
    plan = build_evidence_publish_plan(
        run_id=run_id,
        local_terminal_log=local_terminal_log,
        work_result=work_result,
        root=root_path,
    )
    _run_git(["add", *plan.files_to_stage], root=root_path)
    print(render_summary(result))
    return plan


def render_plan(plan: EvidencePublishPlan) -> str:
    lines = [
        "NEXT_TURN_EVIDENCE_PUBLISH_PLAN",
        f"run_id={plan.run_id}",
        f"local_terminal_log={plan.local_terminal_log}",
        f"work_result={plan.work_result}",
        f"branch={plan.branch}",
        f"commit_message={plan.commit_message}",
        f"push_command={plan.push_command}",
        "files_to_stage:",
    ]
    lines.extend(f"- {item}" for item in plan.files_to_stage)
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-evidence")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--local-terminal-log", required=True)
    parser.add_argument("--work-result", required=True, choices=["PASS", "FAIL", "PENDING", "HARD_FAIL", "PASS_ALREADY_DONE", "NOOP"])
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()

    if args.plan_only:
        plan = build_evidence_publish_plan(
            run_id=args.run_id,
            local_terminal_log=args.local_terminal_log,
            work_result=args.work_result,
        )
    else:
        plan = publish_and_stage_evidence(
            run_id=args.run_id,
            local_terminal_log=args.local_terminal_log,
            work_result=args.work_result,
        )

    print(render_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
