from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.work_orders import check_work_order, list_work_orders, parse_work_order, render_work_order


def valid_order_data(**overrides):
    data = {
        "id": "demo",
        "title": "Demo",
        "safety": "read_only",
        "expected_branch": "feature/demo",
        "command": ".venv/bin/python -m pytest -q && .venv/bin/ruff check . && PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli check-docs && PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli doctor",
        "log_path": "docs/reports/terminal/demo.log",
        "preconditions": ["branch equals expected_branch"],
        "postconditions": ["pytest passes", "ruff passes", "check-docs passes", "doctor passes", "log exists", "no false PASS"],
        "expected_outputs": ["docs/reports/terminal/demo.log"],
    }
    data.update(overrides)
    return data


def test_parse_work_order_requires_core_fields():
    try:
        parse_work_order({"id": "x"})
    except ValueError as exc:
        assert "missing required work order" in str(exc)
    else:
        raise AssertionError("missing fields should fail")


def test_parse_work_order_requires_expected_branch():
    data = valid_order_data()
    data.pop("expected_branch")
    try:
        parse_work_order(data)
    except ValueError as exc:
        assert "expected_branch" in str(exc)
    else:
        raise AssertionError("expected_branch should be required")


def test_parse_work_order_rejects_bare_exit():
    data = valid_order_data(command="echo ok; exit")
    try:
        parse_work_order(data)
    except ValueError as exc:
        assert "bare exit" in str(exc)
    else:
        raise AssertionError("bare exit should fail")


def test_parse_work_order_rejects_heredoc_fragment():
    data = valid_order_data(command="cat << EOF")
    try:
        parse_work_order(data)
    except ValueError as exc:
        assert "forbidden fragment" in str(exc)
    else:
        raise AssertionError("heredoc should fail")


def test_parse_work_order_rejects_log_path_outside_terminal_reports():
    data = valid_order_data(log_path="tmp/x.log")
    try:
        parse_work_order(data)
    except ValueError as exc:
        assert "log_path must be under docs/reports/terminal" in str(exc)
    else:
        raise AssertionError("unsafe log_path should fail")


def test_check_work_order_requires_constitutional_gates():
    order = parse_work_order(valid_order_data(command="printf ok"))
    errors = check_work_order(order)
    assert any("pytest" in error for error in errors)
    assert any("ruff check" in error for error in errors)
    assert any("check-docs" in error for error in errors)
    assert any("doctor" in error for error in errors)


def test_check_work_order_rejects_false_pass_marker():
    order = parse_work_order(valid_order_data(command=".venv/bin/python -m pytest -q && .venv/bin/ruff check . && check-docs && doctor && printf '### RESULT: PASS ###'"))
    errors = check_work_order(order)
    assert any("must not print PASS directly" in error for error in errors)


def test_check_work_order_rejects_main_expected_branch():
    order = parse_work_order(valid_order_data(expected_branch="main"))
    errors = check_work_order(order)
    assert any("non-main branch" in error for error in errors)


def test_check_work_order_requires_log_expected_output():
    order = parse_work_order(valid_order_data(expected_outputs=[]))
    errors = check_work_order(order)
    assert any("expected_outputs" in error for error in errors)


def test_parse_work_order_accepts_metadata_lists():
    order = parse_work_order(valid_order_data(preconditions=["clean tree"], expected_outputs=["docs/reports/terminal/demo.log"]))
    assert order.preconditions == ("clean tree",)
    assert order.expected_branch == "feature/demo"
    assert order.expected_outputs == ("docs/reports/terminal/demo.log",)


def test_render_work_order_contains_core_fields():
    order = parse_work_order(valid_order_data())
    rendered = render_work_order(order)
    assert "Work order: demo" in rendered
    assert "Safety: read_only" in rendered
    assert "Expected branch: feature/demo" in rendered


def test_list_work_orders_reads_yaml_files(tmp_path):
    root = tmp_path
    directory = root / ".agentic" / "work_orders"
    directory.mkdir(parents=True)
    (directory / "demo.yaml").write_text(
        "id: demo\ntitle: Demo\nsafety: read_only\nexpected_branch: feature/demo\ncommand: pytest && ruff check . && check-docs && doctor\nlog_path: docs/reports/terminal/demo.log\npostconditions:\n  - pytest ruff check-docs doctor log exists no false PASS\nexpected_outputs:\n  - docs/reports/terminal/demo.log\n",
        encoding="utf-8",
    )
    orders = list_work_orders(root)
    assert [order.work_order_id for order in orders] == ["demo"]


def test_work_order_cli_list_allows_empty_directory():
    result = CliRunner().invoke(app, ["work-order", "list"])
    assert result.exit_code == 0


def test_work_order_cli_show_missing_fails():
    result = CliRunner().invoke(app, ["work-order", "show", "missing"])
    assert result.exit_code == 1
    assert "work order not found" in result.output


def test_work_order_check_cli_passes_for_repository_work_orders():
    result = CliRunner().invoke(app, ["work-order", "check"])
    assert result.exit_code == 0
    assert "Work order contract check passed" in result.output


def test_work_order_run_dry_run_does_not_create_log():
    result = CliRunner().invoke(app, ["work-order", "run", "missing"])
    assert result.exit_code == 1


def test_work_order_execute_wrong_branch_writes_fail_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess_dir = tmp_path / ".git"
    subprocess_dir.mkdir()
    directory = tmp_path / ".agentic" / "work_orders"
    directory.mkdir(parents=True)
    (directory / "demo.yaml").write_text(
        "id: demo\ntitle: Demo\nsafety: read_only\nexpected_branch: feature/demo\ncommand: pytest && ruff check . && check-docs && doctor\nlog_path: docs/reports/terminal/demo.log\npostconditions:\n  - pytest passes\n  - ruff passes\n  - check-docs passes\n  - doctor passes\n  - log exists\n  - no false PASS\nexpected_outputs:\n  - docs/reports/terminal/demo.log\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["work-order", "run", "demo", "--execute"])
    assert result.exit_code != 0
    log_file = tmp_path / "docs/reports/terminal/demo.log"
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "Branch assertion failed" in log_text
    assert "### RESULT: FAIL ###" in log_text
    assert "### RESULT: PASS ###" not in log_text


def test_work_order_run_blocks_when_governance_fails(tmp_path, monkeypatch):
    from agentic_project_kit import work_orders

    order = work_orders.WorkOrder(
        work_order_id="blocked-governance",
        title="Blocked governance",
        safety="read_only",
        expected_branch="feature/test-branch",
        command="pytest && ruff check . && agentic-kit check-docs && agentic-kit doctor",
        log_path="docs/reports/terminal/blocked_governance.log",
        postconditions=(
            "pytest passes",
            "ruff passes",
            "check-docs passes",
            "doctor passes",
            "log exists",
            "no false pass",
        ),
        expected_outputs=("docs/reports/terminal/blocked_governance.log",),
    )
    monkeypatch.setattr(work_orders, "current_git_branch", lambda project_root=tmp_path: "feature/test-branch")
    import agentic_project_kit.governance as governance

    monkeypatch.setattr(governance, "governance_check", lambda: ["constitution broken"])
    code = work_orders.run_work_order(order, tmp_path)
    assert code == 98
    log_text = (tmp_path / order.log_path).read_text(encoding="utf-8")
    assert "governance: constitution broken" in log_text
    assert "### RESULT: FAIL ###" in log_text

