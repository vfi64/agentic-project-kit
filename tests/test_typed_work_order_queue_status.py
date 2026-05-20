from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.typed_work_order_queue import (
    STATUS_EXACTLY_ONE_COMMAND,
    STATUS_MULTIPLE_COMMANDS,
    STATUS_NO_COMMAND,
    inspect_typed_work_order_queue,
    typed_work_order_queue_status_as_json_data,
)

runner = CliRunner()


def test_missing_typed_queue_is_no_command(tmp_path: Path) -> None:
    status = inspect_typed_work_order_queue(tmp_path / "missing")
    assert status.status == STATUS_NO_COMMAND
    assert status.pending_count == 0
    data = typed_work_order_queue_status_as_json_data(status)
    assert data["schema_version"] == 1
    assert data["status"] == STATUS_NO_COMMAND

def test_typed_queue_detects_exactly_one_command(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "one.yaml").write_text("id: one\n", encoding="utf-8")
    status = inspect_typed_work_order_queue(inbox)
    assert status.status == STATUS_EXACTLY_ONE_COMMAND
    assert status.pending_count == 1
    assert status.pending_paths == (inbox / "one.yaml",)

def test_typed_queue_detects_multiple_commands(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.yaml").write_text("id: a\n", encoding="utf-8")
    (inbox / "b.yaml").write_text("id: b\n", encoding="utf-8")
    status = inspect_typed_work_order_queue(inbox)
    assert status.status == STATUS_MULTIPLE_COMMANDS
    assert [path.name for path in status.pending_paths] == ["a.yaml", "b.yaml"]

def test_typed_queue_status_cli_outputs_json_for_no_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["work-order", "typed-queue-status", "--inbox", str(tmp_path / "missing"), "--json"])
    assert result.exit_code == 0, result.output
    assert "\"status\": \"no_command\"" in result.output

def test_typed_queue_status_cli_fails_for_multiple_commands(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.yaml").write_text("id: a\n", encoding="utf-8")
    (inbox / "b.yaml").write_text("id: b\n", encoding="utf-8")
    result = runner.invoke(app, ["work-order", "typed-queue-status", "--inbox", str(inbox)])
    assert result.exit_code == 2
    assert "status=multiple_commands" in result.output
