from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state


def test_handoff_prompt_contains_required_sections_and_active_rules_only():
    data = load_handoff_state()
    prompt = render_handoff_prompt(data)
    assert "## 1. Arbeitsumgebung" in prompt
    assert "## 2. Sicherer Stand" in prompt
    assert "## 6. Aktive Regeln" in prompt
    assert "no-copy-terminal-evidence" in prompt
    assert "manual-copy-terminal-by-default" not in prompt


def test_handoff_cli_commands():
    runner = CliRunner()
    check_result = runner.invoke(app, ["handoff", "check"])
    assert check_result.exit_code == 0
    assert "check passed" in check_result.output
    show_result = runner.invoke(app, ["handoff", "show"])
    assert show_result.exit_code == 0
    assert "agentic-project-kit" in show_result.output
    prompt_result = runner.invoke(app, ["handoff", "prompt"])
    assert prompt_result.exit_code == 0
    assert "Übergabeprompt" in prompt_result.output


def test_handoff_prompt_contains_successor_chat_bootstrap_sections() -> None:
    prompt = render_handoff_prompt(load_handoff_state())
    required_sections = [
        "## 1. Arbeitsumgebung",
        "## 4. Pflichtquellen vor jeder Mutation",
        "## 5. Kommunikations- und Summary-Regeln",
        "## 9. Letzte bekannte Fehler- und Driftmuster",
        "## 10. Verbotene Muster",
        "## 14. Arbeitsmodus für den Nachfolge-Chat",
    ]
    for section in required_sections:
        assert section in prompt


def test_handoff_prompt_lists_mandatory_rule_documents() -> None:
    prompt = render_handoff_prompt(load_handoff_state())
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
        assert source in prompt


def test_handoff_prompt_defines_communication_shortcuts_and_summary_vocabulary() -> None:
    prompt = render_handoff_prompt(load_handoff_state())
    for shortcut in ["d/D", "f/F", "w/W", "paste-output", "stop"]:
        assert shortcut in prompt
    for summary_line in [
        "WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND",
        "REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED",
        "NEXT_CHAT_REPLY: p|f|paste-output|continue|stop",
    ]:
        assert summary_line in prompt


def test_handoff_prompt_includes_forbidden_patterns() -> None:
    prompt = render_handoff_prompt(load_handoff_state())
    forbidden = [
        "mutating before reading the mandatory successor-chat sources",
        "treating d as proof of success",
        "using shell-only snippets as canonical cross-platform execution",
        "printing REMOTE_EVIDENCE: PENDING in a final summary",
    ]
    for item in forbidden:
        assert item in prompt
