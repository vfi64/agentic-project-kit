from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.evidence_inspector import EvidenceInspection
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.run_summary_renderer import SummaryPayload
from agentic_project_kit.run_summary_renderer import render_summary


@dataclass(frozen=True)
class FinalizeLogResult:
    success: bool
    run_log: Path
    remote_log: Path
    commit_created: bool
    commit_sha: str
    summary_inspection: EvidenceInspection
    findings: tuple[str, ...] = ()


def _run_git(args: list[str], *, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _git_stdout(args: list[str], *, root: Path) -> str:
    result = _run_git(args, root=root)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def finalize_log(
    *,
    root: Path | str,
    run_log: Path | str,
    remote_log: Path | str,
    slice_name: str,
    scope: str,
    mode_check: str,
    work: str,
    evidence: str,
    overall: str,
    remote_evidence: str,
    pr: str,
    ci: str,
    merge: str,
    command_report: str,
    interpretation: str,
    safe_step: str,
    chat_reply: str = "d",
    origin: str = "local",
    state_mode: str = "local",
    comm_id: str = "COMM-LOCAL",
    commit_message: str | None = None,
    push: bool = False,
) -> FinalizeLogResult:
    root_path = Path(root).resolve()
    run_log_path = Path(run_log)
    if not run_log_path.is_absolute():
        run_log_path = root_path / run_log_path
    remote_log_path = Path(remote_log)
    if remote_log_path.is_absolute():
        raise ValueError("remote_log must be a repository-relative docs/reports/terminal path")
    if not str(remote_log_path).startswith("docs/reports/terminal/"):
        raise ValueError("remote_log must start with docs/reports/terminal/")
    if not run_log_path.exists():
        raise FileNotFoundError(run_log_path)

    branch = _git_stdout(["branch", "--show-current"], root=root_path) or "UNKNOWN"
    head_sha = _git_stdout(["rev-parse", "HEAD"], root=root_path) or "UNKNOWN"
    payload = SummaryPayload(
        comm_id=comm_id,
        slice=slice_name,
        scope=scope,
        branch=branch,
        origin=origin,
        state_mode=state_mode,
        mode_check=mode_check,
        work=work,
        evidence=evidence,
        overall=overall,
        remote_evidence=remote_evidence,
        pr=pr,
        head_sha=head_sha,
        ci=ci,
        merge=merge,
        terminal_log=str(run_log_path),
        terminal_log_remote=str(remote_log_path),
        terminal_log_local=str(run_log_path),
        command_report=command_report,
        interpretation=interpretation,
        safe_step=safe_step,
        chat_reply=chat_reply,
    )
    summary = render_summary(payload)
    with run_log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n### CANONICAL SUMMARY ###\n")
        handle.write(summary)
        handle.write("\n")

    summary_inspection = inspect_evidence(run_log_path, root=root_path, require_summary=True)
    findings: list[str] = []
    if not summary_inspection.success:
        findings.append("structured summary inspection failed")
        return FinalizeLogResult(False, run_log_path, remote_log_path, False, "", summary_inspection, tuple(findings))

    destination = root_path / remote_log_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(run_log_path, destination)

    add_result = _run_git(["add", str(remote_log_path)], root=root_path)
    if add_result.returncode != 0:
        findings.append(add_result.stderr.strip() or "git add failed")
        return FinalizeLogResult(False, run_log_path, remote_log_path, False, "", summary_inspection, tuple(findings))

    diff_result = _run_git(["diff", "--cached", "--quiet"], root=root_path)
    commit_created = diff_result.returncode != 0
    commit_sha = _git_stdout(["rev-parse", "HEAD"], root=root_path) or "UNKNOWN"
    if commit_created:
        message = commit_message or f"Record {slice_name} evidence log"
        commit_result = _run_git(["commit", "-m", message], root=root_path)
        if commit_result.returncode != 0:
            findings.append(commit_result.stderr.strip() or "git commit failed")
            return FinalizeLogResult(False, run_log_path, remote_log_path, False, "", summary_inspection, tuple(findings))
        commit_sha = _git_stdout(["rev-parse", "HEAD"], root=root_path) or "UNKNOWN"
        if push:
            push_result = _run_git(["push", "origin", branch], root=root_path)
            if push_result.returncode != 0:
                findings.append(push_result.stderr.strip() or "git push failed")
                return FinalizeLogResult(False, run_log_path, remote_log_path, True, commit_sha, summary_inspection, tuple(findings))
    return FinalizeLogResult(True, run_log_path, remote_log_path, commit_created, commit_sha, summary_inspection, tuple(findings))


def render_finalize_log_result(result: FinalizeLogResult) -> str:
    lines = [
        "EVIDENCE_FINALIZE_LOG",
        f"success: {'yes' if result.success else 'no'}",
        f"run_log: {result.run_log}",
        f"remote_log: {result.remote_log}",
        f"commit_created: {'yes' if result.commit_created else 'no'}",
        f"commit_sha: {result.commit_sha or 'NONE'}",
        f"summary_verdict: {result.summary_inspection.verdict.value}",
        f"structured_summary_found: {'yes' if result.summary_inspection.structured_summary.found else 'no'}",
        f"structured_summary_valid: {'yes' if result.summary_inspection.structured_summary.valid else 'no'}",
    ]
    if result.findings:
        lines.append("findings:")
        lines.extend(f"- {finding}" for finding in result.findings)
    lines.append(f"### RESULT: {'PASS' if result.success else 'FAIL'} ###")
    return "\n".join(lines)
