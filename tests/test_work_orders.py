from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.work_orders import list_work_orders, parse_work_order, render_work_order


def test_parse_work_order_requires_core_fields():
    try:
        parse_work_order({"id": "x"})
    except ValueError as exc:
        assert "missing required work order" in str(exc)
    else:
        raise AssertionError("missing fields should fail")


def test_parse_work_order_rejects_bare_exit():
    data = {"id": "x", "title": "X", "safety": "read_only", "command": "echo ok; exit", "log_path": "docs/reports/terminal/x.log"}
    try:
        parse_work_order(data)
    except ValueError as exc:
        assert "bare exit" in str(exc)
    else:
        raise AssertionError("bare exit should fail")


def test_render_work_order_contains_core_fields():
    order = parse_work_order({"id": "demo", "title": "Demo", "safety": "read_only", "command": "echo ok", "log_path": "docs/reports/terminal/demo.log"})
    rendered = render_work_order(order)
    assert "Work order: demo" in rendered
    assert "Safety: read_only" in rendered
    assert "echo ok" in rendered


def test_list_work_orders_reads_yaml_files(tmp_path):
    root = tmp_path
    directory = root / ".agentic" / "work_orders"
    directory.mkdir(parents=True)
    (directory / "demo.yaml").write_text("id: demo\ntitle: Demo\nsafety: read_only\ncommand: echo ok\nlog_path: docs/reports/terminal/demo.log\n", encoding="utf-8")
    orders = list_work_orders(root)
    assert [order.work_order_id for order in orders] == ["demo"]


def test_work_order_cli_list_allows_empty_directory():
    result = CliRunner().invoke(app, ["work-order", "list"])
    assert result.exit_code == 0


def test_work_order_cli_show_missing_fails():
    result = CliRunner().invoke(app, ["work-order", "show", "missing"])
    assert result.exit_code == 1
    assert "work order not found" in result.output
