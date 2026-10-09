"""Signed, fail-closed reruns of CI that never executed test steps."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Callable

from agentic_project_kit.github_check_policy import is_failed_check_conclusion
from agentic_project_kit.github_ci_failure import classify_failed_job
from agentic_project_kit.repo_identity import github_cli_env_for_origin
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_lock import acquire_workspace_lock

Api = Callable[[str, str], object]


def signature(plan: dict) -> str:
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]


def _pages(api: Api, path: str, key: str) -> list[dict]:
    pages = api(path, "PAGES")
    if not isinstance(pages, list) or not pages:
        raise ValueError("GitHub pagination returned no pages")
    items = []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get(key), list):
            raise ValueError("GitHub pagination returned invalid evidence")
        items.extend(page[key])
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("GitHub evidence contains invalid entries")
    return items


def collect_plan(pr: int, api: Api) -> dict:
    info = api(f"repos/{{owner}}/{{repo}}/pulls/{pr}", "GET")
    if not isinstance(info, dict) or info.get("state") != "open":
        raise ValueError("PR is not open or its identity is unavailable")
    repo = info["base"]["repo"]["full_name"]
    head = info["head"]["sha"]
    if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not isinstance(head, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        raise ValueError("invalid repository or PR head identity")
    runs = _pages(api, f"repos/{repo}/actions/runs?head_sha={head}&per_page=100", "workflow_runs")
    latest = {}
    for run in runs:
        if run.get("head_sha") != head or not run.get("workflow_id") or not run.get("id"):
            raise ValueError("workflow run identity does not match the PR head")
        key = (run["workflow_id"], run.get("event"))
        if key not in latest or int(run["id"]) > int(latest[key]["id"]):
            latest[key] = run
    candidates, blockers = [], []
    for run in sorted(latest.values(), key=lambda item: int(item["id"])):
        if run.get("status") != "completed":
            blockers.append(f"run {run['id']} is still pending")
            continue
        if not is_failed_check_conclusion(str(run.get("conclusion", "")).upper()):
            if run.get("conclusion") not in {"success", "neutral", "skipped"}:
                blockers.append(f"run {run['id']} has an unknown conclusion")
            continue
        attempt = run.get("run_attempt")
        if not isinstance(attempt, int) or attempt < 1:
            raise ValueError("workflow attempt is unavailable")
        jobs = _pages(api, f"repos/{repo}/actions/runs/{run['id']}/attempts/{attempt}/jobs?per_page=100", "jobs")
        failed = []
        for job in jobs:
            if job.get("status") != "completed":
                blockers.append(f"job {job.get('id')} is still pending")
            if is_failed_check_conclusion(str(job.get("conclusion", "")).upper()):
                state, reason = classify_failed_job(job)
                failed.append({"id": job.get("id"), "name": job.get("name"), "ci_state": state,
                               "reason": reason, "started_at": job.get("started_at"),
                               "completed_at": job.get("completed_at"), "conclusion": job.get("conclusion")})
                if state != "NOT_RUN":
                    blockers.append(f"job {job.get('id')}: {reason}")
        # A completed failed run with no jobs is observable evidence that no job ran.
        if jobs and not failed:
            blockers.append(f"run {run['id']} failed without identifiable failed jobs")
        candidates.append({"run_id": run["id"], "attempt": attempt, "conclusion": run["conclusion"],
                           "failed_jobs": failed, "zero_jobs": not jobs})
    if not candidates:
        blockers.append("no failed Actions run on the current PR head")
    return {"policy": "AGP_CI_NOT_STARTED_V1", "repository": repo, "pr": pr, "head_sha": head,
            "action": "rerun-failed-jobs", "runs": candidates, "blockers": blockers}


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".writing")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def rerun_checks(root: Path, pr: int, *, execute: bool = False, expected_signature: str = "",
                 api: Api | None = None) -> dict:
    tmp = load_workspace(root, suppress_legacy_profile_warning=True).tmp()
    evidence = tmp / f"pr-{pr}-rerun-checks.json"
    log = tmp / f"pr-{pr}-rerun-checks.jsonl"
    result = {"result_status": "BLOCKED", "pr_number": pr, "evidence_path": str(evidence),
              "log_path": str(log), "next_action": "Inspect CI evidence before requesting a rerun."}
    def gh_api(path: str, method: str) -> object:
        argv = ["gh", "api", path]
        argv += ["--paginate", "--slurp"] if method == "PAGES" else ["--method", method]
        started = time.monotonic()
        try:
            completed = subprocess.run(argv, cwd=root, env=github_cli_env_for_origin(root), text=True,
                                       capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            completed = subprocess.CompletedProcess(argv, 124, "", "GitHub API request timed out after 60 seconds")
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as stream:
            stream.write(json.dumps({"argv": argv, "returncode": completed.returncode,
                                     "stdout": completed.stdout, "stderr": completed.stderr, "duration_seconds": time.monotonic() - started}) + "\n")
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "GitHub API query failed")
        return json.loads(completed.stdout) if completed.stdout.strip() else None
    query = api or gh_api
    try:
        with acquire_workspace_lock(root, "pr rerun-checks"):
            plan = collect_plan(pr, query)
            sig = signature(plan)
            result.update(plan=plan, approval_signature=sig,
                          ci_state="FAILED" if plan["blockers"] else "NOT_RUN")
            if plan["blockers"]:
                return result
            result["next_action"] = f"agentic-kit pr rerun-checks --pr {pr} --execute --expected-signature {sig} --json"
            if not execute:
                result["result_status"] = "AWAITING_APPROVAL"
                return result
            if expected_signature != sig:
                result["blocker"] = "approval signature is stale or incorrect"
                return result
            receipt = tmp / f"pr-{pr}-rerun-{sig}.json"
            if receipt.exists():
                result["blocker"] = "rerun already attempted; inspect the receipt and fresh CI before retrying"
                return result
            # Fresh evidence for all runs before any mutation. Never rerun an old attempt or head.
            if collect_plan(pr, query) != plan:
                result["blocker"] = "PR head or workflow attempt changed before execution"
                return result
            attempts = [tmp / f"ci-rerun-{plan['repository'].replace('/', '_')}-{run['run_id']}-{run['attempt']}.json"
                        for run in plan["runs"]]
            if any(path.exists() for path in attempts):
                result["blocker"] = "this workflow attempt already has a rerun intent receipt; inspect it before retrying"
                return result
            record = {"plan": plan, "approval_signature": sig, "attempted_run_ids": [], "rerun_run_ids": []}
            _write(receipt, record)
            result["receipt_path"] = str(receipt)
            for run, attempt_receipt in zip(plan["runs"], attempts, strict=True):
                _write(attempt_receipt, {"approval_signature": sig, "run": run, "status": "REQUEST_INTENT"})
                run_id = run["run_id"]
                record["attempted_run_ids"].append(run_id)
                _write(receipt, record)  # Persist intent even if the response is lost.
                query(f"repos/{plan['repository']}/actions/runs/{run_id}/rerun-failed-jobs", "POST")
                record["rerun_run_ids"].append(run_id)
                _write(receipt, record)
            result.update(result_status="PASS", ci_state="PENDING", rerun_run_ids=record["rerun_run_ids"],
                          next_action=f"agentic-kit pr wait-ci {pr} --expected-head-sha {plan['head_sha']}")
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as exc:
        result["blocker"] = str(exc)
    finally:
        _write(evidence, result)
    return result
