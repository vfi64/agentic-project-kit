from __future__ import annotations

from typing import Any

from agentic_project_kit.ci_github_proof import (
    required_ci_test_passed,
    resolve_main_push_pr_tree_proof,
    select_single_merged_pr_for_commit,
)


CURRENT_SHA = "977a51cedb9ad4ca68132d7045521eaaa4b59f90"
HEAD_SHA = "d9f93511ba6b1725a3f8809935a960f9eb163f61"


def _associated_pr() -> dict[str, Any]:
    return {
        "number": 2205,
        "state": "closed",
        "merged_at": "2026-08-28T15:01:08Z",
        "merge_commit_sha": CURRENT_SHA,
        "html_url": "https://github.com/vfi64/agentic-project-kit/pull/2205",
        "base": {"ref": "main"},
    }


def _pr_view(*, tree_check: bool = True) -> dict[str, Any]:
    return {
        "number": 2205,
        "state": "MERGED",
        "baseRefName": "main",
        "headRefOid": HEAD_SHA,
        "mergeCommit": {"oid": CURRENT_SHA},
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "workflowName": "CI",
                "name": "test",
                "status": "COMPLETED",
                "conclusion": "SUCCESS" if tree_check else "FAILURE",
            }
        ],
        "url": "https://github.com/vfi64/agentic-project-kit/pull/2205",
    }


def test_required_ci_test_passed_requires_exact_workflow_check_success() -> None:
    assert required_ci_test_passed(_pr_view()["statusCheckRollup"]) is True
    assert required_ci_test_passed(_pr_view(tree_check=False)["statusCheckRollup"]) is False
    assert (
        required_ci_test_passed(
            [
                {
                    "__typename": "CheckRun",
                    "workflowName": "CI",
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "SKIPPED",
                }
            ]
        )
        is False
    )
    assert (
        required_ci_test_passed(
            [
                {
                    "__typename": "CheckRun",
                    "workflowName": "Pages",
                    "name": "test",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                }
            ]
        )
        is False
    )


def test_select_single_merged_pr_for_commit_is_fail_closed() -> None:
    selected, reasons = select_single_merged_pr_for_commit(
        [_associated_pr()],
        current_sha=CURRENT_SHA,
        base_branch="main",
    )

    assert selected and selected["number"] == 2205
    assert reasons == ()

    assert select_single_merged_pr_for_commit([], current_sha=CURRENT_SHA, base_branch="main")[1] == (
        "no associated merged pull request was found for the push commit",
    )
    assert select_single_merged_pr_for_commit(
        [{**_associated_pr(), "base": {"ref": "release"}}],
        current_sha=CURRENT_SHA,
        base_branch="main",
    )[1] == ("associated pull request does not target the protected base branch",)


def test_resolve_main_push_pr_tree_proof_accepts_exact_tree_and_required_check() -> None:
    def json_runner(argv: list[str]) -> Any:
        if argv[:2] == ["gh", "api"]:
            return [_associated_pr()]
        if argv[:2] == ["gh", "pr"]:
            return _pr_view()
        raise AssertionError(argv)

    def text_runner(argv: list[str]) -> str:
        if argv[:2] == ["git", "rev-parse"]:
            return "tree123"
        if argv[:2] == ["git", "cat-file"]:
            return ""
        if argv[:2] == ["git", "fetch"]:
            return ""
        raise AssertionError(argv)

    proof = resolve_main_push_pr_tree_proof(
        repo="vfi64/agentic-project-kit",
        current_sha=CURRENT_SHA,
        json_runner=json_runner,
        text_runner=text_runner,
    )

    assert proof.status == "PASS"
    assert proof.source_pr == 2205
    assert proof.final_tree_sha == "tree123"
    assert proof.tested_tree_sha == "tree123"
    assert proof.pr_checks_passed is True


def test_resolve_main_push_pr_tree_proof_ignores_skipped_shadow_when_required_check_passed() -> None:
    pr_view = _pr_view()
    pr_view["statusCheckRollup"].append(
        {
            "__typename": "CheckRun",
            "workflowName": "CI",
            "name": "pytest-parallel-shadow",
            "status": "COMPLETED",
            "conclusion": "SKIPPED",
        }
    )

    def json_runner(argv: list[str]) -> Any:
        if argv[:2] == ["gh", "api"]:
            return [_associated_pr()]
        if argv[:2] == ["gh", "pr"]:
            return pr_view
        raise AssertionError(argv)

    def text_runner(argv: list[str]) -> str:
        if argv[:2] == ["git", "rev-parse"]:
            return "tree123"
        if argv[:2] == ["git", "cat-file"]:
            return ""
        if argv[:2] == ["git", "fetch"]:
            return ""
        raise AssertionError(argv)

    proof = resolve_main_push_pr_tree_proof(
        repo="vfi64/agentic-project-kit",
        current_sha=CURRENT_SHA,
        json_runner=json_runner,
        text_runner=text_runner,
    )

    assert proof.status == "PASS"
    assert proof.pr_checks_passed is True


def test_resolve_main_push_pr_tree_proof_blocks_tree_mismatch_or_missing_check() -> None:
    def json_runner(argv: list[str]) -> Any:
        if argv[:2] == ["gh", "api"]:
            return [_associated_pr()]
        if argv[:2] == ["gh", "pr"]:
            return _pr_view(tree_check=False)
        raise AssertionError(argv)

    def text_runner(argv: list[str]) -> str:
        if argv[:2] == ["git", "rev-parse"]:
            return "final-tree" if argv[-1].startswith(CURRENT_SHA) else "head-tree"
        if argv[:2] == ["git", "cat-file"]:
            return ""
        if argv[:2] == ["git", "fetch"]:
            return ""
        raise AssertionError(argv)

    proof = resolve_main_push_pr_tree_proof(
        repo="vfi64/agentic-project-kit",
        current_sha=CURRENT_SHA,
        json_runner=json_runner,
        text_runner=text_runner,
    )

    assert proof.status == "BLOCK"
    assert "required CI/test check did not pass for the pull request" in proof.reasons
    assert "final main tree does not match the pull request head tree" in proof.reasons
