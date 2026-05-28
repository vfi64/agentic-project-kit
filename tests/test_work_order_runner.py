from pathlib import Path

from agentic_project_kit.work_order_runner import (
    render_work_order_run_result,
    run_validated_work_order,
)


def _valid_work_order_text() -> str:
    return """# agentic-project-kit work order
from pathlib import Path

print("hello from work order")
COMMAND_HINT = "./ns pr-status 123"
SUMMARY = """### CANONICAL SUMMARY ###
### RESULT: PASS ###
Terminal bleibt offen. Kein exit am Blockende.
"""
"""


def test_run_validated_work_order_blocks_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_validated_work_order(
        work_order_path=Path(".agentic/commands/inbox/next-turn.py"),
        local_log_path=tmp_path / "local.log",
        remote_log_path=tmp_path / "remote.log",
    )

    assert result.validation_ok is False
    assert result.executed is False
    assert result.returncode == 1
    assert "missing work order file" in (tmp_path / "remote.log").read_text(
        encoding="utf-8"
    )


def test_run_validated_work_order_executes_and_writes_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    work_order = tmp_path / ".agentic/commands/inbox/next-turn.py"
    work_order.parent.mkdir(parents=True)
    work_order.write_text(_valid_work_order_text(), encoding="utf-8")

    result = run_validated_work_order(
        work_order_path=work_order,
        local_log_path=tmp_path / "next-turn-latest-local.log",
        remote_log_path=tmp_path / "docs/reports/terminal/next-turn-latest.log",
    )

    rendered = render_work_order_run_result(result)
    remote_log = (tmp_path / "docs/reports/terminal/next-turn-latest.log").read_text(
        encoding="utf-8"
    )

    assert result.validation_ok is True
    assert result.executed is True
    assert result.returncode == 0
    assert "WORK_ORDER_RUN_RESULT" in rendered
    assert "hello from work order" in remote_log
