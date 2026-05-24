from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_contains(path: str, terms: list[str]) -> None:
    text = read(path)
    for term in terms:
        assert term in text, f"missing {term!r} in {path}"


def test_llm_communication_contract_files_exist_and_have_required_anchors() -> None:
    assert_contains("docs/governance/CHAT_COMMUNICATION_CONTRACT.md", [
        "User acknowledgements", "LLM-to-terminal rules", "Terminal-to-LLM rules",
        "Failure communication", "PASS communication", "REMOTE_EVIDENCE: PENDING",
        "paste-output", "a rendered final summary printed in the terminal output",
        "captured in the terminal log or command report",
    ])
    assert_contains("docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md", [
        "operating-system-independent", "Python modules", "shell commands are adapters only",
        "pathlib.Path", "shutil", "platform", "subprocess.run([...", "shell=False",
    ])
    assert_contains("docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md", [
        "Mandatory startup sequence", "Drift classes", "Drift response",
        "Handoff prompt requirements", "comm-rules-check", "fail closed",
    ])


def test_compiled_context_lists_mandatory_successor_chat_sources() -> None:
    assert_contains(".agentic/compiled_agent_context.yaml", [
        "mandatory_successor_chat_sources", ".agentic/compiled_agent_context.yaml",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/TEST_GATES.md", "docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md",
    ])


def test_compiled_context_defines_final_summary_remote_evidence_vocabulary() -> None:
    assert_contains(".agentic/compiled_agent_context.yaml", [
        "- PASS", "- FAIL", "- PARTIAL", "- NOT_REQUIRED",
        "forbidden_remote_evidence_values:", "- PENDING", "- NONE", "- CHAT_ONLY",
    ])


def test_contracts_forbid_shell_as_canonical_workflow_control() -> None:
    assert_contains("docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md", [
        "Shell commands are adapters only", "/usr/bin/git", "/bin/cp",
        "hard-coded Unix paths such as `/usr/bin/git`, `/bin/cp`, or `/tmp` as normative rules",
        "must not require:",
    ])


def test_chat_bootstrap_contract_requires_stop_on_drift_before_mutation() -> None:
    assert_contains("docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md", [
        "avoid mutation-oriented work unless the mutation is the drift fix itself",
        "must not replace the source-reading step with memory",
    ])


def test_sentinel_tracks_llm_governance_contracts_with_realistic_limits() -> None:
    assert_contains("sentinel.yaml", [
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md", "max_words: 2200",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md", "max_words: 1800",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md", "max_words: 2000",
        "## LLM Communication and Bootstrap Gate", "max_words: 3200",
    ])


def test_test_gates_points_to_contracts_without_becoming_rule_book() -> None:
    assert_contains("docs/TEST_GATES.md", [
        "## LLM Communication and Bootstrap Gate",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        ".agentic/compiled_agent_context.yaml",
        "concise pointers, not duplicate rule books",
    ])


def test_documentation_coverage_tracks_llm_communication_contracts() -> None:
    assert_contains("docs/DOCUMENTATION_COVERAGE.yaml", [
        "llm-communication-bootstrap-coverage", ".agentic/compiled_agent_context.yaml",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/TEST_GATES.md", "mandatory_successor_chat_sources",
        "forbidden_remote_evidence_values", "User acknowledgements",
        "LLM-to-terminal rules", "Terminal-to-LLM rules",
        "a rendered final summary printed in the terminal output",
        "Shell commands are adapters only", "Mandatory startup sequence",
        "LLM Communication and Bootstrap Gate",
    ])


def test_local_repository_freshness_precondition_is_hardened_across_governance_docs() -> None:
    requirements = {
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md": [
            "Local repository freshness precondition", "stale or contaminated local tree is drift"],
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md": [
            "Local repository freshness rule", "Mutation before that precondition is forbidden"],
        "docs/TEST_GATES.md": ["Local Freshness Gate", "local repository freshness precondition"],
        ".agentic/compiled_agent_context.yaml": [
            "local_repo_freshness_before_local_work", "local-main-freshness-before-local-work"],
        "docs/DOCUMENTATION_COVERAGE.yaml": [
            "Local repository freshness precondition", "local-main-freshness-before-local-work"],
    }
    for path, anchors in requirements.items():
        assert_contains(path, anchors)


def test_remote_connector_route_is_hardened_before_search_or_raw_fallback() -> None:
    requirements = {
        ".agentic/compiled_agent_context.yaml": [
            "github_connector_direct_path_first",
            "github-connector-direct-path-first",
            "fetch_file/fetch_commit/get_pr_info/fetch_commit_workflow_runs/compare_commits",
        ],
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md": [
            "Remote repository connector route",
            "GitHub connector direct-path-first workflow",
            "call `fetch_file` for known paths instead of searching for them",
        ],
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md": [
            "Remote connector route rule",
            "direct connector route",
            "Search is for unknown paths or symbols",
        ],
        "docs/TEST_GATES.md": [
            "Remote Connector Gate",
            "GitHub connector direct-path-first workflow",
        ],
    }
    for path, anchors in requirements.items():
        assert_contains(path, anchors)


def test_governance_yaml_mutation_workflow_is_parse_modify_dump_only() -> None:
    requirements = {
        ".agentic/compiled_agent_context.yaml": [
            "yaml_governance_mutation_requires_parse_modify_dump",
            "yaml-governance-parse-modify-dump-only",
            "parse-modify-dump is the only allowed governance YAML mutation workflow",
        ],
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md": [
            "Governance YAML mutation rule",
            "The only allowed mutation workflow for these files is parse-modify-dump",
            "Free-text insertion, regex insertion, manual indentation patches",
        ],
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md": [
            "Governance YAML mutation rule",
            "must use parse-modify-dump",
            "YAML parse error in CI is a workflow defect",
        ],
        "docs/TEST_GATES.md": [
            "YAML Mutation Gate",
            "parse-modify-dump",
            "tests/test_yaml_governance_integrity.py tests/test_patch_artifact_preflight.py",
        ],
    }
    for path, anchors in requirements.items():
        assert_contains(path, anchors)
