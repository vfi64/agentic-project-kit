from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.typed_work_order_queue import STATUS_ALREADY_EXECUTED, run_typed_next

runner = CliRunner()


def write_order(path: Path, log_name: str = "already-executed.log") -> None:
    lines = [
        "id: already-executed-demo",
        "title: Already Executed Demo",
        "safety: read_only",
        f"log_path: docs/reports/terminal/{log_name}",
        "block_dirty_worktree: false",
        "steps:",
        "  - kind: command_argv",
        "    label: python version",
        "    argv:",
        "      - python3",
        "      - --version",
    ]
    path.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")


def test_typed_next_refuses_already_executed_work_order_without_running(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic/typed_work_orders/inbox"
    executed = tmp_path / ".agentic/typed_work_orders/executed"
    inbox.mkdir(parents=True)
    executed.mkdir(parents=True)
    source = inbox / "one.yaml"
    target = executed / "one.yaml"
    write_order(source)
    target.write_text("already done", encoding="utf-8")
    result = run_typed_next(tmp_path)
    assert result.queue_status == STATUS_ALREADY_EXECUTED
    assert result.result_status == "PENDING"
    assert result.returncode == 2
    assert result.source_path == ".agentic/typed_work_orders/inbox/one.yaml"
    assert result.executed_path == ".agentic/typed_work_orders/executed/one.yaml"
    assert source.exists()
    assert target.read_text(encoding="utf-8") == "already done"
    assert not (tmp_path / "docs/reports/terminal/already-executed.log").exists()


def test_typed_next_cli_json_reports_already_executed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = tmp_path / ".agentic/typed_work_orders/inbox"
    executed = tmp_path / ".agentic/typed_work_orders/executed"
    inbox.mkdir(parents=True)
    executed.mkdir(parents=True)
    write_order(inbox / "one.yaml")
    (executed / "one.yaml").write_text("already done", encoding="utf-8")
    result = runner.invoke(app, ["work-order", "typed-next", "--json"])
    assert result.exit_code == 2
    assert "\"queue_status\": \"already_executed\"" in result.output
    assert "\"result_status\": \"PENDING\"" in result.output
    assert "refusing duplicate execution" in result.output
