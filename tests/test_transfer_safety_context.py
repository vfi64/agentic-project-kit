from pathlib import Path

from agentic_project_kit.transfer_safety_context import build_transfer_safety_header
from agentic_project_kit.transfer_safety_context import write_transfer_outbox


def test_transfer_safety_header_contains_known_failure_classes() -> None:
    header = build_transfer_safety_header(Path("."))

    assert header["derived_projection"] is True
    assert header["canonical_transfer_files"]["llm_to_local"] == ".agentic/transfer/inbox/next_command.py.txt"
    assert header["canonical_transfer_files"]["local_to_llm"] == ".agentic/transfer/outbox/last_result.txt"
    assert "raw_newline_in_python_string_literals" in header["known_failure_classes"]
    assert "python_transfer_txt_suffix_not_syntax_validated" in header["known_failure_classes"]
    assert "expected_branch_must_match" in header["preflight_rules"]
    assert "changed_python_files_must_compile_before_cli_import" in header["post_patch_rules"]


def test_transfer_outbox_is_json_with_safety_header(tmp_path: Path) -> None:
    for relative in (
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_preservation.yaml",
        "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md",
        "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    ):
        source = Path(relative)
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    outbox = write_transfer_outbox(tmp_path, {"final_signal": "d", "next_action": "continue"})
    text = outbox.read_text(encoding="utf-8")

    assert '"kind": "local_to_llm_last_result"' in text
    assert '"safety_header"' in text
    assert '"raw_newline_in_python_string_literals"' in text
    assert '"last_result"' in text
