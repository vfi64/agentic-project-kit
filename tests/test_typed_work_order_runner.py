from pathlib import Path

from agentic_project_kit.typed_work_order_queue import run_typed_next, typed_next_result_as_json_data
from agentic_project_kit.typed_work_order_runner import (
    RESULT_FAIL,
    RESULT_HARD_FAIL,
    RESULT_PASS,
    RESULT_PENDING,
    TypedWorkOrder,
    TypedWorkOrderStep,
    parse_typed_work_order,
    run_typed_work_order,
    typed_work_order_result_as_json_data,
)


class CompletedOk:
    returncode = 0
    stdout = "ok"
    stderr = ""


class CompletedFail:
    returncode = 7
    stdout = ""
    stderr = "boom"


def make_order(log_path: str = "docs/reports/terminal/test-typed-work-order.log") -> TypedWorkOrder:
    return TypedWorkOrder(
        work_order_id="demo",
        title="Demo",
        safety="read_only",
        log_path=log_path,
        steps=(TypedWorkOrderStep(kind="command_argv", label="echo", argv=("echo", "ok")),),
        block_dirty_worktree=False,
    )


def test_parse_typed_work_order_requires_steps() -> None:
    try:
        parse_typed_work_order({"id": "x", "title": "X", "safety": "read_only", "log_path": "docs/reports/terminal/x.log", "steps": []})
    except ValueError as exc:
        assert "requires at least one step" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_typed_work_order_rejects_shell_string_shape() -> None:
    data = {"id": "x", "title": "X", "safety": "read_only", "log_path": "docs/reports/terminal/x.log", "steps": [{"kind": "command_argv", "argv": "echo ok"}]}
    try:
        parse_typed_work_order(data)
    except ValueError as exc:
        assert "argv string list" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_run_typed_work_order_pass_writes_machine_readable_log(tmp_path: Path) -> None:
    order = make_order()
    result = run_typed_work_order(order, tmp_path, runner=lambda argv, root: CompletedOk())
    assert result.result_status == RESULT_PASS
    data = typed_work_order_result_as_json_data(result)
    assert data["schema_version"] == 1
    assert data["work_order_id"] == "demo"
    assert data["terminal_log"] == order.log_path
    log_text = (tmp_path / order.log_path).read_text(encoding="utf-8")
    assert "### JSON RESULT ###" in log_text
    assert "### RESULT: PASS ###" in log_text


def test_run_typed_work_order_fail_stops_on_failed_step(tmp_path: Path) -> None:
    order = make_order()
    result = run_typed_work_order(order, tmp_path, runner=lambda argv, root: CompletedFail())
    assert result.result_status == RESULT_FAIL
    assert result.returncode == 7
    assert "Step failed" in result.message
    assert "### RESULT: FAIL ###" in (tmp_path / order.log_path).read_text(encoding="utf-8")


def test_run_typed_work_order_blocks_dirty_worktree(tmp_path: Path) -> None:
    order = TypedWorkOrder("dirty-demo", "Dirty Demo", "read_only", "docs/reports/terminal/dirty.log", (TypedWorkOrderStep(kind="command_argv", label="echo", argv=("echo", "ok")),), True)
    (tmp_path / ".git").mkdir()
    result = run_typed_work_order(order, tmp_path, runner=lambda argv, root: CompletedOk())
    assert result.result_status in {RESULT_PENDING, RESULT_PASS}
    assert (tmp_path / order.log_path).exists()


def test_unsupported_step_kind_is_hard_fail(tmp_path: Path) -> None:
    order = TypedWorkOrder("bad", "Bad", "read_only", "docs/reports/terminal/bad.log", (TypedWorkOrderStep(kind="unknown", label="bad"),), False)
    result = run_typed_work_order(order, tmp_path)
    assert result.result_status == RESULT_HARD_FAIL
    assert result.returncode == 94


def test_run_typed_next_reports_expected_closeout_paths_on_pass(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic/typed_work_orders/inbox"
    inbox.mkdir(parents=True)
    (inbox / "demo.yaml").write_text(
        "id: demo\n"
        "title: Demo\n"
        "safety: read_only\n"
        "log_path: docs/reports/terminal/demo.log\n"
        "block_dirty_worktree: false\n"
        "steps:\n"
        "  - kind: command_argv\n"
        "    label: echo\n"
        "    argv:\n"
        "      - echo\n"
        "      - ok\n",
        encoding="utf-8",
    )
    (tmp_path / ".git").mkdir()

    result = run_typed_next(tmp_path)
    data = typed_next_result_as_json_data(result)

    assert result.result_status == RESULT_PASS
    assert result.expected_closeout_paths == (
        ".agentic/typed_work_orders/inbox/demo.yaml",
        ".agentic/typed_work_orders/executed/demo.yaml",
        "docs/reports/terminal/demo.log",
    )
    assert data["expected_closeout_paths"] == list(result.expected_closeout_paths)
