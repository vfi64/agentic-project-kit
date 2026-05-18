from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.work_orders import load_work_order, check_work_order


def test_standard_local_gates_template_exists_and_is_valid():
    path = Path(".agentic/work_orders/standard-local-gates.yaml")
    assert path.exists()
    order = load_work_order("standard-local-gates")
    assert order.safety == "read_only"
    assert order.expected_branch == "feature/read-only-work-order-templates"
    assert check_work_order(order) == []


def test_standard_local_gates_template_is_listed():
    result = CliRunner().invoke(app, ["work-order", "list"])
    assert result.exit_code == 0
    assert "standard-local-gates" in result.output


def test_standard_local_gates_template_show_is_readable():
    result = CliRunner().invoke(app, ["work-order", "show", "standard-local-gates"])
    assert result.exit_code == 0
    assert "Safety: read_only" in result.output
    assert "pytest" in result.output
    assert "doctor" in result.output
