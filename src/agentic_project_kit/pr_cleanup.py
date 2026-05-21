from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
from typing import Any


@dataclass(frozen=True)
class PullRequestInfo:
    number: int
    head: str
    base: str
    mergeable: str
    is_draft: bool
    author: str
    updated_at: str
    title: str


@dataclass(frozen=True)
class ClassifiedPullRequest:
    info: PullRequestInfo
    pr_class: str
    action: str


def classify_pr(pr: PullRequestInfo) -> ClassifiedPullRequest:
    pr_class = "ACTIVE_FEATURE_PR"
    action = "review_manually"

    if pr.head.startswith("dependabot/"):
        pr_class = "DEPENDABOT_PR"
        action = "review_dependency_update"
    elif pr.head.startswith(("docs/finalize-", "docs/record-", "docs/post-")):
        pr_class = "STALE_DOCS_FINALIZATION_CANDIDATE"
        action = "run_finalize_guard_before_closing_or_recreating"
    elif pr.head.startswith("release/prepare-"):
        pr_class = "RELEASE_PREP_PR"
        action = "verify_release_state_before_merge_or_close"

    if pr.mergeable == "CONFLICTING":
        if pr_class == "STALE_DOCS_FINALIZATION_CANDIDATE":
            pr_class = "SUPERSEDED_OR_CONFLICTING_DOCS_FINALIZATION"
            action = "run_finalize_guard_then_human_decide_safe_close"
        elif pr_class == "DEPENDABOT_PR":
            action = "review_dependency_conflict"
        else:
            pr_class = "CONFLICTING_RELEVANT_PR"
            action = "human_review_required"

    if pr.is_draft:
        action = "draft_review_required"

    return ClassifiedPullRequest(pr, pr_class, action)


def _run(repo_root: Path, args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def _author_login(raw_author: Any) -> str:
    if isinstance(raw_author, dict):
        return str(raw_author.get("login") or "")
    return str(raw_author or "")


def parse_prs(payload: str) -> list[PullRequestInfo]:
    data = json.loads(payload or "[]")
    prs: list[PullRequestInfo] = []
    for item in data:
        prs.append(
            PullRequestInfo(
                number=int(item.get("number", 0)),
                head=str(item.get("headRefName") or ""),
                base=str(item.get("baseRefName") or ""),
                mergeable=str(item.get("mergeable") or "UNKNOWN"),
                is_draft=bool(item.get("isDraft", False)),
                author=_author_login(item.get("author")),
                updated_at=str(item.get("updatedAt") or ""),
                title=str(item.get("title") or ""),
            )
        )
    return prs


def list_open_prs(repo_root: Path) -> tuple[int, list[PullRequestInfo], str]:
    rc, output = _run(
        repo_root,
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,headRefName,baseRefName,mergeable,isDraft,title,author,updatedAt",
        ],
    )
    if rc != 0:
        return rc, [], output
    return 0, parse_prs(output), ""


def render_classification(classified: list[ClassifiedPullRequest], branch: str, status: str, ok: bool = True) -> str:
    lines = [
        "",
        "",
        "",
        "-------------------------------------------------------------------------",
        "-------------------------------------------------------------------------",
        "-------------------------------------------------------------------------",
        "",
        "",
        "",
        "NS PR CLEANUP CLASSIFICATION",
        "",
        "### SAFETY ###",
        "Safety: read-only PR classification; no close, merge, edit, push, delete, tag, or release action.",
        "",
        "### OPEN PR CLASSIFICATION ###",
        f"open_pr_count={len(classified)}",
    ]
    if not classified:
        lines.append("No open PRs found.")
    for entry in classified:
        pr = entry.info
        draft = str(pr.is_draft).lower()
        lines.append(
            f"#{pr.number} class={entry.pr_class} action={entry.action} mergeable={pr.mergeable} "
            f"draft={draft} head={pr.head} base={pr.base} author={pr.author} updated={pr.updated_at} title={pr.title}"
        )
    lines.extend(["", "### FINAL STATE ###", branch])
    if status:
        lines.append(status)
    lines.append("" )
    lines.append("### RESULT: PASS ###" if ok else "### RESULT: FAIL ###")
    return "\n".join(lines)


def run_pr_cleanup(repo_root: Path) -> int:
    rc, prs, error = list_open_prs(repo_root)
    if rc != 0:
        print("ERROR: unable to list open PRs.")
        if error:
            print(error)
        print("\n### RESULT: FAIL ###")
        return 1
    branch_rc, branch = _run(repo_root, ["git", "branch", "--show-current"])
    status_rc, status = _run(repo_root, ["git", "status", "--short"])
    ok = branch_rc == 0 and status_rc == 0
    print(render_classification([classify_pr(pr) for pr in prs], branch, status, ok=ok))
    return 0 if ok else 1


def main() -> int:
    return run_pr_cleanup(Path(".").resolve())


if __name__ == "__main__":
    raise SystemExit(main())
