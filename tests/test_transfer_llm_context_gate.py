from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_safety_context import build_local_to_llm_payload


SOURCE_FILES = (
    ".agentic/compiled_agent_context.yaml",
    ".agentic/transfer_safety_rules.yaml",
    ".agentic/transfer/one_command_transfer_protocol.yaml",
    "docs/reference/agentic-kit-commands.json",
    "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_preservation.yaml",
    "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
)


def _copy_context_sources(tmp_path: Path) -> None:
    for relative in SOURCE_FILES:
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _write_fresh_context_reports(tmp_path: Path) -> None:
    payload = build_local_to_llm_payload(tmp_path, {"final_signal": "d", "next_action": "continue"})
    outbox = tmp_path / ".agentic/transfer/outbox/last_result.txt"
    latest = tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    latest.parent.mkdir(parents=True, exist_ok=True)
    outbox.write_text(json.dumps(payload), encoding="utf-8")
    latest.write_text(json.dumps(payload), encoding="utf-8")


def test_require_fresh_llm_context_blocks_when_reports_missing(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "require-fresh-llm-context"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout
    assert "missing" in result.stdout


def test_require_fresh_llm_context_passes_with_generated_reports(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    _write_fresh_context_reports(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "require-fresh-llm-context", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["result_status"] == "PASS"
    assert data["valid_contexts"]


def test_transfer_continue_blocks_without_fresh_llm_context(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "continue"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout


def test_transfer_continue_skip_llm_context_gate_reaches_continue_wrapper(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "continue", "--skip-llm-context-gate", "--json"])

    assert result.exit_code != 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" not in result.stdout
