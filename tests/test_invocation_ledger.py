"""Local invocation ledger (plan step local-invocation-ledger)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit import invocation_ledger as ledger
from agentic_project_kit.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_KEYS = {
    "schema_version",
    "invocation_id",
    "parent_id",
    "root_id",
    "depth",
    "kind",
    "command",
    "started_at",
    "duration_ms",
    "returncode",
    "kit_version",
    "branch",
}


@pytest.fixture
def foreign_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "feature/ledger"], cwd=root, check=True)
    monkeypatch.chdir(root)
    for key in (ledger.LEDGER_ENV, ledger.ID_ENV, ledger.ROOT_ENV, ledger.DEPTH_ENV):
        monkeypatch.delenv(key, raising=False)
    return root


def _records(root: Path) -> list[dict[str, object]]:
    path = ledger.ledger_path(root)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def _exit(code: int):
    def call() -> None:
        raise SystemExit(code)

    return call


def test_command_path_uses_registered_names_and_never_arguments() -> None:
    assert ledger.command_path(app, ["transfer", "remote-next", "secret-branch", "--json"]) == "agentic-kit transfer remote-next"
    assert ledger.command_path(app, ["work", "finish", "--message", "secret message", "--execute"]) == "agentic-kit work finish"
    assert ledger.command_path(app, ["doctor"]) == "agentic-kit doctor"
    assert ledger.command_path(app, ["no-such-command", "secret"]) == "agentic-kit"


def test_ledger_is_off_in_foreign_repositories_by_default(foreign_repo: Path) -> None:
    with pytest.raises(SystemExit):
        ledger.run_cli(_exit(0), app, ["doctor"])

    assert not ledger.ledger_path(foreign_repo).exists()


def test_ledger_records_only_the_documented_fields(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")

    with pytest.raises(SystemExit):
        ledger.run_cli(_exit(3), app, ["work", "finish", "--message", "secret message", "--branch", "secret-branch"])

    [record] = _records(foreign_repo)
    assert set(record) == RECORD_KEYS
    assert record["command"] == "agentic-kit work finish"
    assert record["returncode"] == 3
    assert record["kind"] == "cli"
    assert record["depth"] == 0
    assert record["parent_id"] == ""
    assert record["root_id"] == record["invocation_id"]
    assert record["branch"] == "feature/ledger"
    assert "secret" not in ledger.ledger_path(foreign_repo).read_text(encoding="utf-8")


def test_ledger_opt_in_marker_and_opt_out_environment(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = foreign_repo / ledger.LEDGER_DIR / ledger.ENABLE_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("", encoding="utf-8")
    assert ledger.ledger_enabled(foreign_repo) is True

    monkeypatch.setenv(ledger.LEDGER_ENV, "0")
    assert ledger.ledger_enabled(foreign_repo) is False
    assert ledger.ledger_enabled(REPO_ROOT) is False

    monkeypatch.delenv(ledger.LEDGER_ENV)
    assert ledger.ledger_enabled(REPO_ROOT) is True


@pytest.mark.parametrize("broken", ["write_record", "_begin", "command_path"])
def test_ledger_failure_never_changes_the_return_code(
    foreign_repo: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(ledger, broken, boom)

    with pytest.raises(SystemExit) as exc:
        ledger.run_cli(_exit(7), app, ["doctor"])
    assert exc.value.code == 7
    assert ledger.run_cli(lambda: "result", app, ["doctor"]) == "result"
    assert ledger._ACTIVE == []
    assert ledger.ID_ENV not in os.environ
    # Evidence of the failure is kept: stage and exception type, never the message.
    errors = (foreign_repo / ledger.LEDGER_DIR / ledger.ERROR_FILE).read_text(encoding="utf-8")
    assert "OSError" in errors
    assert "disk full" not in errors


def test_command_exceptions_pass_through_unchanged(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")

    def fail() -> None:
        raise ValueError("command bug")

    with pytest.raises(ValueError, match="command bug"):
        ledger.run_cli(fail, app, ["doctor"])
    assert _records(foreign_repo)[0]["returncode"] == 1


def test_parent_links_for_subprocesses_and_internal_calls(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")
    seen: dict[str, str] = {}

    def outer() -> None:
        seen["exported_id"] = os.environ[ledger.ID_ENV]
        with ledger.internal_call("agentic-kit transfer remote-next"):
            pass
        # A Kit subprocess inherits the exported ids and records the outer call as parent.
        ledger.run_cli(lambda: None, app, ["doctor"])

    ledger.run_cli(outer, app, ["transfer", "continue"])

    records = {record["command"]: record for record in _records(foreign_repo)}
    outer_record = records["agentic-kit transfer continue"]
    internal = records["agentic-kit transfer remote-next"]
    nested = records["agentic-kit doctor"]
    assert seen["exported_id"] == outer_record["invocation_id"]
    assert (internal["kind"], internal["parent_id"], internal["depth"]) == ("internal", outer_record["invocation_id"], 1)
    assert (nested["parent_id"], nested["root_id"], nested["depth"]) == (
        outer_record["invocation_id"],
        outer_record["invocation_id"],
        1,
    )
    assert ledger.ID_ENV not in os.environ


def test_child_process_records_parent_from_environment(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")
    monkeypatch.setenv(ledger.ID_ENV, "parent0000000000")
    monkeypatch.setenv(ledger.ROOT_ENV, "root000000000000")
    monkeypatch.setenv(ledger.DEPTH_ENV, "1")

    ledger.run_cli(lambda: None, app, ["doctor"])

    [record] = _records(foreign_repo)
    assert (record["parent_id"], record["root_id"], record["depth"]) == ("parent0000000000", "root000000000000", 2)
    assert os.environ[ledger.ID_ENV] == "parent0000000000"


def test_retention_drops_old_records_and_bounds_the_file(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ledger, "MAX_BYTES", 200)
    monkeypatch.setattr(ledger, "KEEP_RECORDS", 3)
    old = (datetime.now(timezone.utc) - timedelta(days=ledger.MAX_AGE_DAYS + 1)).isoformat()
    new = datetime.now(timezone.utc).isoformat()
    ledger.write_record(foreign_repo, {"started_at": old, "command": "old"})
    for index in range(5):
        ledger.write_record(foreign_repo, {"started_at": new, "command": f"new-{index}"})

    commands = [record["command"] for record in _records(foreign_repo)]
    assert "old" not in commands
    assert len(commands) <= 4
    assert commands[-1] == "new-4"


def test_ledger_path_is_git_ignored_in_the_kit_repository() -> None:
    path = ledger.LEDGER_DIR / ledger.LEDGER_FILE
    completed = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=REPO_ROOT, check=False)

    assert completed.returncode == 0


def test_ledger_report_counts_outer_nested_internal_and_cycles(foreign_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ledger.LEDGER_ENV, "1")

    def outer() -> None:
        with ledger.internal_call("agentic-kit transfer remote-next"):
            pass
        with pytest.raises(SystemExit):
            ledger.run_cli(_exit(2), app, ["doctor"])

    ledger.run_cli(outer, app, ["transfer", "continue"])
    ledger.run_cli(lambda: None, app, ["doctor"])

    report = ledger.ledger_report(foreign_repo)
    rows = {row["command"]: row for row in report["commands"]}
    assert report["record_count"] == 4
    assert report["root_invocation_count"] == 2
    assert report["invocations_per_root"]["max"] == 3
    assert (rows["agentic-kit doctor"]["outer"], rows["agentic-kit doctor"]["nested"], rows["agentic-kit doctor"]["failed"]) == (1, 1, 1)
    assert rows["agentic-kit transfer remote-next"]["internal"] == 1

    result = CliRunner().invoke(app, ["ledger", "report", "--root", str(foreign_repo), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["record_count"] == 4


def test_real_entry_point_records_a_process_start(foreign_repo: Path) -> None:
    env = {**os.environ, ledger.LEDGER_ENV: "1", "PYTHONPATH": str(REPO_ROOT / "src")}
    for key in (ledger.ID_ENV, ledger.ROOT_ENV, ledger.DEPTH_ENV):
        env.pop(key, None)

    completed = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.cli", "ledger", "report", "--json"],
        cwd=foreign_repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    [record] = _records(foreign_repo)
    assert record["command"] == "agentic-kit ledger report"
    assert record["returncode"] == 0


def test_doc_registry_register_records_status_review_policy_and_summary(tmp_path: Path) -> None:
    from agentic_project_kit.documentation_registry import register_documentation_registry_entry

    result = register_documentation_registry_entry(
        REPO_ROOT,
        document_path="docs/workflow/INVOCATION_LEDGER.md",
        document_class="operational/automation",
        status="bogus",
    )
    assert result["code"] == "FAIL_UNKNOWN_STATUS"
    result = register_documentation_registry_entry(
        REPO_ROOT,
        document_path="docs/workflow/INVOCATION_LEDGER.md",
        document_class="operational/automation",
        review_policy="sometimes",
    )
    assert result["code"] == "FAIL_UNKNOWN_REVIEW_POLICY"

    from agentic_project_kit.documentation_registry import append_documentation_registry_entry_text

    text = append_documentation_registry_entry_text(
        "documents:\n  - path: a.md\n    class: evidence/log\n    owner: maintainers\n",
        path="docs/workflow/x.md",
        document_class="operational/automation",
        owner="maintainers",
        extra={"status": "active", "review_policy": "required"},
    )
    assert text.endswith(
        "  - path: docs/workflow/x.md\n    class: operational/automation\n    owner: maintainers\n"
        "    status: active\n    review_policy: required\n"
    )
