from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "governance" / "PORTABLE_CHAT_EXECUTION_CONTRACT.md"
COMPILED_CONTEXT = ROOT / ".agentic" / "compiled_agent_context.yaml"


def _contract_text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _compiled_context() -> dict[str, object]:
    return yaml.safe_load(COMPILED_CONTEXT.read_text(encoding="utf-8"))


def test_portable_execution_contract_defines_python_core_as_canonical() -> None:
    text = _contract_text()

    assert "Durable workflow behavior belongs in Python modules, tests, and CLI commands." in text
    assert "shell commands are adapters only" in text
    assert "pathlib.Path" in text
    assert "shutil" in text
    assert "platform" in text
    assert "subprocess.run([...], shell=False)" in text
    assert "explicit return objects or structured text reports" in text


def test_portable_execution_contract_rejects_shell_as_canonical_dependency() -> None:
    text = _contract_text()

    forbidden_terms = ["cp", "tail", "grep", "sed", "head", "tee", "find", "sh"]
    for term in forbidden_terms:
        assert f"`{term}`" in text
    assert "hard-coded Unix paths" in text
    assert "shell pipelines for correctness" in text
    assert "shell-specific quoting behavior" in text
    assert "shell activation of a virtual environment as the only path to execution" in text


def test_portable_execution_contract_preserves_remote_connector_and_yaml_mutation_rules() -> None:
    text = _contract_text()

    assert "Remote connector route rule" in text
    assert "direct connector route" in text
    assert "fetch_file" in text
    assert "fetch_commit" in text
    assert "get_pr_info" in text
    assert "fetch_commit_workflow_runs" in text
    assert "Governance YAML mutation rule" in text
    assert "parse-modify-dump" in text
    assert "Manual indentation patches" in text
    assert "unparsed string concatenation" in text


def test_portable_execution_contract_preserves_portable_evidence_and_chat_block_boundaries() -> None:
    text = _contract_text()

    assert "Evidence rule" in text
    assert "without POSIX file-copy utilities" in text
    assert "direct log writing through Python file APIs" in text
    assert "A chat-generated terminal block is allowed only as a bounded fallback or adapter." in text
    assert "must not be the authoritative expression of a reusable workflow" in text
    assert "must not claim the portable workflow is healthy" in text


def test_compiled_context_matches_portable_execution_contract() -> None:
    context = _compiled_context()

    assert "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md" in context["mandatory_successor_chat_sources"]
    hard_rules = {item["id"]: item["rule"] for item in context["hard_rules"]}
    assert "portable-chat-execution-contract" in hard_rules
    assert "Python-core-first" in hard_rules["portable-chat-execution-contract"]
    portable_rules = context["portable_execution_rules"]
    assert portable_rules["canonical_core"] == "Python modules and CLI commands"
    assert portable_rules["shell_role"] == "adapter only"
    assert "pathlib.Path" in portable_rules["python_apis"]
    assert "subprocess.run with shell=False" in portable_rules["python_apis"]
    assert "shell pipelines for correctness" in portable_rules["forbidden_canonical_dependencies"]
    assert "hard-coded Unix tool paths" in portable_rules["forbidden_canonical_dependencies"]
