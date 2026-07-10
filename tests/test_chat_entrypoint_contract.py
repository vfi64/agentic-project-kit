from __future__ import annotations

import json
from pathlib import Path


def test_successor_execution_contract_carries_command_reference_identity() -> None:
    contract_path = Path("docs/reports/handoff-packages/latest/execution_contract.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    context = contract.get("llm_execution_context") or contract
    command_reference = context.get("command_reference")
    assert isinstance(command_reference, dict)

    assert command_reference.get("json") == "docs/reference/agentic-kit-commands.json"
    assert command_reference.get("markdown") == "docs/reference/AGENTIC_KIT_COMMANDS.md"
    assert command_reference.get("must_not_reconstruct_commands_from_memory") is True

    source_hashes = context.get("source_hashes")
    assert isinstance(source_hashes, dict)
    assert "docs/reference/agentic-kit-commands.json" in source_hashes
    assert "docs/reference/AGENTIC_KIT_COMMANDS.md" in source_hashes


def test_gui_initial_llm_prompt_mentions_command_reference_and_hashes() -> None:
    from typer.testing import CliRunner

    from agentic_project_kit.cli import app

    result = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)

    prompt_text = data.get("prompt_text", "")
    assert "docs/reference/agentic-kit-commands.json" in prompt_text
    assert "docs/reference/AGENTIC_KIT_COMMANDS.md" in prompt_text
    assert "source_hashes" in prompt_text
    assert "must_not_reconstruct_commands_from_memory" in prompt_text


def test_chat_switch_complete_renders_command_reference_contract(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from agentic_project_kit.cli import app

    output_dir = tmp_path / "handoff-package"
    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "chat-switch-complete",
            "--output-dir",
            str(output_dir),
            "--no-update-canonical-prompts",
            "--json",
        ],
    )

    assert result.exit_code == 0

    execution_contract = json.loads((output_dir / "execution_contract.json").read_text(encoding="utf-8"))
    successor_prompt = (output_dir / "successor_prompt.md").read_text(encoding="utf-8")

    context = execution_contract.get("llm_execution_context") or execution_contract
    assert context["command_reference"]["json"] == "docs/reference/agentic-kit-commands.json"
    assert context["command_reference"]["markdown"] == "docs/reference/AGENTIC_KIT_COMMANDS.md"
    assert context["command_reference"]["must_not_reconstruct_commands_from_memory"] is True

    assert "docs/reference/agentic-kit-commands.json" in successor_prompt
    assert "docs/reference/AGENTIC_KIT_COMMANDS.md" in successor_prompt
    assert "must_not_reconstruct_commands_from_memory" in successor_prompt
