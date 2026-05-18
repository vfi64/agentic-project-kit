from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.work_orders import list_work_order_templates, load_work_order, prepare_work_order

BASIC_TEMPLATE = """title: Basic gates\nsafety: read_only\ncommand: pytest && ruff check . && check-docs && doctor\nlog_path: docs/reports/terminal/{work_order_id}.log\npostconditions:\n  - pytest passes\n  - ruff passes\n  - check-docs passes\n  - doctor passes\n  - log exists\n  - no false pass\nexpected_outputs:\n  - docs/reports/terminal/{work_order_id}.log\n"""

def test_standard_local_gates_template_is_listed():
    assert "standard-local-gates" in list_work_order_templates()

def test_prepare_work_order_from_template(tmp_path):
    template_dir = tmp_path / ".agentic" / "work_order_templates"
    template_dir.mkdir(parents=True)
    template_dir.joinpath("basic.yaml").write_text(BASIC_TEMPLATE, encoding="utf-8")
    path = prepare_work_order("basic", "demo-order", "feature/demo", tmp_path)
    assert path == tmp_path / ".agentic" / "work_orders" / "demo-order.yaml"
    order = load_work_order("demo-order", tmp_path)
    assert order.work_order_id == "demo-order"
    assert order.expected_branch == "feature/demo"
    assert order.log_path == "docs/reports/terminal/demo-order.log"

def test_work_order_templates_cli_lists_templates():
    result = CliRunner().invoke(app, ["work-order", "templates"])
    assert result.exit_code == 0
    assert "standard-local-gates" in result.output

def test_work_order_prepare_cli_creates_order(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    template_dir = tmp_path / ".agentic" / "work_order_templates"
    template_dir.mkdir(parents=True)
    template_dir.joinpath("basic.yaml").write_text(BASIC_TEMPLATE, encoding="utf-8")
    result = CliRunner().invoke(app, ["work-order", "prepare", "basic", "demo-order", "feature/demo"])
    assert result.exit_code == 0
    assert (tmp_path / ".agentic" / "work_orders" / "demo-order.yaml").exists()
