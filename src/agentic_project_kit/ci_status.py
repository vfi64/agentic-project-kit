from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
import subprocess
from typing import Any, Literal

from agentic_project_kit.github_check_policy import (
    is_failed_check_conclusion,
    is_optional_skipped_check,
    is_successful_check_conclusion,
    normalize_check_conclusion,
    normalize_check_status,
)

Decision = Literal["green", "red", "pending", "no-runs", "unknown"]
ResultStatus = Literal["PASS", "PENDING", "BLOCKED"]
GhJsonRunner = Callable[[list[str]], Any]


@dataclass(frozen=True)
class CiRunSummary:
    name: str
    workflow_name: str
    database_id: str
    status: str
    conclusion: str
    url: str
    head_sha: str
    head_branch: str
    event: str


@dataclass(frozen=True)
class CiStatusResult:
    schema_version: int
    kind: str
    result_status: ResultStatus
    decision: Decision
    commit: str
    branch: str
    successful_checks: tuple[str, ...]
    pending_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    unknown_checks: tuple[str, ...]
    skipped_optional_checks: tuple[str, ...]
    runs: tuple[CiRunSummary, ...]
    command: tuple[str, ...]
    next_action: str


def _default_run_gh_json(args: list[str]) -> Any:
    completed = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"gh exited {completed.returncode}")
    return json.loads(completed.stdout)


def _run_name(run: dict[str, Any]) -> str:
    return str(run.get("name") or run.get("workflowName") or "workflow")


def _summary(run: dict[str, Any]) -> CiRunSummary:
    return CiRunSummary(
        name=_run_name(run),
        workflow_name=str(run.get("workflowName") or ""),
        database_id=str(run.get("databaseId") or ""),
        status=normalize_check_status(run.get("status")),
        conclusion=normalize_check_conclusion(run.get("conclusion")),
        url=str(run.get("url") or ""),
        head_sha=str(run.get("headSha") or ""),
        head_branch=str(run.get("headBranch") or ""),
        event=str(run.get("event") or ""),
    )


def _query_args(*, commit: str, branch: str, limit: int) -> list[str]:
    args = [
        "run",
        "list",
        "--limit",
        str(limit),
        "--json",
        "conclusion,databaseId,event,headBranch,headSha,name,status,url,workflowName",
    ]
    if branch:
        args.extend(["--branch", branch])
    if commit:
        args.extend(["--commit", commit])
    return args


def _classify_runs(runs: list[dict[str, Any]]) -> tuple[Decision, dict[str, tuple[str, ...]]]:
    successful: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []
    skipped_optional: list[str] = []

    if not runs:
        return "no-runs", {
            "successful": (),
            "pending": (),
            "failed": (),
            "unknown": (),
            "skipped_optional": (),
        }

    for run in runs:
        name = _run_name(run)
        status = normalize_check_status(run.get("status"))
        conclusion = normalize_check_conclusion(run.get("conclusion"))
        if status != "COMPLETED":
            pending.append(name)
        elif is_successful_check_conclusion(conclusion):
            successful.append(name)
        elif is_optional_skipped_check(name, status=status, conclusion=conclusion):
            skipped_optional.append(name)
        elif is_failed_check_conclusion(conclusion):
            failed.append(name)
        else:
            unknown.append(name)

    if failed:
        decision: Decision = "red"
    elif pending:
        decision = "pending"
    elif unknown:
        decision = "unknown"
    elif successful:
        decision = "green"
    else:
        decision = "no-runs"
    return decision, {
        "successful": tuple(successful),
        "pending": tuple(pending),
        "failed": tuple(failed),
        "unknown": tuple(unknown),
        "skipped_optional": tuple(skipped_optional),
    }


def result_status_for_decision(decision: Decision) -> ResultStatus:
    if decision == "green":
        return "PASS"
    if decision == "pending":
        return "PENDING"
    return "BLOCKED"


def read_ci_status(
    *,
    commit: str = "",
    branch: str = "",
    limit: int = 20,
    run_gh_json: GhJsonRunner = _default_run_gh_json,
) -> CiStatusResult:
    commit = commit.strip()
    branch = branch.strip()
    if not commit and not branch:
        raise ValueError("provide --commit, --branch, or both")
    args = _query_args(commit=commit, branch=branch, limit=limit)
    payload = run_gh_json(args)
    if not isinstance(payload, list):
        raise RuntimeError("gh run list did not return a JSON array")
    runs = [item for item in payload if isinstance(item, dict)]
    decision, buckets = _classify_runs(runs)
    next_action = "none" if decision == "green" else "inspect failed or pending GitHub Actions run details"
    return CiStatusResult(
        schema_version=1,
        kind="ci_status",
        result_status=result_status_for_decision(decision),
        decision=decision,
        commit=commit,
        branch=branch,
        successful_checks=buckets["successful"],
        pending_checks=buckets["pending"],
        failed_checks=buckets["failed"],
        unknown_checks=buckets["unknown"],
        skipped_optional_checks=buckets["skipped_optional"],
        runs=tuple(_summary(run) for run in runs),
        command=tuple(["gh", *args]),
        next_action=next_action,
    )


def result_to_dict(result: CiStatusResult) -> dict[str, Any]:
    return asdict(result)


def render_ci_status(result: CiStatusResult) -> str:
    lines = [
        "CI_STATUS",
        f"result_status={result.result_status}",
        f"decision={result.decision}",
        f"commit={result.commit or '(any)'}",
        f"branch={result.branch or '(any)'}",
        "successful_checks:",
        *[f"- {item}" for item in result.successful_checks],
        "pending_checks:",
        *[f"- {item}" for item in result.pending_checks],
        "failed_checks:",
        *[f"- {item}" for item in result.failed_checks],
        "unknown_checks:",
        *[f"- {item}" for item in result.unknown_checks],
        "skipped_optional_checks:",
        *[f"- {item}" for item in result.skipped_optional_checks],
        f"next_action={result.next_action}",
    ]
    return "\n".join(lines) + "\n"
