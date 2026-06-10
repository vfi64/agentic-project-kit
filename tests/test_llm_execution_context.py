from __future__ import annotations

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
