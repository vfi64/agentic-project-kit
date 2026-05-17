from __future__ import annotations

from dataclasses import dataclass
import json
import re
import subprocess
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PullRequestInfo:
    number: int
    title: str
    head_ref: str
    base_ref: str = "main"
    url: str | None = None
    commits_ahead: int | None = None


@dataclass(frozen=True)
class BranchInfo:
    name: str
    gone: bool = False
    merged: bool = False


@dataclass(frozen=True)
class HygieneFinding:
    code: str
    severity: str
    summary: str
    details: tuple[str, ...]


@dataclass(frozen=True)
class HygieneReport:
    findings: tuple[HygieneFinding, ...]
    open_pr_count: int
    local_branch_count: int

    @property
    def ok(self) -> bool:
        return not self.findings


def normalize_slice_prefix(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"^(feature|fix|docs|release|chore|temp)/", "", text)
    text = re.sub(r"^#+\\d+[-_ ]*", "", text)
    text = re.sub(r"\\([^)]*\\)", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    parts = [part for part in text.split("-") if part]
    return "-".join(parts[:3]) if parts else "unknown"



def similar_pr_group_key(pr: PullRequestInfo) -> str:
    if pr.head_ref.startswith("dependabot/"):
        parts = pr.head_ref.split("/")
        if len(parts) >= 4:
            dependency = "/".join(parts[2:])
            dependency = re.sub(r"-[0-9][a-zA-Z0-9._-]*$", "", dependency)
            return f"dependabot:{parts[1]}:{dependency}"
        return f"dependabot:{pr.head_ref}"
    return normalize_slice_prefix(pr.head_ref or pr.title)


def analyze_pr_hygiene(open_prs: list[PullRequestInfo], local_branches: list[BranchInfo]) -> HygieneReport:
    findings: list[HygieneFinding] = []
    by_prefix: dict[str, list[PullRequestInfo]] = {}
    for pr in open_prs:
        prefix = similar_pr_group_key(pr)
        by_prefix.setdefault(prefix, []).append(pr)
        if pr.commits_ahead == 0:
            findings.append(HygieneFinding(
                "open-pr-without-main-delta",
                "warning",
                f"Open PR #{pr.number} has no commits ahead of {pr.base_ref}.",
                (f"title={pr.title}", f"head_ref={pr.head_ref}"),
            ))
    for prefix, prs in sorted(by_prefix.items()):
        if prefix != "unknown" and len(prs) > 1:
            details = tuple(f"#{pr.number} {pr.head_ref}: {pr.title}" for pr in prs)
            findings.append(HygieneFinding(
                "similar-open-prs",
                "warning",
                f"{len(prs)} open PRs share slice prefix {prefix}.",
                details,
            ))
    gone = [branch for branch in local_branches if branch.gone]
    if gone:
        findings.append(HygieneFinding(
            "local-branch-gone-upstream",
            "info",
            f"{len(gone)} local branches track deleted upstream branches.",
            tuple(branch.name for branch in gone),
        ))
    merged_prefixes = {normalize_slice_prefix(branch.name) for branch in local_branches if branch.merged}
    for pr in open_prs:
        prefix = normalize_slice_prefix(pr.head_ref)
        if prefix in merged_prefixes and pr.commits_ahead == 0:
            findings.append(HygieneFinding(
                "stale-sibling-after-merged-branch",
                "warning",
                f"Open PR #{pr.number} looks stale because a sibling branch with prefix {prefix} is already merged.",
                (f"title={pr.title}", f"head_ref={pr.head_ref}"),
            ))
    return HygieneReport(tuple(findings), len(open_prs), len(local_branches))


def report_as_json_data(report: HygieneReport) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "ok": report.ok,
        "open_pr_count": report.open_pr_count,
        "local_branch_count": report.local_branch_count,
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "summary": finding.summary,
                "details": list(finding.details),
            }
            for finding in report.findings
        ],
    }


def render_pr_hygiene_report(report: HygieneReport) -> str:
    lines = [
        "PR hygiene report",
        "Safety: read-only diagnosis; no branches, PRs, tags, releases, or files are changed.",
        f"open_pr_count={report.open_pr_count}",
        f"local_branch_count={report.local_branch_count}",
        f"ok={str(report.ok).lower()}",
    ]
    if not report.findings:
        lines.extend(["", "Findings:", "- none"])
        return "\n".join(lines)
    lines.extend(["", "Findings:"])
    for finding in report.findings:
        lines.append(f"- [{finding.severity}] {finding.code}: {finding.summary}")
        for detail in finding.details:
            lines.append(f"  - {detail}")
    lines.extend(["", "Next:", "- Review findings manually before closing PRs or deleting branches."])
    return "\n".join(lines)


def collect_pr_hygiene_inputs(project_root: Path) -> tuple[list[PullRequestInfo], list[BranchInfo]]:
    root = project_root.resolve()
    open_prs = _collect_open_prs(root)
    branches = _collect_local_branches(root)
    prs_with_delta = [_with_commits_ahead(root, pr) for pr in open_prs]
    return prs_with_delta, branches


def _collect_open_prs(root: Path) -> list[PullRequestInfo]:
    completed = subprocess.run([
        "gh", "pr", "list", "--state", "open", "--json", "number,title,headRefName,baseRefName,url"
    ], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    data = json.loads(completed.stdout)
    return [
        PullRequestInfo(
            number=int(item["number"]),
            title=str(item.get("title", "")),
            head_ref=str(item.get("headRefName", "")),
            base_ref=str(item.get("baseRefName", "main") or "main"),
            url=item.get("url"),
        )
        for item in data
    ]


def _collect_local_branches(root: Path) -> list[BranchInfo]:
    completed = subprocess.run([
        "git", "branch", "--format", "%(refname:short)|%(upstream:track)|%(if)%(HEAD)%(then)current%(end)"
    ], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return []
    merged = _merged_branches(root)
    branches = []
    for line in completed.stdout.splitlines():
        name, track, *_rest = (line.split("|") + ["", ""])[:3]
        if not name:
            continue
        branches.append(BranchInfo(name=name, gone="[gone]" in track, merged=name in merged))
    return branches


def _merged_branches(root: Path) -> set[str]:
    completed = subprocess.run(["git", "branch", "--merged"], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return set()
    return {line.replace("*", "").strip() for line in completed.stdout.splitlines() if line.strip()}


def _with_commits_ahead(root: Path, pr: PullRequestInfo) -> PullRequestInfo:
    completed = subprocess.run([
        "git", "rev-list", "--count", f"{pr.base_ref}..{pr.head_ref}"
    ], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return pr
    try:
        count = int(completed.stdout.strip())
    except ValueError:
        return pr
    return PullRequestInfo(pr.number, pr.title, pr.head_ref, pr.base_ref, pr.url, count)
