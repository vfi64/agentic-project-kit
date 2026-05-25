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


def _run_git(args: list[str], *, root: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed


def _git_stdout(args: list[str], *, root: Path) -> str:
    return _run_git(args, root=root).stdout.strip()


def current_branch(root: Path | str = ".") -> str:
    return _git_stdout(["branch", "--show-current"], root=Path(root))


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



@dataclass(frozen=True)
class EvidenceFinalizeResult:
    plan: EvidencePublishPlan
    committed: bool
    pushed: bool
    already_clean: bool
    commit_sha: str
    message: str


def has_staged_changes(root: Path | str = ".") -> bool:
    completed = _run_git(["diff", "--cached", "--quiet"], root=Path(root), check=False)
    return completed.returncode == 1


def commit_and_push_evidence(
    *,
    plan: EvidencePublishPlan,
    root: Path | str = ".",
    push: bool = True,
) -> EvidenceFinalizeResult:
    root_path = Path(root)

    if not has_staged_changes(root_path):
        return EvidenceFinalizeResult(
            plan=plan,
            committed=False,
            pushed=False,
            already_clean=True,
            commit_sha="",
            message="PASS_ALREADY_DONE: no staged evidence changes",
        )

    commit = _run_git(["commit", "-m", plan.commit_message], root=root_path, check=False)
    if commit.returncode != 0:
        combined = (commit.stderr + commit.stdout).strip()
        if "nothing to commit" in combined or "no changes added to commit" in combined:
            return EvidenceFinalizeResult(
                plan=plan,
                committed=False,
                pushed=False,
                already_clean=True,
                commit_sha="",
                message="PASS_ALREADY_DONE: nothing to commit",
            )
        raise RuntimeError(combined)

    sha = _git_stdout(["rev-parse", "HEAD"], root=root_path)

    pushed = False
    if push:
        push_result = _run_git(["push", "-u", "origin", plan.branch], root=root_path, check=False)
        if push_result.returncode != 0:
            raise RuntimeError((push_result.stderr + push_result.stdout).strip())
        pushed = True

    return EvidenceFinalizeResult(
        plan=plan,
        committed=True,
        pushed=pushed,
        already_clean=False,
        commit_sha=sha,
        message="PASS: evidence committed" + (" and pushed" if pushed else ""),
    )


def render_finalize_result(result: EvidenceFinalizeResult) -> str:
    lines = [
        "NEXT_TURN_EVIDENCE_FINALIZE_RESULT",
        f"run_id={result.plan.run_id}",
        f"committed={str(result.committed).lower()}",
        f"pushed={str(result.pushed).lower()}",
        f"already_clean={str(result.already_clean).lower()}",
        f"commit_sha={result.commit_sha}",
        f"message={result.message}",
        f"branch={result.plan.branch}",
        "subresult=PASS",
    ]
    return "\n".join(lines)

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
    lines.append("subresult=PASS")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-evidence")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--local-terminal-log", required=True)
    parser.add_argument("--work-result", required=True, choices=["PASS", "FAIL", "PENDING", "HARD_FAIL", "PASS_ALREADY_DONE", "NOOP"])
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()

    if args.plan_only:
        plan = build_evidence_publish_plan(
            run_id=args.run_id,
            local_terminal_log=args.local_terminal_log,
            work_result=args.work_result,
        )
        print(render_plan(plan))
        return 0

    plan = publish_and_stage_evidence(
        run_id=args.run_id,
        local_terminal_log=args.local_terminal_log,
        work_result=args.work_result,
    )

    if args.commit:
        finalize_result = commit_and_push_evidence(
            plan=plan,
            push=not args.no_push,
        )
        print(render_finalize_result(finalize_result))
    else:
        print(render_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
