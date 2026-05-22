from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_llm_communication_contract_files_exist_and_have_required_anchors() -> None:
    required = {
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md": [
            "User acknowledgements",
            "LLM-to-terminal rules",
            "Terminal-to-LLM rules",
            "Failure communication",
            "PASS communication",
            "REMOTE_EVIDENCE: PENDING",
            "paste-output",
        ],
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md": [
            "operating-system-independent",
            "Python modules",
            "shell commands are adapters only",
            "pathlib.Path",
            "shutil",
            "platform",
            "subprocess.run([...]",
            "shell=False",
        ],
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md": [
            "Mandatory startup sequence",
            "Drift classes",
            "Drift response",
            "Handoff prompt requirements",
            "comm-rules-check",
            "fail closed",
        ],
    }
    for path, anchors in required.items():
        text = read(path)
        for anchor in anchors:
            assert anchor in text, f"missing {anchor!r} in {path}"


def test_compiled_context_lists_mandatory_successor_chat_sources() -> None:
    text = read(".agentic/compiled_agent_context.yaml")
    required_sources = [
        ".agentic/compiled_agent_context.yaml",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/TEST_GATES.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    ]
    assert "mandatory_successor_chat_sources" in text
    for source in required_sources:
        assert source in text


def test_compiled_context_defines_final_summary_remote_evidence_vocabulary() -> None:
    text = read(".agentic/compiled_agent_context.yaml")
    for value in ["PASS", "FAIL", "PARTIAL", "NOT_REQUIRED"]:
        assert f"- {value}" in text
    assert "forbidden_remote_evidence_values:" in text
    for value in ["PENDING", "NONE", "CHAT_ONLY"]:
        assert f"- {value}" in text


def test_contracts_forbid_shell_as_canonical_workflow_control() -> None:
    text = read("docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md")
    forbidden_normative_patterns = [
        "/usr/bin/git",
        "/bin/cp",
        "hard-coded Unix paths such as `/usr/bin/git`, `/bin/cp`, or `/tmp` as normative rules",
    ]
    assert "Shell commands are adapters only" in text or "shell commands are adapters only" in text
    for pattern in forbidden_normative_patterns:
        assert pattern in text
    assert "must not require:" in text


def test_chat_bootstrap_contract_requires_stop_on_drift_before_mutation() -> None:
    text = read("docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md")
    assert "avoid mutation-oriented work unless the mutation is the drift fix itself" in text
    assert "must not replace the source-reading step with memory" in text
    assert "forbidden final summary values" in text or "forbidden final values" in text
