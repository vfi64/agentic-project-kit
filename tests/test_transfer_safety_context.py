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
        "docs/planning/PROJECT_DIRECTION.yaml",
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


def test_transfer_safety_header_loads_meta_command_preference_from_rule_files(tmp_path: Path):
    from agentic_project_kit.transfer_safety_context import build_transfer_safety_header

    safety = tmp_path / ".agentic" / "transfer_safety_rules.yaml"
    protocol = tmp_path / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml"
    safety.parent.mkdir(parents=True)
    protocol.parent.mkdir(parents=True)

    safety.write_text(
        "\n".join(
            [
                "canonical_transfer_files:",
                "  inbox: .agentic/transfer/inbox/next_command.py.txt",
                "  outbox: .agentic/transfer/outbox/last_result.txt",
                "transfer_priorities: []",
                "known_failure_classes: []",
                "preflight_rules: []",
                "post_patch_rules: []",
                "meta_command_preference:",
                "  priority: primary_path",
                "  preferred_commands:",
                "    work_start: agentic-kit work start",
                "  fallback_rule: Low-level commands require a reason.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    protocol.write_text(
        "\n".join(
            [
                "meta_command_preference:",
                "  preferred_entrypoints:",
                "    - agentic-kit release ready",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    header = build_transfer_safety_header(tmp_path)
    preference = header["meta_command_preference"]

    assert preference["source"] == "dynamic-from-rule-files"
    assert preference["status"] == "active"
    assert "agentic-kit work start" in preference["preferred_commands"]
    assert "agentic-kit release ready" in preference["preferred_commands"]
    assert preference["fallback_rule"] == "Low-level commands require a reason."


def test_transfer_safety_header_meta_preference_changes_with_rule_files(tmp_path: Path):
    from agentic_project_kit.transfer_safety_context import build_transfer_safety_header

    safety = tmp_path / ".agentic" / "transfer_safety_rules.yaml"
    protocol = tmp_path / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml"
    safety.parent.mkdir(parents=True)
    protocol.parent.mkdir(parents=True)

    base_rules = "\n".join(
        [
            "canonical_transfer_files:",
            "  inbox: .agentic/transfer/inbox/next_command.py.txt",
            "  outbox: .agentic/transfer/outbox/last_result.txt",
            "transfer_priorities: []",
            "known_failure_classes: []",
            "preflight_rules: []",
            "post_patch_rules: []",
            "meta_command_preference:",
            "  preferred_commands:",
        ]
    )
    protocol.write_text("meta_command_preference:\n  preferred_entrypoints: []\n", encoding="utf-8")

    safety.write_text(base_rules + "\n    work_start: agentic-kit work start\n", encoding="utf-8")
    first = build_transfer_safety_header(tmp_path)

    safety.write_text(base_rules + "\n    work_check: agentic-kit work check\n", encoding="utf-8")
    second = build_transfer_safety_header(tmp_path)

    assert "agentic-kit work start" in first["meta_command_preference"]["preferred_commands"]
    assert "agentic-kit work check" in second["meta_command_preference"]["preferred_commands"]
    assert "agentic-kit work start" not in second["meta_command_preference"]["preferred_commands"]


def test_local_to_llm_log_header_contains_dynamic_meta_policy(tmp_path: Path):
    from agentic_project_kit.transfer_safety_context import render_local_to_llm_log_header

    safety = tmp_path / ".agentic" / "transfer_safety_rules.yaml"
    protocol = tmp_path / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml"
    safety.parent.mkdir(parents=True)
    protocol.parent.mkdir(parents=True)

    safety.write_text(
        "\n".join(
            [
                "canonical_transfer_files:",
                "  inbox: .agentic/transfer/inbox/next_command.py.txt",
                "  outbox: .agentic/transfer/outbox/last_result.txt",
                "transfer_priorities: []",
                "known_failure_classes: []",
                "preflight_rules: []",
                "post_patch_rules: []",
                "meta_command_preference:",
                "  priority: primary_path",
                "  preferred_commands:",
                "    work_start: agentic-kit work start",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    protocol.write_text(
        "meta_command_preference:\n  preferred_entrypoints:\n    - agentic-kit release ready\n",
        encoding="utf-8",
    )

    rendered = render_local_to_llm_log_header(tmp_path, log_path="tmp/example.log")

    assert "LOCAL_TO_LLM_COPY_PASTE_LOG_HEADER" in rendered
    assert "dynamic-from-rule-files" in rendered
    assert "tmp/example.log" in rendered
    assert "meta_command_preference" in rendered
    assert "agentic-kit work start" in rendered
    assert "agentic-kit release ready" in rendered


def test_local_to_llm_log_upload_hint_is_explicit():
    from agentic_project_kit.transfer_safety_context import render_local_to_llm_log_upload_hint

    hint = render_local_to_llm_log_upload_hint("tmp/example.log", return_code=1)

    assert "ACTION REQUIRED FOR COPY-AND-PASTE COMMUNICATION" in hint
    assert "LOG  =  tmp/example.log" in hint
    assert "RC   =  1" in hint
    assert "RC=1   error / command failed; inspect the log before continuing" in hint


def test_transfer_safety_header_contains_python_only_work_order_contract(tmp_path: Path):
    from agentic_project_kit.transfer_safety_context import build_transfer_safety_header

    safety = tmp_path / ".agentic" / "transfer_safety_rules.yaml"
    protocol = tmp_path / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml"
    safety.parent.mkdir(parents=True)
    protocol.parent.mkdir(parents=True)
    safety.write_text(
        "\n".join(
            [
                "canonical_transfer_files:",
                "  inbox: .agentic/transfer/inbox/next_command.py.txt",
                "  outbox: .agentic/transfer/outbox/last_result.txt",
                "transfer_priorities: []",
                "known_failure_classes: []",
                "preflight_rules: []",
                "post_patch_rules: []",
                "llm_work_order_contract:",
                "  required_format: python_script",
                "  shell_usage: outer_logging_wrapper_only",
                "meta_command_preference:",
                "  preferred_commands:",
                "    work_start: agentic-kit work start",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    protocol.write_text(
        "\n".join(
            [
                "llm_work_order_contract:",
                "  required_format: python_script",
                "  transfer_file:",
                "    canonical_inbox: .agentic/transfer/inbox/next_command.py.txt",
                "    shell_commands_allowed: false",
                "meta_command_preference:",
                "  preferred_entrypoints: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    header = build_transfer_safety_header(tmp_path)
    contract = header["llm_work_order_contract"]

    assert contract["source"] == "dynamic-from-rule-files"
    assert contract["status"] == "active"
    assert contract["required_format"] == "python_script"
    assert contract["transfer_file"]["canonical_inbox"].endswith("next_command.py.txt")
    assert contract["transfer_file"]["shell_commands_allowed"] is False
