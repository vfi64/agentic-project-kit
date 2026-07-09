from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import subprocess
from typing import Any


@dataclass(frozen=True)
class RemoteBranchInfo:
    branch: str
    merged_to_origin_main: bool


@dataclass(frozen=True)
class OpenPullRequestHead:
    head: str
    number: int
    title: str
    url: str


@dataclass(frozen=True)
class RemoteBranchFinding:
    branch: str
    short_name: str
    merged_to_origin_main: bool
    has_open_pr: bool
    open_pr_number: int | None
    proposed_action: str
    safety_class: str
    reason: str
    delete_command: str | None = None


@dataclass(frozen=True)
class RemoteBranchHygieneReport:
    findings: tuple[RemoteBranchFinding, ...]
    summary: dict[str, int]


def _short_name(branch: str) -> str:
    return branch.removeprefix("origin/")


def _is_protected_remote_ref(branch: str) -> bool:
    return branch in {"origin", "origin/HEAD", "origin/main"} or not branch.startswith("origin/")


def analyze_remote_branch_hygiene(
    remote_branches: list[RemoteBranchInfo],
    open_pr_heads: list[OpenPullRequestHead],
) -> RemoteBranchHygieneReport:
    open_prs_by_head = {pr.head: pr for pr in open_pr_heads}
    findings: list[RemoteBranchFinding] = []

    for info in sorted(remote_branches, key=lambda item: item.branch):
        if _is_protected_remote_ref(info.branch):
            continue

        short = _short_name(info.branch)
        open_pr = open_prs_by_head.get(short)

        if open_pr is not None:
            finding = RemoteBranchFinding(
                branch=info.branch,
                short_name=short,
                merged_to_origin_main=info.merged_to_origin_main,
                has_open_pr=True,
                open_pr_number=open_pr.number,
                proposed_action="keep",
                safety_class="protected-open-pr",
                reason="has open PR",
            )
        elif info.merged_to_origin_main:
            finding = RemoteBranchFinding(
                branch=info.branch,
                short_name=short,
                merged_to_origin_main=True,
                has_open_pr=False,
                open_pr_number=None,
                proposed_action="candidate-delete-merged-remote-branch",
                safety_class="dry-run-candidate",
                reason="merged into origin/main and no open PR",
            )
        else:
            finding = RemoteBranchFinding(
                branch=info.branch,
                short_name=short,
                merged_to_origin_main=False,
                has_open_pr=False,
                open_pr_number=None,
                proposed_action="manual-review",
                safety_class="manual-review",
                reason="not merged into origin/main",
            )
        findings.append(finding)

    summary = {
        "remote_branches": len(findings),
        "keep": sum(f.proposed_action == "keep" for f in findings),
        "candidate_delete_merged_remote_branch": sum(
            f.proposed_action == "candidate-delete-merged-remote-branch" for f in findings
        ),
        "manual_review": sum(f.proposed_action == "manual-review" for f in findings),
    }
    return RemoteBranchHygieneReport(findings=tuple(findings), summary=summary)


def report_as_json_data(report: RemoteBranchHygieneReport) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "k3_remote_branch_hygiene_report",
        "mode": "dry-run",
        "mutation": "none",
        "result_status": "PASS",
        "summary": report.summary,
        "findings": [asdict(finding) for finding in report.findings],
    }


def render_remote_branch_hygiene_report(report: RemoteBranchHygieneReport) -> str:
    lines = [
        "K3_REMOTE_BRANCH_HYGIENE",
        "MODE: dry-run",
        "MUTATION: none",
        "DELETE: disabled",
        "",
        "SUMMARY",
    ]
    for key, value in report.summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "FINDINGS"])
    if not report.findings:
        lines.append("- none")
    for finding in report.findings:
        pr = f" open_pr=#{finding.open_pr_number}" if finding.open_pr_number else ""
        lines.append(
            f"- {finding.branch}: action={finding.proposed_action} "
            f"safety={finding.safety_class}{pr} reason={finding.reason}"
        )
    return "\n".join(lines) + "\n"


def _run(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout.strip() or f"command failed: {' '.join(args)}")
    return completed.stdout


def _lines(repo_root: Path, args: list[str]) -> list[str]:
    return [line.strip() for line in _run(repo_root, args).splitlines() if line.strip()]


def collect_remote_branch_hygiene_inputs(repo_root: Path) -> tuple[list[RemoteBranchInfo], list[OpenPullRequestHead]]:
    remote_refs = _lines(repo_root, ["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"])
    merged_refs = set(
        _lines(repo_root, ["git", "branch", "-r", "--merged", "origin/main", "--format=%(refname:short)"])
    )
    remote_branches = [
        RemoteBranchInfo(branch=ref, merged_to_origin_main=ref in merged_refs)
        for ref in remote_refs
        if not _is_protected_remote_ref(ref)
    ]

    raw_prs = _run(
        repo_root,
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "300",
            "--json",
            "number,headRefName,title,url",
        ],
    )
    prs = []
    for item in json.loads(raw_prs or "[]"):
        prs.append(
            OpenPullRequestHead(
                head=str(item.get("headRefName") or ""),
                number=int(item.get("number") or 0),
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
            )
        )
    return remote_branches, prs

def build_remote_branch_hygiene_evidence_report_payload(report: RemoteBranchHygieneReport) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "k3_remote_branch_hygiene_evidence_report",
        "mode": "dry-run",
        "mutation": "none",
        "result_status": "PASS",
        "inventory": report_as_json_data(report),
    }


def write_remote_branch_hygiene_evidence_report(path: Path, report: RemoteBranchHygieneReport) -> None:
    payload = build_remote_branch_hygiene_evidence_report_payload(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
