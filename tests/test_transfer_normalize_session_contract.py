from pathlib import Path

from agentic_project_kit.volatile_paths import (
    KNOWN_VOLATILE_TRANSFER_PATHS,
    RULE_ACK_CURRENT_PATH,
    TRANSFER_INBOX_NEXT_COMMAND_PATH,
    TRANSFER_OUTBOX_LAST_RESULT_PATH,
)


def test_normalize_session_defaults_to_no_outbox_write() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer_handoff_flow.py").read_text(encoding="utf-8")
    start = text.index("def normalize_session(")
    end = text.index("def _emit_successor_package(")
    section = text[start:end]

    assert "--write-outbox/--no-write-outbox" in section
    assert "write_outbox: bool = typer.Option(\n        False" in section
    assert "if write_outbox:" in section
    assert "payload[\"outbox_written\"] = None" in section
    assert section.count("volatile_repair_result = None") == 1


def test_normalize_session_rule_ack_accepts_rule_ack_sha_prefix() -> None:
    from pathlib import Path

    text = Path("src/agentic_project_kit/cli_commands/transfer_handoff_flow.py").read_text(encoding="utf-8")

    assert 'ack_data.get("repo_head") == head[:7]' not in text
    assert "head.startswith(ack_head)" in text


def test_normalize_session_known_volatile_paths_include_canonical_inbox() -> None:
    from pathlib import Path

    text = Path("src/agentic_project_kit/cli_commands/transfer_context_helpers.py").read_text(
        encoding="utf-8"
    )

    assert "KNOWN_VOLATILE_TRANSFER_PATHS" in text
    assert TRANSFER_INBOX_NEXT_COMMAND_PATH in KNOWN_VOLATILE_TRANSFER_PATHS
    assert TRANSFER_OUTBOX_LAST_RESULT_PATH in KNOWN_VOLATILE_TRANSFER_PATHS
    assert RULE_ACK_CURRENT_PATH in KNOWN_VOLATILE_TRANSFER_PATHS
