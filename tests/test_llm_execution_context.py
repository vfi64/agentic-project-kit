from __future__ import annotations

from pathlib import Path

import json

from agentic_project_kit.llm_execution_context import build_llm_execution_context


def test_llm_execution_context_is_generated_from_current_repo_sources() -> None:
    context = build_llm_execution_context(".")

    assert context["kind"] == "llm_execution_context"
    assert context["generated_from_current_repo"] is True
    assert context["projection_only_not_source_of_truth"] is True
    assert "docs/reference/agentic-kit-commands.json" in context["source_files"]
    assert "docs/reference/AGENTIC_KIT_COMMANDS.md" in context["source_files"]
    assert context["command_reference"]["command_count"] > 0
    assert context["command_reference"]["must_not_reconstruct_commands_from_memory"] is True

    wrappers = {
        item["qualified_name"]: item
        for item in context["command_reference"]["important_wrappers"]
    }
    for name in (
        "agentic-kit transfer pr-create-complete",
        "agentic-kit transfer pr-complete",
        "agentic-kit transfer post-merge-complete",
        "agentic-kit transfer command-reference-refresh",
    ):
        assert wrappers[name]["present"] is True

    assert context["execution_policy"]["wrapper_first"] is True
    assert context["execution_policy"]["post_merge_complete_required_after_merge"] is True


def test_llm_execution_context_records_placeholder_and_terminal_resilience_policy() -> None:
    context = build_llm_execution_context(".")

    assert "agentic-kit transfer pr-create-complete --post-merge-complete" in {
        item["qualified_name"] for item in context["command_reference"]["important_wrappers"]
    }

    lifecycle = context["canonical_lifecycle"]
    assert lifecycle["shell_placeholder_policy"]["no_angle_bracket_placeholders_in_executable_blocks"] is True
    assert "<PR_NUMMER>" not in str(lifecycle)
    assert "<PR_NUMBER>" not in str(lifecycle)

    assert context["running_chat_refresh_contract"]["refresh_required_for_running_chats"] is True
    assert context["shell_placeholder_policy"]["no_angle_bracket_placeholders_in_executable_blocks"] is True
    assert context["terminal_resilience"]["avoid_process_ended_terminal_dead_end"] is True
    assert context["patch_generation_policy"]["avoid_heredoc_quote_escape_drift"] is True
    assert context["context_quality"]["source_hashes_complete"] is True

def test_llm_execution_context_records_transfer_payload_and_command_integration_governance() -> None:
    context = build_llm_execution_context(".")

    transfer_policy = context["llm_to_local_transfer_policy"]
    assert transfer_policy["payload_file"] == ".agentic/transfer/inbox/next_command.py.txt"
    assert transfer_policy["payload_language"] == "python"
    assert transfer_policy["payload_suffix"] == ".py.txt"
    assert any("raw gh" in rule for rule in transfer_policy["rules"])
    assert any("agentic-kit wrappers" in rule for rule in transfer_policy["rules"])

    governance = context["command_integration_governance"]
    assert governance["normative"] is True
    assert "new agentic-kit commands" in governance["applies_to"]
    assert "changed agentic-kit commands" in governance["applies_to"]
    assert "LLM execution context visibility" in governance["required_review"]
    assert "fresh LLM context gate requirement or explicit non-gated exception" in governance["required_review"]

def test_llm_execution_context_governance_mentions_refresh_and_post_merge_context_carriers() -> None:
    context = build_llm_execution_context(".")
    governance_text = json.dumps(context["command_integration_governance"], ensure_ascii=False)

    assert "handoff and transfer-context visibility" in governance_text
    assert "LLM execution context visibility" in governance_text
    assert "fresh LLM context gate requirement or explicit non-gated exception" in governance_text

def test_llm_execution_context_encodes_pr_handoff_lifecycle_order(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path(".agentic/transfer").mkdir(parents=True)
    Path("docs/reference").mkdir(parents=True)
    Path(".agentic/compiled_agent_context.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    Path(".agentic/transfer_safety_rules.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    Path(".agentic/transfer/one_command_transfer_protocol.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    Path("docs/reference/agentic-kit-commands.json").write_text(
        '{"schema_version": 1, "commands": []}\n',
        encoding="utf-8",
    )
    Path("docs/reference/AGENTIC_KIT_COMMANDS.md").write_text("# Commands\n", encoding="utf-8")

    from agentic_project_kit.llm_execution_context import build_llm_execution_context

    lifecycle = build_llm_execution_context(tmp_path)["canonical_lifecycle"]

    assert lifecycle["feature_branch_pre_pr_gate"] == "agentic-kit transfer repo-status"
    assert lifecycle["forbidden_feature_branch_pre_pr_gate"] == "agentic-kit transfer post-merge-check"
    assert lifecycle["post_merge_checks_belong_to_main"] is True
    assert lifecycle["post_merge_check_after_merge_only"] is True
    assert lifecycle["do_not_use_stale_prompt_text_as_handoff_source"] is True
    assert lifecycle["fresh_llm_context_before_pr"] == [
        "./.venv/bin/agentic-kit transfer prepare-successor-handoff --render-prompt",
        "./.venv/bin/agentic-kit transfer publish-last-report",
        "./.venv/bin/agentic-kit transfer require-fresh-llm-context --json",
    ]

