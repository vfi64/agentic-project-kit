import json
from pathlib import Path


def test_patch_transfer_request_schema_exists_and_blocks_fragile_patch_style() -> None:
    schema = json.loads(Path(".agentic/transfer/schemas/patch_transfer_request.schema.json").read_text(encoding="utf-8"))

    assert schema["properties"]["kind"]["const"] == "llm_to_local_transfer_request"
    assert schema["properties"]["message_kind"]["const"] == "patch_transfer_request"

    policy = schema["properties"]["patch_policy"]["properties"]
    assert policy["no_heredoc"]["const"] is True
    assert policy["no_inline_multiline_shell"]["const"] is True
    assert policy["write_canonical_next_command_only"]["const"] is True
    assert policy["require_repo_status_before_and_after"]["const"] is True


def test_handoff_required_sources_include_patch_transfer_schema() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    assert ".agentic/transfer/schemas/handoff_request.schema.json" in text
    assert ".agentic/transfer/schemas/patch_transfer_request.schema.json" in text
