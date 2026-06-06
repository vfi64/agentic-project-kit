from pathlib import Path


def test_normalize_session_defaults_to_no_outbox_write() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    start = text.index("def normalize_session(")
    end = text.index("@transfer_app.command(\"prepare-successor-handoff\")")
    section = text[start:end]

    assert "--write-outbox/--no-write-outbox" in section
    assert "write_outbox: bool = typer.Option(\n        False" in section
    assert "if write_outbox:" in section
    assert "payload[\"outbox_written\"] = None" in section
    assert section.count("volatile_repair_result = None") == 1
