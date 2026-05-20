from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.typed_work_order_queue import run_typed_next

runner = CliRunner()

def write_order(path: Path, log_name: str = "typed-next-test.log") -> None:
    path.write_text("\n".join(["id: typed-next-demo", "title: Typed Next Demo", "safety: read_only", f"log_path: docs/reports/terminal/{log_name}", "block_dirty_worktree: false", "steps:", "  - kind: command_argv", "    label: python version", "    argv:", "      - python3", "      - --version", ""]) , encoding="utf-8")

def test_typed_next_blocks_no_command(tmp_path: Path) -> None:
    result = run_typed_next(tmp_path)
    assert result.queue_status == "no_command"
    assert result.result_status == "PENDING"
    assert result.returncode == 2

def test_typed_next_blocks_multiple_commands(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic/typed_work_orders/inbox"
    inbox.mkdir(parents=True)
    write_order(inbox / "a.yaml", "a.log")
    write_order(inbox / "b.yaml", "b.log")
    result = run_typed_next(tmp_path)
    assert result.queue_status == "multiple_commands"
    assert result.result_status == "FAIL"
    assert (inbox / "a.yaml").exists()
    assert (inbox / "b.yaml").exists()

def test_typed_next_executes_exactly_one_and_moves_to_executed(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic/typed_work_orders/inbox"
    inbox.mkdir(parents=True)
    source = inbox / "one.yaml"
    write_order(source)
    result = run_typed_next(tmp_path)
    assert result.queue_status == "exactly_one_command"
    assert result.result_status == "PASS"
    assert result.executed_path == ".agentic/typed_work_orders/executed/one.yaml"
    assert not source.exists()
    assert (tmp_path / ".agentic/typed_work_orders/executed/one.yaml").exists()
    assert (tmp_path / "docs/reports/terminal/typed-next-test.log").exists()

def test_typed_next_cli_json_no_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["work-order", "typed-next", "--json"])
    assert result.exit_code == 2
    assert "\"queue_status\": \"no_command\"" in result.output
    assert "\"result_status\": \"PENDING\"" in result.output

def test_ns_exposes_typed_next_shortcut() -> None:
    ns = Path("ns").read_text(encoding="utf-8")
    assert "typed-next" in ns
    assert "work-order typed-next" in ns
