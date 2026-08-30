from __future__ import annotations

from pathlib import Path

from agentic_project_kit.cli_commands import transfer_pr_create_flow
from agentic_project_kit.volatile_paths import (
    RULE_ACK_CURRENT_PATH,
    TRANSFER_OUTBOX_LAST_RESULT_PATH,
)


PR_CREATE_FLOW = Path("src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py")


def _source() -> str:
    return PR_CREATE_FLOW.read_text(encoding="utf-8")


def test_pr_create_complete_has_automatic_preflight_helper() -> None:
    text = _source()

    assert "def _auto_preflight_pr_create_complete(" in text
    assert "rules acknowledge" in text or "rules_acknowledge" in text
    assert "refresh-llm-context-carriers" in text or "refresh_llm_context_carriers" in text
    assert "require-fresh-llm-context" in text or "require_fresh_llm_context" in text
    assert "restore-known-volatile" in text or "restore_known_volatile" in text
    assert "TRANSFER_OUTBOX_LAST_RESULT_PATH" in text
    assert "RULE_ACK_DIRECTORY_PATH" in text


def test_pr_create_complete_runs_auto_preflight_before_gate_and_github_mutation() -> None:
    text = _source()

    command_pos = text.index('def pr_create_complete_command(')
    auto_preflight_pos = text.index("_auto_preflight_pr_create_complete(", command_pos)
    fresh_gate_pos = text.index("_require_fresh_llm_context_or_exit", command_pos)
    github_create_pos = text.index('"pr-create"', command_pos)

    assert command_pos < auto_preflight_pos < fresh_gate_pos < github_create_pos



def test_pr_create_complete_preflight_does_not_shadow_fresh_context_gate() -> None:
    text = _source()

    helper_pos = text.index("def _auto_preflight_pr_create_complete(")
    helper_text = text[helper_pos : text.index('@transfer_app.command("pr-create")')]

    assert '"rules_acknowledge"' in helper_text
    assert '"git_status"' in helper_text
    assert "allow_nonzero=True" in helper_text
    assert "status_result.returncode != 0" in helper_text
    assert 'if not (root / ".git").exists()' in helper_text


def test_pr_create_complete_preflight_has_unexpected_dirt_blocker() -> None:
    text = _source()

    helper_pos = text.index("def _auto_preflight_pr_create_complete(")
    helper_text = text[helper_pos : text.index('@transfer_app.command("pr-create")')]

    assert "unexpected_dirt" in helper_text
    assert "_known_volatile_transfer_paths" in helper_text
    assert "RULE_ACK_DIRECTORY_PATH" in helper_text
    volatile_paths = transfer_pr_create_flow._known_volatile_transfer_paths(Path("."))
    assert RULE_ACK_CURRENT_PATH in volatile_paths
    assert TRANSFER_OUTBOX_LAST_RESULT_PATH in volatile_paths
    assert "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json" in volatile_paths
    assert "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log" in volatile_paths
