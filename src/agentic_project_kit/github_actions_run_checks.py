from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

RunJsonFetcher = Callable[[list[str]], Any]


def run_id_from_url(url: str) -> str:
    marker = "/actions/runs/"
    if marker not in url:
        return ""
    tail = url.split(marker, 1)[1]
    return tail.split("/", 1)[0]


def parse_github_datetime(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def stale_zero_job_run(run: dict[str, Any], *, now: datetime, stale_after_seconds: int) -> bool:
    status = str(run.get("status") or "").lower()
    conclusion = str(run.get("conclusion") or "")
    if status not in {"queued", "in_progress"} or conclusion:
        return False
    try:
        job_count = int(run.get("jobCount"))
    except (TypeError, ValueError):
        return False
    if job_count != 0:
        return False
    updated_at = parse_github_datetime(run.get("updatedAt") or run.get("updated_at") or run.get("createdAt"))
    if updated_at is None:
        return False
    return (now - updated_at).total_seconds() >= stale_after_seconds


def fetch_run_job_count(run_id: str, *, run_gh_json: RunJsonFetcher) -> int | None:
    try:
        payload = run_gh_json(["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs"])
    except RuntimeError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return int(payload.get("total_count"))
    except (TypeError, ValueError):
        return None


def fetch_action_run_checks(
    *,
    commit_sha: str,
    branch: str,
    run_gh_json: RunJsonFetcher,
    stale_after_seconds: int = 600,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    runs = run_gh_json(
        [
            "run",
            "list",
            "--branch",
            branch,
            "--commit",
            commit_sha,
            "--limit",
            "20",
            "--json",
            "createdAt,databaseId,status,conclusion,name,workflowName,url,updatedAt",
        ]
    )
    if not isinstance(runs, list):
        raise RuntimeError("gh run list did not return a JSON array")
    timestamp = now or datetime.now(timezone.utc)
    checks: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_id = str(run.get("databaseId") or run_id_from_url(str(run.get("url") or "")))
        job_count = fetch_run_job_count(run_id, run_gh_json=run_gh_json) if run_id else None
        enriched_run = dict(run)
        if job_count is not None:
            enriched_run["jobCount"] = job_count
        checks.append(
            {
                "name": run.get("name") or run.get("workflowName") or "workflow",
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "detailsUrl": run.get("url") or "",
                "jobCount": job_count,
                "staleRemoteEvidence": stale_zero_job_run(
                    enriched_run,
                    now=timestamp,
                    stale_after_seconds=stale_after_seconds,
                ),
            }
        )
    return checks
