from pathlib import Path


def test_text_transfer_runner_documents_secure_remote_connector_branch_pr_merge_path() -> None:
    text = Path("docs/workflow/TEXT_TRANSFER_RUNNER.md").read_text(encoding="utf-8")

    required_terms = [
        "Secure remote connector Branch/PR/Merge path",
        "agentic-kit transfer branch-create <branch> --push",
        "agentic-kit transfer branch-switch <branch> --pull",
        "GitHub connector only for direct-path file create/update operations",
        "agentic-kit transfer pr-create --head <branch> --base main",
        "agentic-kit transfer pr-status <pr> --expected-head-sha <full_sha>",
        "agentic-kit transfer pr-wait-ci <pr> --expected-head-sha <full_sha>",
        "agentic-kit transfer pr-merge-safe <pr> --expected-head-sha <full_sha>",
        "connector must not write directly to `main` for product work",
        "PR head SHA must be treated as a pinned merge precondition",
    ]

    for term in required_terms:
        assert term in text
