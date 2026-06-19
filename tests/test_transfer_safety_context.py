from pathlib import Path
import json

from agentic_project_kit.transfer_safety_context import build_transfer_safety_header
from agentic_project_kit.transfer_safety_context import write_transfer_outbox


def test_transfer_safety_header_contains_known_failure_classes() -> None:
    header = build_transfer_safety_header(Path("."))

    assert header["derived_projection"] is True
    assert header["canonical_transfer_files"]["llm_to_local"] == ".agentic/transfer/inbox/next_command.py.txt"
    assert header["canonical_transfer_files"]["local_to_llm"] == ".agentic/transfer/outbox/last_result.txt"
    assert header["canonical_transfer_files"]["transfer_order"] == ".agentic/transfer/inbox/current.yaml"
    assert "raw_newline_in_python_string_literals" in header["known_failure_classes"]
    assert "python_transfer_txt_suffix_not_syntax_validated" in header["known_failure_classes"]
    assert "expected_branch_must_match" in header["preflight_rules"]
    assert "changed_python_files_must_compile_before_cli_import" in header["post_patch_rules"]


def test_transfer_outbox_is_json_with_safety_header(tmp_path: Path) -> None:
    for relative in (
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_preservation.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml",
        "docs/planning/project_direction.yaml",
    ):
        source = Path(relative)
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    outbox = write_transfer_outbox(tmp_path, {"final_signal": "d", "next_action": "continue"})
    text = outbox.read_text(encoding="utf-8")

    assert '"kind": "local_to_llm_last_result"' in text
    assert '"safety_header"' in text
    assert '"canonical_runner"' in text
    assert '"decision_tree"' in text
    assert '"raw_newline_in_python_string_literals"' in text
    assert '"last_result"' in text


def test_transfer_safety_header_contains_cli_usage_and_terminal_rules() -> None:
    header = build_transfer_safety_header(Path("."))

    cli_usage = header["canonical_cli_usage"]
    assert "--head" in cli_usage["transfer_pr_create"]["required_options"]
    assert "--run-log" in cli_usage["evidence_finalize_log"]["required_options"]
    assert "--remote-log" in cli_usage["evidence_finalize_log"]["required_options"]
    assert "agentic-kit evidence inspect --run-log <path>" in cli_usage["evidence_inspect"]["invalid_forms"]
    assert "--after-pr" in cli_usage["transfer_admin_refresh_pr"]["required_options"]
    assert cli_usage["rules_acknowledge_after_commit"]["trigger"] == "required after every commit because repo_head changes"

    terminal_rules = header["terminal_block_rules"]
    assert "Use ./.venv/bin/python instead of python" in terminal_rules["preferred"]
    assert "commands that can leave zsh in quote> or dquote>" in terminal_rules["avoid"]
    assert "terminal_quote_prompt_hang" in header["known_failure_classes"]


def test_transfer_rules_define_remote_next_as_only_normal_user_command() -> None:
    header = build_transfer_safety_header(Path("."))

    assert header["canonical_runner"]["command"] == ["./.venv/bin/agentic-kit", "transfer", "remote-next"]
    assert header["canonical_runner"]["direct_python_execution_allowed"] == "recovery_only"
    assert header["transfer_lanes"]["control_lane"]["runner"] == "./.venv/bin/agentic-kit transfer remote-next"
    assert header["transfer_lanes"]["python_payload_lane"]["direct_user_execution"] == "forbidden_except_recovery"
    assert header["canonical_cli_usage"]["canonical_one_command_transfer"]["command"] == (
        "./.venv/bin/agentic-kit transfer remote-next"
    )
    assert "direct next_command.py.txt execution by the user" in header["canonical_cli_usage"]["canonical_one_command_transfer"]["forbidden_normal_replacements"]


def test_transfer_rules_require_remote_report_after_g_before_planning() -> None:
    header = build_transfer_safety_header(Path("."))

    after_g = header["decision_tree"]["user_says_g_or_go"]
    assert after_g["action"] == "read_latest_remote_transfer_report_first"
    assert after_g["forbidden"] == "continue_from_chat_memory"
    assert header["decision_tree"]["remote_report_missing_or_stale"]["action"] == "treat_as_transfer_uplink_problem"
    assert header["decision_tree"]["local_transfer_needed"]["action"] == "instruct_user_to_run_remote_next"

def test_transfer_outbox_payload_includes_llm_execution_context(tmp_path: Path) -> None:
    from agentic_project_kit.transfer_safety_context import write_transfer_outbox

    for relative in (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ):
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    outbox = write_transfer_outbox(tmp_path, {"final_signal": "d", "next_action": "continue"})
    data = json.loads(outbox.read_text(encoding="utf-8"))

    assert data["llm_execution_context"]["kind"] == "llm_execution_context"
    assert data["llm_execution_context"]["command_reference"]["must_not_reconstruct_commands_from_memory"] is True
