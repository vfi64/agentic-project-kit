from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import (
    JSON_PATH,
    MD_PATH,
    PACKAGE_JSON_PATH,
    evaluate_command_manifest,
    load_manifest,
)
from agentic_project_kit.command_authority_audit import evaluate_command_authority
from agentic_project_kit.chat_entrypoint_contract import (
    command_manifest_ack_line,
    command_reference_prompt_block,
    mandatory_entrypoint_block,
)


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
    result = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)

    manifest = load_manifest(Path(".").resolve())
    sha = manifest["meta"]["manifest_sha"]
    prompt_text = data.get("prompt_text", "")
    assert command_manifest_ack_line(manifest) in prompt_text
    assert f"manifest_sha: {sha}" in prompt_text
    assert "agentic-kit command-for" in prompt_text
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
    assert "COMMAND_MANIFEST_ACK" in successor_prompt


def test_chat_refresher_renders_six_line_mode_blocks() -> None:
    manifest = load_manifest(Path(".").resolve())
    sha = manifest["meta"]["manifest_sha"]

    expected_mode_lines = {
        "copy-paste": "your reply will be linted before execution",
        "remote": "read the manifest file first, it is the single source",
        "file-transfer": "the carrier header pins the manifest sha",
    }
    for mode, mode_line in expected_mode_lines.items():
        result = CliRunner().invoke(app, ["chat", "refresher", "--mode", mode])

        assert result.exit_code == 0, result.output
        lines = result.output.strip().splitlines()
        assert len(lines) == 6
        assert lines[0] == f"COMMAND_MANIFEST_ACK {sha}"
        assert "docs/reference/agentic-kit-commands.json" in lines[1]
        assert "agentic-kit command-for" in lines[2]
        assert "raw git/gh commands" in lines[3]
        assert mode_line in lines[4]


def test_chat_session_start_inlines_all_manifest_commands() -> None:
    manifest = load_manifest(Path(".").resolve())
    result = CliRunner().invoke(app, ["chat", "session-start", "--mode", "copy-paste"])

    assert result.exit_code == 0, result.output
    command_lines = [line for line in result.output.splitlines() if line.startswith("agentic-kit ")]
    assert len(command_lines) == len(manifest["commands"])
    assert "agentic-kit command-for" in result.output
    command_safety = {command["qualified_name"]: command["safety"] for command in manifest["commands"]}
    assert command_safety["agentic-kit chat refresher"] == "READ_ONLY"
    assert command_safety["agentic-kit chat session-start"] == "READ_ONLY"


def test_agents_entrypoint_block_matches_manifest_sha() -> None:
    manifest = load_manifest(Path(".").resolve())
    text = Path("AGENTS.md").read_text(encoding="utf-8")

    assert mandatory_entrypoint_block(manifest) in text


def test_command_authority_audit_passes_for_current_chat_surfaces() -> None:
    audit = evaluate_command_authority(Path(".").resolve())

    assert audit.ok, audit.as_dict()


def test_command_authority_audit_blocks_missing_start_surface_terms(tmp_path: Path) -> None:
    manifest = load_manifest(Path(".").resolve())
    for source in (JSON_PATH, MD_PATH):
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    (tmp_path / "AGENTS.md").write_text(mandatory_entrypoint_block(manifest) + "\n", encoding="utf-8")
    for rel in (
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        "docs/reports/handoff-packages/latest/successor_prompt.md",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(command_reference_prompt_block(tmp_path), encoding="utf-8")
    (tmp_path / "docs/handoff/START_NEW_CHAT_PROMPT.md").write_text("stale prompt\n", encoding="utf-8")
    contract = {
        "command_reference": {
            "ack": command_manifest_ack_line(manifest),
            "json": "docs/reference/agentic-kit-commands.json",
            "manifest_sha": manifest["meta"]["manifest_sha"],
            "markdown": "docs/reference/AGENTIC_KIT_COMMANDS.md",
            "must_not_reconstruct_commands_from_memory": True,
            "source_hashes": {
                "docs/reference/agentic-kit-commands.json": "sha",
                "docs/reference/AGENTIC_KIT_COMMANDS.md": "sha",
            },
        }
    }
    contract_path = tmp_path / "docs/reports/handoff-packages/latest/execution_contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    audit = evaluate_command_authority(tmp_path)

    assert not audit.ok
    assert any(
        finding.code == "COMMAND_AUTHORITY_TERM_MISSING"
        and finding.path == "docs/handoff/START_NEW_CHAT_PROMPT.md"
        for finding in audit.findings
    )


def test_workspace_initial_prompt_contains_command_manifest_header(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])

    assert result.exit_code == 0, result.output
    prompt = (tmp_path / ".agentic/INITIAL_LLM_PROMPT.md").read_text(encoding="utf-8")
    assert "COMMAND_MANIFEST_ACK" in prompt
    assert "agentic-kit command-for" in prompt
    assert "manifest_sha:" in prompt


def test_sync_entrypoints_repairs_stale_manifest_sha_and_agents_block(tmp_path: Path) -> None:
    reference_root = tmp_path / JSON_PATH.parent
    reference_root.mkdir(parents=True)
    shutil.copy2(JSON_PATH, tmp_path / JSON_PATH)
    shutil.copy2(MD_PATH, tmp_path / MD_PATH)
    (tmp_path / "AGENTS.md").write_text(
        "<!-- command-manifest-entrypoint:start -->\n"
        "MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json "
        "(manifest_sha: stale). Every reply containing commands MUST start with: "
        "COMMAND_MANIFEST_ACK stale. Consult `agentic-kit command-for` before proposing commands.\n"
        "<!-- command-manifest-entrypoint:end -->\n",
        encoding="utf-8",
    )
    start_prompt = tmp_path / "docs/handoff/START_NEW_CHAT_PROMPT.md"
    start_prompt.parent.mkdir(parents=True)
    start_prompt.write_text(
        "# Start New Chat Prompt\n\n"
        "Command manifest entrypoint:\n"
        "- MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json "
        "(manifest_sha: stale). Every reply containing commands MUST start with: "
        "COMMAND_MANIFEST_ACK stale. Consult `agentic-kit command-for` before proposing commands.\n"
        "- Before proposing ANY command run/consult `agentic-kit command-for` and choose the most specific available Kit workflow command.\n"
        "- raw git/gh commands with a mapped wrapper are rejected by instruction lint.\n\n"
        "Command reference contract:\n"
        "- Read `docs/reference/agentic-kit-commands.json` before composing agentic-kit commands.\n"
        "- Read `docs/reference/AGENTIC_KIT_COMMANDS.md` before composing agentic-kit commands.\n"
        "- `must_not_reconstruct_commands_from_memory: true`.\n"
        "- Treat `source_hashes` as freshness evidence.\n"
        "source_hashes:\n"
        "- docs/reference/AGENTIC_KIT_COMMANDS.md: stalehash\n"
        "- docs/reference/agentic-kit-commands.json: stalehash\n\n"
        "## Tail\nkeep this paragraph\n",
        encoding="utf-8",
    )
    data = json.loads((tmp_path / JSON_PATH).read_text(encoding="utf-8"))
    data["meta"]["manifest_sha"] = "stale"
    (tmp_path / JSON_PATH).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    stale_audit = evaluate_command_manifest(tmp_path)
    assert not stale_audit.ok
    assert {finding.code for finding in stale_audit.findings} >= {
        "MANIFEST_SHA_MISMATCH",
        "ENTRYPOINT_MANIFEST_SHA_MISMATCH",
    }

    result = CliRunner().invoke(
        app,
        ["commands", "sync-entrypoints", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["changed"] is True
    assert evaluate_command_manifest(tmp_path).ok
    prompt_text = start_prompt.read_text(encoding="utf-8")
    assert command_manifest_ack_line(load_manifest(tmp_path)) in prompt_text
    assert "COMMAND_MANIFEST_ACK stale" not in prompt_text
    assert prompt_text.count("Command manifest entrypoint:") == 1
    assert "## Tail\nkeep this paragraph" in prompt_text
    assert not (tmp_path / PACKAGE_JSON_PATH).exists()

    idempotent = CliRunner().invoke(
        app,
        ["commands", "sync-entrypoints", "--root", str(tmp_path), "--json"],
    )
    assert idempotent.exit_code == 0, idempotent.output
    assert json.loads(idempotent.output)["changed"] is False
