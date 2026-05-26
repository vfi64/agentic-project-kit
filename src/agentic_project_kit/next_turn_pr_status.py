from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict
import json
import re
import subprocess
from dataclasses import dataclass, replace
from typing import Any, Literal

Decision = Literal["green", "red", "pending", "no-checks", "unknown", "not-open"]
FailedLogStatus = Literal["not-fetched", "fetched", "unavailable", "missing-run-id"]


@dataclass(frozen=True)
class FailedRunDiagnostic:
    check_name: str
    conclusion: str
    run_id: str
    details_url: str
    command: str
    log_status: FailedLogStatus = "not-fetched"
    log_excerpt: str = ""
    error: str = ""


@dataclass(frozen=True)
class PrStatusDecision:
    pr: str
    state: str
    merge_state_status: str
    head_ref_oid: str
    decision: Decision
    successful_checks: tuple[str, ...]
    pending_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    unknown_checks: tuple[str, ...]
    failed_run_log_hint: str
    failed_run_diagnostics: tuple[FailedRunDiagnostic, ...]


def _check_name(item: dict[str, Any]) -> str:
    return str(item.get("name") or item.get("workflowName") or item.get("__typename") or "unknown")


def _run_id_from_details_url(details_url: str) -> str:
    match = re.search(r"/actions/runs/([0-9]+)(?:/|$)", details_url)
    return match.group(1) if match else ""


def _failed_run_diagnostic(item: dict[str, Any], *, name: str, conclusion: str) -> FailedRunDiagnostic:
    details_url = str(item.get("detailsUrl") or item.get("details_url") or "")
    run_id = _run_id_from_details_url(details_url)
    command = f"gh run view {run_id} --log-failed" if run_id else ""
    return FailedRunDiagnostic(
        check_name=name,
        conclusion=conclusion,
        run_id=run_id,
        details_url=details_url,
        command=command,
    )


def classify_pr_status(payload: dict[str, Any], *, pr: str = "") -> PrStatusDecision:
    state = str(payload.get("state") or "UNKNOWN")
    checks = payload.get("statusCheckRollup") or []
    successful: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []
    failed_diagnostics: list[FailedRunDiagnostic] = []

    if state != "OPEN":
        decision: Decision = "not-open"
    elif not isinstance(checks, list) or not checks:
        decision = "no-checks"
    else:
        for item in checks:
            if not isinstance(item, dict):
                unknown.append("unknown")
                continue
            name = _check_name(item)
            status = str(item.get("status") or "").upper()
            conclusion = str(item.get("conclusion") or "").upper()
            if status != "COMPLETED":
                pending.append(name)
            elif conclusion == "SUCCESS":
                successful.append(name)
            elif conclusion in {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}:
                failed.append(name)
                failed_diagnostics.append(_failed_run_diagnostic(item, name=name, conclusion=conclusion))
            else:
                unknown.append(name)

        if failed:
            decision = "red"
        elif pending:
            decision = "pending"
        elif unknown:
            decision = "unknown"
        else:
            decision = "green"

    hint = "none"
    if decision == "red":
        commands = [diagnostic.command for diagnostic in failed_diagnostics if diagnostic.command]
        hint = f"run: {commands[0]}" if commands else "run: gh run view <failed-run-id> --log-failed"

    return PrStatusDecision(
        pr=pr,
        state=state,
        merge_state_status=str(payload.get("mergeStateStatus") or "UNKNOWN"),
        head_ref_oid=str(payload.get("headRefOid") or ""),
        decision=decision,
        successful_checks=tuple(successful),
        pending_checks=tuple(pending),
        failed_checks=tuple(failed),
        unknown_checks=tuple(unknown),
        failed_run_log_hint=hint,
        failed_run_diagnostics=tuple(failed_diagnostics),
    )


def _excerpt(text: str, *, max_lines: int) -> str:
    lines = text.strip().splitlines()
    if max_lines <= 0 or len(lines) <= max_lines:
        return "\n".join(lines)
    omitted = len(lines) - max_lines
    return "\n".join([*lines[:max_lines], f"... ({omitted} lines omitted)"])


def _fetch_failed_run_log(run_id: str) -> tuple[int, str, str]:
    completed = subprocess.run(["gh", "run", "view", run_id, "--log-failed"], text=True, capture_output=True, check=False)
    return completed.returncode, completed.stdout, completed.stderr


def attach_failed_run_logs(
    decision: PrStatusDecision,
    *,
    max_lines: int = 120,
    fetcher: Callable[[str], tuple[int, str, str]] = _fetch_failed_run_log,
) -> PrStatusDecision:
    diagnostics: list[FailedRunDiagnostic] = []
    for diagnostic in decision.failed_run_diagnostics:
        if not diagnostic.run_id:
            diagnostics.append(
                replace(
                    diagnostic,
                    log_status="missing-run-id",
                    error="failed check detailsUrl did not contain a GitHub Actions run id",
                )
            )
            continue
        returncode, stdout, stderr = fetcher(diagnostic.run_id)
        if returncode == 0:
            diagnostics.append(replace(diagnostic, log_status="fetched", log_excerpt=_excerpt(stdout, max_lines=max_lines)))
            continue
        diagnostics.append(
            replace(
                diagnostic,
                log_status="unavailable",
                log_excerpt=_excerpt(stdout, max_lines=max_lines),
                error=(stderr.strip() or stdout.strip() or f"gh run view exited with {returncode}"),
            )
        )
    return replace(decision, failed_run_diagnostics=tuple(diagnostics))


def _render_indented_block(text: str, *, indent: str = "  ") -> list[str]:
    if not text:
        return [f"{indent}(none)"]
    return [f"{indent}{line}" for line in text.splitlines()]


def render_decision(decision: PrStatusDecision) -> str:
    lines = [
        "NEXT_TURN_PR_STATUS",
        f"pr={decision.pr}",
        f"state={decision.state}",
        f"merge_state_status={decision.merge_state_status}",
        f"head_ref_oid={decision.head_ref_oid}",
        f"decision={decision.decision}",
        "successful_checks:",
        *[f"- {item}" for item in decision.successful_checks],
        "pending_checks:",
        *[f"- {item}" for item in decision.pending_checks],
        "failed_checks:",
        *[f"- {item}" for item in decision.failed_checks],
        "unknown_checks:",
        *[f"- {item}" for item in decision.unknown_checks],
        f"failed_run_log_hint={decision.failed_run_log_hint}",
        "failed_run_diagnostics:",
    ]
    for diagnostic in decision.failed_run_diagnostics:
        lines.extend(
            [
                (
                    f"- check={diagnostic.check_name} conclusion={diagnostic.conclusion} "
                    f"run_id={diagnostic.run_id or '(missing)'} log_status={diagnostic.log_status}"
                ),
                f"  command={diagnostic.command or '(unavailable)'}",
                f"  details_url={diagnostic.details_url or '(missing)'}",
            ]
        )
        if diagnostic.error:
            lines.append(f"  error={diagnostic.error}")
        lines.append("  log_excerpt:")
        lines.extend(_render_indented_block(diagnostic.log_excerpt, indent="    "))
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)


def _run_gh(args: list[str]) -> str:
    completed = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def fetch_pr_payload(pr: str) -> dict[str, Any]:
    raw = _run_gh([
        "pr",
        "view",
        pr,
        "--json",
        "baseRefName,baseRefOid,headRefName,headRefOid,state,mergeStateStatus,statusCheckRollup,url",
    ])
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("gh pr view did not return a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-pr-status")
    parser.add_argument("pr")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-failed-log-fetch", action="store_true")
    parser.add_argument("--failed-log-lines", type=int, default=120)
    args = parser.parse_args()

    payload = fetch_pr_payload(args.pr)
    decision = classify_pr_status(payload, pr=args.pr)
    if decision.decision == "red" and not args.no_failed_log_fetch:
        decision = attach_failed_run_logs(decision, max_lines=args.failed_log_lines)
    if args.json:
        print(json.dumps(asdict(decision), indent=2, sort_keys=True))
    else:
        print(render_decision(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
