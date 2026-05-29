from __future__ import annotations

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_refresh import (
    COMMUNICATION_RULES_OUTPUT,
    HANDOFF_RULES_OUTPUT,
    refresh_communication_rules,
    refresh_handoff_rules,
)


def write_sources(root):
    paths = [
        "docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        ".agentic/compiled_agent_context.yaml",
        ".agentic/handoff_state.yaml",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    ]
    for rel in paths:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"content for {rel}\n", encoding="utf-8")


def test_refresh_communication_rules_writes_generated_file(tmp_path):
    write_sources(tmp_path)

    result = refresh_communication_rules(tmp_path)

    assert result.output_path == str(COMMUNICATION_RULES_OUTPUT)
    assert result.next_reply == "d2"
    output = tmp_path / COMMUNICATION_RULES_OUTPUT
    text = output.read_text(encoding="utf-8")
    assert "Next reply trigger: `d2`" in text
    assert "docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md" in text


def test_refresh_handoff_rules_writes_generated_file(tmp_path):
    write_sources(tmp_path)

    result = refresh_handoff_rules(tmp_path)

    assert result.output_path == str(HANDOFF_RULES_OUTPUT)
    assert result.next_reply == "d3"
    output = tmp_path / HANDOFF_RULES_OUTPUT
    text = output.read_text(encoding="utf-8")
    assert "Next reply trigger: `d3`" in text
    assert "docs/handoff/CURRENT_HANDOFF.md" in text


def test_rules_cli_communication_refresh(tmp_path):
    write_sources(tmp_path)

    result = CliRunner().invoke(app, ["rules", "communication-refresh", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "RULE_REFRESH_RESULT" in result.output
    assert "next_reply=d2" in result.output
    assert (tmp_path / COMMUNICATION_RULES_OUTPUT).exists()


def test_rules_cli_handoff_refresh_json(tmp_path):
    write_sources(tmp_path)

    result = CliRunner().invoke(app, ["rules", "handoff-refresh", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    assert '"next_reply": "d3"' in result.output
    assert (tmp_path / HANDOFF_RULES_OUTPUT).exists()
