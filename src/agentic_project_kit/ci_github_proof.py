from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


JsonRunner = Callable[[list[str]], Any]
TextRunner = Callable[[list[str]], str]


@dataclass(frozen=True)
class MainPushPrProof:
    schema_version: int
    kind: str
    status: str
    reasons: tuple[str, ...]
    final_commit_sha: str
    final_tree_sha: str = ""
    source_pr: int | None = None
    source_pr_url: str = ""
    base_ref: str = ""
    merge_commit_sha: str = ""
    tested_commit_sha: str = ""
    tested_tree_sha: str = ""
    pr_checks_passed: bool = False
    required_check: str = "CI/test"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _proof(
    *,
    status: str,
    reasons: tuple[str, ...],
    final_commit_sha: str,
    final_tree_sha: str = "",
    source_pr: int | None = None,
    source_pr_url: str = "",
    base_ref: str = "",
    merge_commit_sha: str = "",
    tested_commit_sha: str = "",
    tested_tree_sha: str = "",
    pr_checks_passed: bool = False,
    required_check: str = "CI/test",
) -> MainPushPrProof:
    return MainPushPrProof(
        schema_version=1,
        kind="main_push_pr_tree_proof_input",
        status=status,
        reasons=reasons,
        final_commit_sha=final_commit_sha,
        final_tree_sha=final_tree_sha,
        source_pr=source_pr,
        source_pr_url=source_pr_url,
        base_ref=base_ref,
        merge_commit_sha=merge_commit_sha,
        tested_commit_sha=tested_commit_sha,
        tested_tree_sha=tested_tree_sha,
        pr_checks_passed=pr_checks_passed,
        required_check=required_check,
    )


def required_ci_test_passed(
    status_check_rollup: list[dict[str, Any]],
    *,
    workflow_name: str = "CI",
    check_name: str = "test",
) -> bool:
    for check in status_check_rollup:
        if not isinstance(check, dict):
            continue
        if check.get("__typename") != "CheckRun":
            continue
        if check.get("workflowName") != workflow_name:
            continue
        if check.get("name") != check_name:
            continue
        if check.get("status") == "COMPLETED" and check.get("conclusion") == "SUCCESS":
            return True
    return False


def select_single_merged_pr_for_commit(
    associated_prs: list[dict[str, Any]],
    *,
    current_sha: str,
    base_branch: str,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not associated_prs:
        return None, ("no associated merged pull request was found for the push commit",)
    if len(associated_prs) != 1:
        return None, ("push commit is associated with multiple pull requests",)
    pr = associated_prs[0]
    if pr.get("state") != "closed" or not pr.get("merged_at"):
        return None, ("associated pull request is not merged",)
    if pr.get("merge_commit_sha") != current_sha:
        return None, ("associated pull request merge commit does not match the push commit",)
    base = pr.get("base")
    if not isinstance(base, dict) or base.get("ref") != base_branch:
        return None, ("associated pull request does not target the protected base branch",)
    return pr, ()


def _run_json(argv: list[str]) -> Any:
    process = subprocess.run(argv, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "command failed")
    return json.loads(process.stdout)


def _run_text(argv: list[str]) -> str:
    process = subprocess.run(argv, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "command failed")
    return process.stdout.strip()


def _fetch_commit_if_needed(sha: str, *, text_runner: TextRunner = _run_text) -> None:
    commit_available = True
    try:
        text_runner(["git", "cat-file", "-e", f"{sha}^{{commit}}"])
    except RuntimeError:
        commit_available = False
    if commit_available:
        return
    text_runner(["git", "fetch", "--no-tags", "--depth=1", "origin", sha])
    text_runner(["git", "cat-file", "-e", f"{sha}^{{commit}}"])


def resolve_main_push_pr_tree_proof(
    *,
    repo: str,
    current_sha: str,
    base_branch: str = "main",
    required_workflow: str = "CI",
    required_check: str = "test",
    json_runner: JsonRunner = _run_json,
    text_runner: TextRunner = _run_text,
) -> MainPushPrProof:
    reasons: list[str] = []
    final_tree_sha = ""
    try:
        final_tree_sha = text_runner(["git", "rev-parse", f"{current_sha}^{{tree}}"])
    except RuntimeError as exc:
        reasons.append(f"final push tree could not be resolved: {exc}")
        return _proof(status="BLOCK", reasons=tuple(reasons), final_commit_sha=current_sha)

    try:
        associated_prs = json_runner(
            [
                "gh",
                "api",
                "-H",
                "Accept: application/vnd.github+json",
                f"repos/{repo}/commits/{current_sha}/pulls",
            ]
        )
    except (RuntimeError, json.JSONDecodeError) as exc:
        return _proof(
            status="BLOCK",
            reasons=(f"associated pull request lookup failed: {exc}",),
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
        )
    if not isinstance(associated_prs, list):
        return _proof(
            status="BLOCK",
            reasons=("associated pull request lookup did not return a list",),
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
        )
    associated_pr, blockers = select_single_merged_pr_for_commit(
        associated_prs,
        current_sha=current_sha,
        base_branch=base_branch,
    )
    if blockers or associated_pr is None:
        return _proof(
            status="BLOCK",
            reasons=blockers,
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
        )

    source_pr = int(associated_pr["number"])
    source_pr_url = str(associated_pr.get("html_url") or "")
    try:
        pr_view = json_runner(
            [
                "gh",
                "pr",
                "view",
                str(source_pr),
                "--json",
                "number,state,baseRefName,headRefOid,mergeCommit,statusCheckRollup,url",
            ]
        )
    except (RuntimeError, json.JSONDecodeError) as exc:
        return _proof(
            status="BLOCK",
            reasons=(f"pull request proof lookup failed: {exc}",),
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
            source_pr=source_pr,
            source_pr_url=source_pr_url,
        )

    if not isinstance(pr_view, dict):
        return _proof(
            status="BLOCK",
            reasons=("pull request proof lookup did not return an object",),
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
            source_pr=source_pr,
            source_pr_url=source_pr_url,
        )

    base_ref = str(pr_view.get("baseRefName") or "")
    merge_commit = pr_view.get("mergeCommit")
    merge_commit_sha = str(merge_commit.get("oid") or "") if isinstance(merge_commit, dict) else ""
    tested_commit_sha = str(pr_view.get("headRefOid") or "")
    checks = pr_view.get("statusCheckRollup")
    checks_passed = required_ci_test_passed(
        checks if isinstance(checks, list) else [],
        workflow_name=required_workflow,
        check_name=required_check,
    )

    if pr_view.get("state") != "MERGED":
        reasons.append("pull request proof state is not MERGED")
    if base_ref != base_branch:
        reasons.append("pull request proof base branch does not match protected branch")
    if merge_commit_sha != current_sha:
        reasons.append("pull request proof merge commit does not match push commit")
    if not tested_commit_sha:
        reasons.append("pull request proof head commit is missing")
    if not checks_passed:
        reasons.append("required CI/test check did not pass for the pull request")

    tested_tree_sha = ""
    if tested_commit_sha:
        try:
            _fetch_commit_if_needed(tested_commit_sha, text_runner=text_runner)
            tested_tree_sha = text_runner(["git", "rev-parse", f"{tested_commit_sha}^{{tree}}"])
        except RuntimeError as exc:
            reasons.append(f"pull request tested tree could not be resolved: {exc}")

    if tested_tree_sha and tested_tree_sha != final_tree_sha:
        reasons.append("final main tree does not match the pull request head tree")

    if reasons:
        return _proof(
            status="BLOCK",
            reasons=tuple(reasons),
            final_commit_sha=current_sha,
            final_tree_sha=final_tree_sha,
            source_pr=source_pr,
            source_pr_url=source_pr_url,
            base_ref=base_ref,
            merge_commit_sha=merge_commit_sha,
            tested_commit_sha=tested_commit_sha,
            tested_tree_sha=tested_tree_sha,
            pr_checks_passed=checks_passed,
            required_check=f"{required_workflow}/{required_check}",
        )
    return _proof(
        status="PASS",
        reasons=("merged pull request, required check, and exact tree equality are proven",),
        final_commit_sha=current_sha,
        final_tree_sha=final_tree_sha,
        source_pr=source_pr,
        source_pr_url=source_pr_url,
        base_ref=base_ref,
        merge_commit_sha=merge_commit_sha,
        tested_commit_sha=tested_commit_sha,
        tested_tree_sha=tested_tree_sha,
        pr_checks_passed=True,
        required_check=f"{required_workflow}/{required_check}",
    )


def _write_json_or_stdout(payload: dict[str, Any], output: str) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve GitHub proof inputs for CI runtime policy.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--current-sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--required-workflow", default="CI")
    parser.add_argument("--required-check", default="test")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)

    if not args.repo or not args.current_sha:
        payload = _proof(
            status="BLOCK",
            reasons=("repository and current SHA are required",),
            final_commit_sha=args.current_sha,
            required_check=f"{args.required_workflow}/{args.required_check}",
        ).as_dict()
    else:
        payload = resolve_main_push_pr_tree_proof(
            repo=args.repo,
            current_sha=args.current_sha,
            base_branch=args.base_branch,
            required_workflow=args.required_workflow,
            required_check=args.required_check,
        ).as_dict()
    _write_json_or_stdout(payload, args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
