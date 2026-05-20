import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def write_typed_order(path: Path, log_path: str = "docs/reports/terminal/typed-cli.log") -> None:
    path.write_text(
        "\n".join(
            [
                "id: typed-cli-demo",
                "title: Typed CLI Demo",
                "safety: read_only",
                f"log_path: {log_path}",
                "block_dirty_worktree: false",
                "steps:",
                "  - kind: command_argv",
                "    label: python version",
                "    argv:",
                "      - python3",
                "      - --version",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_work_order_typed_run_dry_run_loads_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    order_path = tmp_path / "typed.yaml"
    write_typed_order(order_path)
    result = runner.invoke(app, ["work-order", "typed-run", str(order_path)])
    assert result.exit_code == 0
    assert "Typed work order: typed-cli-demo" in result.output
    assert "Dry run only" in result.output
    assert not (tmp_path / "docs/reports/terminal/typed-cli.log").exists()


def test_work_order_typed_run_execute_json_writes_log(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    order_path = tmp_path / "typed.yaml"
    write_typed_order(order_path)
    result = runner.invoke(app, ["work-order", "typed-run", str(order_path), "--execute", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["schema_version"] == 1
    assert data["work_order_id"] == "typed-cli-demo"
    assert data["result_status"] == "PASS"
    assert data["terminal_log"] == "docs/reports/terminal/typed-cli.log"
    log_text = (tmp_path / "docs/reports/terminal/typed-cli.log").read_text(encoding="utf-8")
    assert "### JSON RESULT ###" in log_text
    assert "### RESULT: PASS ###" in log_text


def test_work_order_typed_run_rejects_missing_file() -> None:
    result = runner.invoke(app, ["work-order", "typed-run", "missing.yaml"])
    assert result.exit_code == 1
