from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.remote_next import (
    STATUS_SYNC_FAIL,
    remote_next_result_as_json_data,
    render_remote_next_result,
    run_remote_next,
)
from agentic_project_kit.typed_work_order_runner import RESULT_PENDING


def test_remote_next_syncs_main_then_runs_typed_next(tmp_path, monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(argv))
        if argv == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(argv, 0, stdout="feature/x\n", stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="ok\n", stderr="")

    typed = SimpleNamespace(
        returncode=2,
        message="No typed work order queued.",
        queue_status="no_command",
        result_status=RESULT_PENDING,
        source_path=None,
        executed_path=None,
        terminal_log=None,
        expected_closeout_paths=(),
    )

    monkeypatch.setattr("agentic_project_kit.remote_next._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.remote_next.run_typed_next", lambda root: typed)

    result = run_remote_next(tmp_path)

    assert result.sync_status == "synced"
    assert result.returncode == 2
    assert result.typed_next is typed
    assert ("git", "fetch", "origin", "main") in calls
    assert ("git", "switch", "main") in calls
    assert ("git", "pull", "--ff-only", "origin", "main") in calls


def test_remote_next_reports_sync_failure(tmp_path, monkeypatch):
    def fake_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fetch failed")

    monkeypatch.setattr("agentic_project_kit.remote_next._run_git", fake_git)

    result = run_remote_next(tmp_path)

    assert result.sync_status == STATUS_SYNC_FAIL
    assert result.returncode == 2
    assert "fetch failed" in result.message
    assert result.typed_next is None


def test_remote_next_render_and_json_shape():
    result = SimpleNamespace(
        sync_status="sync_fail",
        returncode=2,
        message="failed",
        typed_next=None,
    )

    rendered = render_remote_next_result(result)
    data = remote_next_result_as_json_data(result)

    assert "REMOTE_NEXT_RESULT" in rendered
    assert data["schema_version"] == 1
    assert data["typed_next"] is None


def test_remote_next_renders_expected_closeout_paths():
    typed = SimpleNamespace(
        queue_status="exactly_one_command",
        result_status="PASS",
        terminal_log="docs/reports/terminal/example.log",
        expected_closeout_paths=(
            ".agentic/typed_work_orders/inbox/example.yaml",
            ".agentic/typed_work_orders/executed/example.yaml",
            "docs/reports/terminal/example.log",
        ),
    )
    result = SimpleNamespace(sync_status="synced", returncode=0, message="ok", typed_next=typed)

    rendered = render_remote_next_result(result)

    assert "expected_closeout_path=.agentic/typed_work_orders/inbox/example.yaml" in rendered
    assert "expected_closeout_path=.agentic/typed_work_orders/executed/example.yaml" in rendered
    assert "expected_closeout_path=docs/reports/terminal/example.log" in rendered


def test_remote_next_cli_is_registered(monkeypatch):
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_next.run_remote_next",
        lambda root: SimpleNamespace(sync_status="synced", returncode=0, message="ok", typed_next=None),
    )

    result = CliRunner().invoke(app, ["remote-next"])

    assert result.exit_code == 0, result.output
    assert "REMOTE_NEXT_RESULT" in result.output
