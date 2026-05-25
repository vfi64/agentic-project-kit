from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHAT_CONTRACT = ROOT / "docs" / "governance" / "CHAT_COMMUNICATION_CONTRACT.md"
SUMMARY_CONTRACT = ROOT / "docs" / "governance" / "FINAL_SUMMARY_CONTRACT.md"
COMPILED_CONTEXT = ROOT / ".agentic" / "compiled_agent_context.yaml"


def _chat_contract_text() -> str:
    return CHAT_CONTRACT.read_text(encoding="utf-8")


def _summary_contract_text() -> str:
    return SUMMARY_CONTRACT.read_text(encoding="utf-8")


def _compiled_context() -> dict[str, object]:
    return yaml.safe_load(COMPILED_CONTEXT.read_text(encoding="utf-8"))


def test_chat_contract_defines_short_replies_as_control_signals_not_evidence() -> None:
    text = _chat_contract_text()

    assert "Short user replies are control signals, not evidence." in text
    assert "`d` or `D`" in text
    assert "must still inspect terminal output, remote log, command report, PR state, branch, dirty state, and summary" in text
    assert "`f` or `F`" in text
    assert "must first look for local or remote evidence paths and propose log upload/recovery" in text
    assert "`w` or `W`: continue, but only within the current governance and evidence rules." in text
    assert "`paste-output`: manual output is needed because repo-backed or local evidence is unavailable" in text
    assert "`stop`: no further mutation or terminal instructions." in text


def test_chat_contract_preserves_remote_log_first_failure_recovery() -> None:
    text = _chat_contract_text()

    assert "inspect remote evidence if available" in text
    assert "inspect local log path if the user pasted it" in text
    assert "propose a minimal log-upload or status-recovery step" in text
    assert "ask for pasted output only when evidence cannot be retrieved or uploaded" in text
    assert "A terminal log upload is evidence transport. It does not change the result of failed work." in text
    assert "If a terminal summary names a concrete remote log path, verify that exact path directly before using search results." in text


def test_chat_contract_preserves_pass_requirements_and_terminal_evidence() -> None:
    text = _chat_contract_text()

    assert "A final PASS claim requires all of the following" in text
    assert "required work passed" in text
    assert "required gates passed or were honestly marked not run/not required" in text
    assert "evidence exists and matches the claim" in text
    assert "no earlier required inner FAIL was overwritten" in text
    assert "the final summary is rendered through the canonical renderer route" in text
    assert "A chat-only structured summary is not enough for terminal-directed work." in text


def test_final_summary_contract_preserves_no_legacy_fallback_and_remote_log_lookup() -> None:
    text = _summary_contract_text()

    assert "No legacy handwritten summary fallback" in text
    assert "./ns summary" in text
    assert "agentic_project_kit.run_summary_renderer" in text
    assert "Remote log lookup rule" in text
    assert "direct fetch of the named path at the expected branch or `main`" in text
    assert "terminal_log_remote" in text
    assert "terminal_log_local" in text
    assert "command_report" in text


def test_compiled_context_matches_chat_communication_contract() -> None:
    context = _compiled_context()

    assert "docs/governance/CHAT_COMMUNICATION_CONTRACT.md" in context["mandatory_successor_chat_sources"]
    assert "docs/governance/FINAL_SUMMARY_CONTRACT.md" in context["mandatory_successor_chat_sources"]
    hard_rules = {item["id"]: item["rule"] for item in context["hard_rules"]}
    assert "chat-communication-contract" in hard_rules
    assert "d/f/w/paste-output/stop" in hard_rules["chat-communication-contract"]
    assert "verify outcomes from evidence" in hard_rules["chat-communication-contract"]
    communication_rules = context["communication_rules"]
    assert communication_rules["d"] == "local block appears finished; inspect evidence before treating as success"
    assert communication_rules["f"] == "failure reported; inspect or upload evidence before asking for pasted output"
    assert communication_rules["w"] == "continue within current governance and evidence rules"
    assert communication_rules["paste-output"] == "manual paste only when repo-backed or local evidence is unavailable or unusable"
    assert communication_rules["stop"] == "no further mutation or terminal instructions"
