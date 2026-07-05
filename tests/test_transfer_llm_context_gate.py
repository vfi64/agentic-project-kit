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
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/planning/PROJECT_DIRECTION.yaml",
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

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.refresh_llm_context_carriers",
        lambda root: (_ for _ in ()).throw(FileNotFoundError("missing context carriers")),
    )

    result = CliRunner().invoke(app, ["transfer", "continue"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout


def test_transfer_continue_skip_llm_context_gate_reaches_continue_wrapper(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "continue", "--skip-llm-context-gate", "--json"])

    assert result.exit_code != 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" not in result.stdout

def test_pr_complete_blocks_without_fresh_llm_context(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "pr-complete", "123"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout


def test_pr_create_complete_blocks_without_fresh_llm_context(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create-complete",
            "--title",
            "Demo",
            "--body",
            "Body",
        ],
    )

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout


def test_pr_merge_safe_blocks_without_fresh_llm_context(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "pr-merge-safe", "123"])

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout

def test_pr_create_blocks_without_fresh_llm_context(tmp_path, monkeypatch):
    _copy_context_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create",
            "--title",
            "Demo",
            "--head",
            "feature/demo",
        ],
    )

    assert result.exit_code == 2
    assert "TRANSFER_REQUIRE_FRESH_LLM_CONTEXT" in result.stdout

def test_require_fresh_llm_context_passes_with_valid_outbox_and_stale_published_report(tmp_path, monkeypatch):
    from agentic_project_kit.cli import app
    from agentic_project_kit.transfer_safety_context import write_transfer_outbox
    from typer.testing import CliRunner

    monkeypatch.chdir(tmp_path)

    (tmp_path / ".agentic/transfer_safety_rules.yaml").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".agentic/transfer_safety_rules.yaml").write_text(
        """
canonical_transfer_files:
  inbox: .agentic/transfer/inbox/next_command.py.txt
  outbox: .agentic/transfer/outbox/last_result.txt
running_chat_refresh_contract:
  refresh_required_for_running_chats: true
transfer_priorities: {}
known_failure_classes: {}
preflight_rules: {}
post_patch_rules: {}
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / ".agentic/transfer/one_command_transfer_protocol.yaml").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".agentic/transfer/one_command_transfer_protocol.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs/DOCUMENTATION_REGISTRY.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    (tmp_path / "docs/planning").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("schema_version: 1\n", encoding="utf-8")

    write_transfer_outbox(tmp_path, {"result_status": "PASS", "final_signal": "d"})

    stale_report = tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    stale_report.parent.mkdir(parents=True, exist_ok=True)
    stale_report.write_text(
        """
{
  "schema_version": 1,
  "llm_execution_context": {
    "source_hashes": {
      ".agentic/transfer_safety_rules.yaml": "stale"
    }
  }
}
""".lstrip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["transfer", "require-fresh-llm-context", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["result_status"] == "PASS"
    assert "outbox" in data["valid_contexts"]
    assert "latest_handoff_report" not in data["valid_contexts"]
    assert "latest_handoff_report_stale_or_not_fresh" in data["blockers"]


def test_require_fresh_llm_context_can_warn_on_clean_post_merge_carrier_staleness(monkeypatch):
    from agentic_project_kit.cli_commands import transfer as transfer_cli

    def fake_evaluate(root, *, max_age_minutes, allow_clean_post_merge_carrier_staleness=False):
        payload = {
            "schema_version": 1,
            "kind": "transfer_require_fresh_llm_context_result",
            "action": "require-fresh-llm-context",
            "result_status": "WARN" if allow_clean_post_merge_carrier_staleness else "BLOCKED",
            "final_signal": "d" if allow_clean_post_merge_carrier_staleness else "f",
            "next_action": "warn",
            "max_age_minutes": max_age_minutes,
            "valid_contexts": [],
            "blockers": [
                "outbox_missing",
                "latest_handoff_report_source_hashes_mismatch",
                "latest_handoff_report_stale_or_not_fresh",
            ],
            "checked": {},
            "allow_clean_post_merge_carrier_staleness": allow_clean_post_merge_carrier_staleness,
            "clean_post_merge_carrier_staleness_allowed": allow_clean_post_merge_carrier_staleness,
        }
        return payload

    monkeypatch.setattr(transfer_cli, "_evaluate_llm_context_freshness", fake_evaluate)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "require-fresh-llm-context",
            "--allow-clean-post-merge-carrier-staleness",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "WARN"
    assert payload["clean_post_merge_carrier_staleness_allowed"] is True


def test_require_fresh_llm_context_strict_still_blocks_on_carrier_staleness(monkeypatch):
    from agentic_project_kit.cli_commands import transfer as transfer_cli

    def fake_evaluate(root, *, max_age_minutes, allow_clean_post_merge_carrier_staleness=False):
        return {
            "schema_version": 1,
            "kind": "transfer_require_fresh_llm_context_result",
            "action": "require-fresh-llm-context",
            "result_status": "BLOCKED",
            "final_signal": "f",
            "next_action": "blocked",
            "max_age_minutes": max_age_minutes,
            "valid_contexts": [],
            "blockers": ["outbox_missing"],
            "checked": {},
            "allow_clean_post_merge_carrier_staleness": allow_clean_post_merge_carrier_staleness,
            "clean_post_merge_carrier_staleness_allowed": False,
        }

    monkeypatch.setattr(transfer_cli, "_evaluate_llm_context_freshness", fake_evaluate)

    result = CliRunner().invoke(app, ["transfer", "require-fresh-llm-context", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
