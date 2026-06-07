from pathlib import Path


def test_prepare_successor_handoff_defaults_to_no_outbox_write() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    start = text.index("def prepare_successor_handoff(")
    end = text.index("@transfer_app.command(\"remote-work-start\")")
    section = text[start:end]

    assert "--write-outbox/--no-write-outbox" in section
    assert "write_outbox: bool = typer.Option(\n        False" in section
    assert "payload[\"outbox_written\"] = None" in section
    assert "if write_outbox:" in section
    assert "if write_outbox:\n            write_transfer_outbox(root, payload)" in section
