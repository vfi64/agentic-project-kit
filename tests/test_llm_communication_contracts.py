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
