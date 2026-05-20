from pathlib import Path

from agentic_project_kit.typed_work_order_runner import load_typed_work_order


def test_read_only_typed_work_order_example_loads() -> None:
    path = Path(".agentic/typed_work_orders/read_only_status_check.yaml")
    order = load_typed_work_order(path)
    assert order.work_order_id == "read-only-status-check"
    assert order.safety == "read_only"
    assert order.log_path == "docs/reports/terminal/typed-work-order-read-only-status-check.log"
    assert [step.kind for step in order.steps] == ["command_argv", "command_argv", "cockpit_action"]
    assert order.steps[0].argv == ("git", "branch", "--show-current")
    assert order.steps[1].argv == ("git", "status", "--short")
    assert order.steps[2].action_id == "git.status"


def test_ns_exposes_typed_run_shortcut() -> None:
    ns = Path("ns").read_text(encoding="utf-8")
    assert "typed-run" in ns
    assert "work-order typed-run" in ns
    assert "PYTHONPATH=src" in ns
