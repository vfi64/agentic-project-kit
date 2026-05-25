from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "governance" / "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md"
COMPILED_CONTEXT = ROOT / ".agentic" / "compiled_agent_context.yaml"


def _contract_text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _compiled_context() -> dict[str, object]:
    return yaml.safe_load(COMPILED_CONTEXT.read_text(encoding="utf-8"))


def test_chat_bootstrap_contract_defines_mandatory_startup_sequence() -> None:
    text = _contract_text()

    assert "A successor chat must perform this sequence before proposing any mutation block" in text
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
    for source in required_sources:
        assert source in text
    assert "Inspect relevant source files and tests for the requested slice." in text
    assert "State any drift or uncertainty before acting." in text
    assert "must not replace the source-reading step with memory" in text


def test_chat_bootstrap_contract_preserves_remote_connector_direct_path_first_route() -> None:
    text = _contract_text()

    assert "Remote repository connector route" in text
    assert "GitHub connector direct-path-first workflow" in text
    assert "call `get_repo` for the exact `repository_full_name`" in text
    assert "call `fetch_file` for known paths instead of searching for them" in text
    assert "call `fetch_commit`, `get_pr_info`, `fetch_commit_workflow_runs`, or `compare_commits`" in text
    assert "use repository search only when the path or symbol is genuinely unknown" in text
    assert "raw URLs or local commands only after connector access is unavailable or insufficient" in text


def test_chat_bootstrap_contract_preserves_drift_classes_and_response() -> None:
    text = _contract_text()

    required_drift_classes = [
        "compiled context names sources that are missing",
        "human governance documents and compiled context disagree",
        "status or handoff documents point to stale next steps",
        "communication rules are absent from coverage or handoff",
        "portable execution rules are absent from coverage or tests",
        "a workflow claims no-copy completion without remote-readable evidence",
        "a workflow asks for pasted output although usable local or remote evidence exists",
        "remote repository inspection ignores the GitHub connector direct-path-first workflow",
        "governance YAML is mutated without a parse-modify-dump workflow and post-mutation parse validation",
    ]
    for drift_class in required_drift_classes:
        assert drift_class in text

    assert "warn that drift exists" in text
    assert "identify the source files involved" in text
    assert "avoid mutation-oriented work unless the mutation is the drift fix itself" in text
    assert "prefer a small deterministic fix slice over broad product work" in text
    assert "Drift must not be hidden behind a final PASS" in text


def test_chat_bootstrap_contract_preserves_yaml_mutation_and_handoff_requirements() -> None:
    text = _contract_text()

    assert "The only allowed mutation workflow for these files is parse-modify-dump" in text
    assert "parse the original YAML with `yaml.safe_load`" in text
    assert "write with `yaml.safe_dump` or an equivalent structured emitter" in text
    assert "parse the written file again" in text
    assert "Free-text insertion, regex insertion, manual indentation patches, and unparsed string concatenation are forbidden" in text
    assert "A drift handoff prompt must include" in text
    assert "current summary contract vocabulary" in text
    assert "communication rules including `d`, `f`, `w`, `paste-output`, and `stop`" in text
    assert "instruction not to mutate before reading the mandatory sources" in text


def test_compiled_context_matches_chat_bootstrap_and_drift_contract() -> None:
    context = _compiled_context()

    assert "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md" in context["mandatory_successor_chat_sources"]
    hard_rules = {item["id"]: item["rule"] for item in context["hard_rules"]}
    assert "chat-bootstrap-and-drift-contract" in hard_rules
    assert "Successor chats must read mandatory sources first" in hard_rules["chat-bootstrap-and-drift-contract"]
    assert "detect drift" in hard_rules["chat-bootstrap-and-drift-contract"]
    assert context["source_policy"]["github_connector_direct_path_first"] is True
    assert context["source_policy"]["yaml_governance_mutation_requires_parse_modify_dump"] is True
    assert context["drift_detection"]["fail_closed"] is True
    assert "warn" in context["drift_detection"]["on_drift"]
    assert "avoid mutation unless fixing drift" in context["drift_detection"]["on_drift"]
    drift_classes = context["drift_detection"]["drift_classes"]
    assert "missing mandatory bootstrap source" in drift_classes
    assert "stale status or handoff state" in drift_classes
    assert "remote work ignores the GitHub connector direct-path-first workflow" in drift_classes
    assert "governance YAML is mutated without parse-modify-dump validation" in drift_classes
