from __future__ import annotations

import json
import sys
from pathlib import Path

from agentic_project_kit.transfer_uplink import (
    LATEST_JSON,
    LATEST_LOG,
    publish_latest_transfer_report,
    run_and_log_transfer_command,
    run_and_log_transfer_sequence,
)


def _write_manifest(root: Path) -> None:
    manifest = root / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )


def test_run_and_log_transfer_command_records_success_with_chat_reply(tmp_path):
    script = "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue now'); print('CHAT_REPLY=d | NEXT=continue now')"

    result = run_and_log_transfer_command(
        [sys.executable, "-c", script],
        label="success-case",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.final_signal == "d"
    assert result.chat_reply == "d | NEXT=Run transfer publish-last-report"
    assert result.next_action == "continue now"
    assert (tmp_path / LATEST_LOG).exists()
    assert result.transfer_upload == "done"
    assert result.remote_report_path.startswith("docs/reports/transfer_runs/")
    assert (tmp_path / result.remote_report_path).exists()
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["next_action"] == "continue now"
    assert "CHAT_REPLY=d | NEXT=Run transfer publish-last-report" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_run_and_log_transfer_command_uses_manifest_transfer_namespace(tmp_path):
    _write_manifest(tmp_path)

    result = run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue now')"],
        label="manifest-case",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.latest_log_path == ".agentic/state/handoff/transfer_runs/latest-transfer-report.log"
    assert result.latest_json_path == ".agentic/state/handoff/transfer_runs/latest-transfer-report.json"
    assert result.remote_report_path.startswith(".agentic/state/handoff/transfer_runs/")
    assert (tmp_path / result.latest_log_path).exists()
    assert (tmp_path / result.remote_report_path).exists()
    assert not (tmp_path / LATEST_LOG).exists()


def test_run_and_log_transfer_command_records_failure_without_explicit_signal(tmp_path):
    result = run_and_log_transfer_command(
        [sys.executable, "-c", "import sys; print('broken'); sys.exit(3)"],
        label="failure-case",
        cwd=tmp_path,
    )

    assert result.returncode == 3
    assert result.final_signal == "f"
    assert result.chat_reply == "d | NEXT=Run transfer publish-last-report"
    assert result.next_action == "Inspect latest-transfer-uplink log before continuing."
    assert "broken" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_run_sequence_stops_on_first_failure_and_keeps_overall_failure(tmp_path):
    result = run_and_log_transfer_sequence(
        [
            [sys.executable, "-c", "print('FINAL_SIGNAL=f'); print('FINAL_NEXT=fix first')"],
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue')"],
        ],
        label="sequence-failure",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.final_signal == "f"
    assert result.chat_reply == "d | NEXT=Run transfer publish-last-report"
    assert result.next_action == "fix first"
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "f"
    assert len(data["sequence_steps"]) == 1
    log = (tmp_path / LATEST_LOG).read_text(encoding="utf-8")
    assert "TRANSFER_REPORT_WRITTEN=done" in log
    assert "LOCAL_REPORT=docs/reports/transfer_runs/" in log
    assert "CHAT_REPLY=d | NEXT=Run transfer publish-last-report" in log


def test_run_sequence_records_success_when_all_steps_succeed(tmp_path):
    result = run_and_log_transfer_sequence(
        [
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=step one')"],
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=step two')"],
        ],
        label="sequence-success",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.final_signal == "d"
    assert result.chat_reply == "d | NEXT=Run transfer publish-last-report"
    assert result.next_action == "Continue with the next safe transfer step."
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert len(data["sequence_steps"]) == 2

def test_run_and_log_cli_prints_only_human_go_lines(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    script = "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue now')"

    result = CliRunner().invoke(
        app,
        ["transfer", "run-and-log", "--label", "quiet-ok", "--", sys.executable, "-c", script],
    )

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_REPORT_WRITTEN=done"
    assert lines[1].startswith("LOCAL_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=d | NEXT=Run transfer publish-last-report"
    assert len(lines) == 3
    report_path = lines[1].split("=", 1)[1]
    data = json.loads((tmp_path / report_path).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["chat_reply"] == "d | NEXT=Run transfer publish-last-report"


def test_run_sequence_cli_prints_go_even_when_step_failed_but_report_written(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "run-sequence-and-log",
            "--label",
            "quiet-fail",
            "--step",
            f"{sys.executable} -c \"import sys; print('broken'); sys.exit(3)\"",
        ],
    )

    assert result.exit_code == 3
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_REPORT_WRITTEN=done"
    assert lines[1].startswith("LOCAL_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=d | NEXT=Run transfer publish-last-report"
    assert len(lines) == 3
    report_path = lines[1].split("=", 1)[1]
    data = json.loads((tmp_path / report_path).read_text(encoding="utf-8"))
    assert data["final_signal"] == "f"
    assert data["returncode"] == 3


def test_show_last_report_prints_compact_summary_by_default(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue')"],
        label="show-latest",
        cwd=tmp_path,
    )

    result = CliRunner().invoke(app, ["transfer", "show-last-report"])

    assert result.exit_code == 0
    assert "TRANSFER_SHOW_LAST_REPORT" in result.stdout
    assert "show-latest" in result.stdout
    assert "FULL_REPORT" in result.stdout


def test_show_last_report_prints_full_json_with_json_flag(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue')"],
        label="show-latest",
        cwd=tmp_path,
    )

    result = CliRunner().invoke(app, ["transfer", "show-last-report", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["label"] == "show-latest"
    assert data["final_signal"] == "d"
    assert data["next_action"] == "continue"


def test_show_last_report_fails_when_missing(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "show-last-report"])

    assert result.exit_code == 1
    assert "latest transfer report not found" in result.stdout

def test_write_transfer_report_from_repo_result_does_not_execute_python(tmp_path):
    from agentic_project_kit.transfer_repo_actions import RepoActionResult
    from agentic_project_kit.transfer_uplink import write_transfer_report_from_repo_result

    result = RepoActionResult(
        action="pr-wait-ci",
        result_status="PASS",
        returncode=0,
        command=["agentic-kit", "pr", "wait-ci", "123"],
        stdout="PR readiness outcome: READY_TO_MERGE\n",
        stderr="",
        next_action="Run transfer pr-status or merge-if-green after CI is green.",
    )

    uplink = write_transfer_report_from_repo_result(
        result,
        label="direct-repo-result",
        cwd=tmp_path,
    )

    report = (tmp_path / uplink.remote_report_path).read_text(encoding="utf-8")
    assert "READY_TO_MERGE" in report
    assert "agentic-kit" in report
    assert "FileNotFoundError" not in report
    assert uplink.returncode == 0
    assert uplink.final_signal == "d"

def test_transfer_run_reports_are_gitignored():

    gitignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()

    assert "docs/reports/transfer_runs/" in gitignore

def test_transfer_report_label_is_sanitized_for_paths(tmp_path):
    result = run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d')"],
        label="../bad label/with spaces",
        cwd=tmp_path,
    )

    assert result.label == "bad-label-with-spaces"
    assert result.remote_report_path.startswith("docs/reports/transfer_runs/")
    assert "../" not in result.remote_report_path
    assert "/" not in result.remote_report_path.removeprefix("docs/reports/transfer_runs/")
    assert (tmp_path / result.remote_report_path).exists()


def test_transfer_report_empty_label_uses_safe_default(tmp_path):
    result = run_and_log_transfer_sequence(
        [[sys.executable, "-c", "print('FINAL_SIGNAL=d')"]],
        label=" ../ ",
        cwd=tmp_path,
    )

    assert result.label == "transfer-report"
    assert result.remote_report_path.endswith("-transfer-report.json")
    assert (tmp_path / result.remote_report_path).exists()


def test_publish_latest_transfer_report_copies_gitignored_latest_report_to_tracked_handoff_dir(tmp_path):
    run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=handoff ready')"],
        label="primary handoff",
        cwd=tmp_path,
    )

    published = publish_latest_transfer_report(tmp_path, label="primary handoff")

    assert published["transfer_upload"] == "done"
    assert published["chat_reply"] == "g"
    assert str(published["remote_report"]).startswith("docs/reports/terminal/transfer_handoff_reports/")
    assert "docs/reports/transfer_runs/" not in str(published["remote_report"])
    report_path = tmp_path / str(published["remote_report"])
    latest_path = tmp_path / str(published["latest_remote_report"])
    assert report_path.exists()
    assert latest_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["published_transfer_handoff"]["source_latest_json_path"] == str(LATEST_JSON)
    assert data["published_transfer_handoff"]["published_report_path"] == published["remote_report"]




def test_publish_last_report_cli_prints_failure_lines_for_failed_tracked_report(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    run_and_log_transfer_command(
        [sys.executable, "-c", "import sys; print('FINAL_SIGNAL=f'); print('FINAL_NEXT=fix failure'); sys.exit(4)"],
        label="failed handoff",
        cwd=tmp_path,
    )

    result = CliRunner().invoke(app, ["transfer", "publish-last-report", "--label", "failed handoff"])

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/")
    assert lines[2] == "CHAT_REPLY=f | NEXT=Inspect published transfer handoff report."
def test_publish_last_report_cli_prints_go_lines_for_tracked_report(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=handoff ready')"],
        label="cli handoff",
        cwd=tmp_path,
    )

    result = CliRunner().invoke(app, ["transfer", "publish-last-report", "--label", "cli handoff"])

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/")
    assert lines[2] == "CHAT_REPLY=g"
    assert len(lines) == 3
    report_path = lines[1].split("=", 1)[1]
    assert (tmp_path / report_path).exists()


def test_run_and_log_writes_canonical_outbox_with_safety_header(tmp_path):

    for relative in (
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_preservation.yaml",
        "docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md",
        "docs/archive/PRE_GUI_HARDENING_TASKS.md",
    ):
        source = Path(relative)
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    run_and_log_transfer_command(
        [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue')"],
        label="outbox-header",
        cwd=tmp_path,
    )

    outbox = tmp_path / ".agentic" / "transfer" / "outbox" / "last_result.txt"
    data = json.loads(outbox.read_text(encoding="utf-8"))
    assert data["kind"] == "local_to_llm_last_result"
    assert data["safety_header"]["canonical_transfer_files"]["local_to_llm"] == ".agentic/transfer/outbox/last_result.txt"
    assert "raw_newline_in_python_string_literals" in data["safety_header"]["known_failure_classes"]
    assert data["last_result"]["transfer_report_written"] == "done"

def test_publish_latest_transfer_report_embeds_llm_execution_context(tmp_path, monkeypatch):
    from agentic_project_kit.transfer_uplink import publish_latest_transfer_report

    for relative in (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ):
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    run_and_log_transfer_command(
        ["python", "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=handoff ready')"],
        label="llm context handoff",
        cwd=tmp_path,
    )

    published = publish_latest_transfer_report(tmp_path, label="llm context handoff")
    data = json.loads((tmp_path / published["remote_report"]).read_text(encoding="utf-8"))

    assert data["llm_execution_context"]["kind"] == "llm_execution_context"
    assert data["llm_execution_context"]["command_reference"]["must_not_reconstruct_commands_from_memory"] is True


def test_publish_latest_transfer_report_latest_json_embeds_llm_execution_context(tmp_path, monkeypatch):
    from agentic_project_kit.transfer_uplink import publish_latest_transfer_report

    for relative in (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ):
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    run_and_log_transfer_command(
        ["python", "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=handoff ready')"],
        label="latest llm context handoff",
        cwd=tmp_path,
    )

    published = publish_latest_transfer_report(tmp_path, label="latest llm context handoff")
    latest = json.loads((tmp_path / published["latest_remote_report"]).read_text(encoding="utf-8"))

    assert latest["llm_execution_context"]["kind"] == "llm_execution_context"
    assert latest["llm_execution_context"]["command_reference"]["must_not_reconstruct_commands_from_memory"] is True


def test_verify_llm_context_refresh_cli_passes_for_generated_reports(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app
    from agentic_project_kit.transfer_safety_context import build_local_to_llm_payload

    for relative in (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_preservation.yaml",
        "docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md",
        "docs/archive/PRE_GUI_HARDENING_TASKS.md",
    ):
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    payload = build_local_to_llm_payload(tmp_path, {"final_signal": "d", "next_action": "continue"})
    outbox = tmp_path / ".agentic/transfer/outbox/last_result.txt"
    latest = tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    latest.parent.mkdir(parents=True, exist_ok=True)
    outbox.write_text(json.dumps(payload), encoding="utf-8")
    latest.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["transfer", "verify-llm-context-refresh"])

    assert result.exit_code == 0
    assert "TRANSFER_VERIFY_LLM_CONTEXT_REFRESH" in result.stdout
    assert "PASS" in result.stdout


def test_verify_llm_context_refresh_cli_blocks_when_context_missing(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    outbox = tmp_path / ".agentic/transfer/outbox/last_result.txt"
    latest = tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    latest.parent.mkdir(parents=True, exist_ok=True)
    outbox.write_text(json.dumps({"kind": "old"}), encoding="utf-8")
    latest.write_text(json.dumps({"kind": "old"}), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["transfer", "verify-llm-context-refresh"])

    assert result.exit_code == 2
    assert "TRANSFER_VERIFY_LLM_CONTEXT_REFRESH" in result.stdout
    assert "BLOCKED" in result.stdout

def test_refresh_llm_context_carriers_cli_uses_refresh_helper(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app
    from agentic_project_kit.cli_commands import transfer as transfer_module

    monkeypatch.setattr(
        transfer_module,
        "refresh_llm_context_carriers",
        lambda root: {
            "result_status": "PASS",
            "final_signal": "d",
            "next_action": "LLM context carriers refreshed.",
            "outbox_path": ".agentic/transfer/outbox/last_result.txt",
            "latest_handoff_report_path": "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        },
    )

    result = CliRunner().invoke(app, ["transfer", "refresh-llm-context-carriers"])

    assert result.exit_code == 0
    assert "TRANSFER_REFRESH_LLM_CONTEXT_CARRIERS" in result.stdout
    assert "PASS" in result.stdout

def test_publish_latest_transfer_report_refreshes_outbox_carrier(tmp_path, monkeypatch):
    from agentic_project_kit.transfer_uplink import LATEST_JSON
    from agentic_project_kit.transfer_uplink import LATEST_LOG
    from agentic_project_kit.transfer_uplink import publish_latest_transfer_report

    monkeypatch.chdir(tmp_path)

    latest_json = tmp_path / LATEST_JSON
    latest_log = tmp_path / LATEST_LOG
    latest_json.parent.mkdir(parents=True, exist_ok=True)
    latest_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "20260619T000000Z-test",
                "label": "unit",
                "command": ["agentic-kit", "transfer", "example"],
                "returncode": 0,
                "stdout": "",
                "stderr": "",
                "final_signal": "d",
                "next_action": "Continue.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    latest_log.write_text("TRANSFER_UPLINK_RUN=20260619T000000Z-test\n", encoding="utf-8")

    result = publish_latest_transfer_report(tmp_path)

    outbox = tmp_path / ".agentic/transfer/outbox/last_result.txt"
    latest_published = tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"

    assert str(result["local_outbox"]).endswith(".agentic/transfer/outbox/last_result.txt")
    assert outbox.exists()
    assert latest_published.exists()

    outbox_data = json.loads(outbox.read_text(encoding="utf-8"))
    published_data = json.loads(latest_published.read_text(encoding="utf-8"))

    assert outbox_data["kind"] == "local_to_llm_last_result"
    assert outbox_data["derived_projection"] is True
    assert outbox_data["last_result"] == published_data
    assert outbox_data["last_result"]["published_transfer_handoff"]["latest_published_report_path"] == (
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert isinstance(outbox_data["llm_execution_context"], dict)
    assert isinstance(outbox_data["last_result"]["llm_execution_context"], dict)

def test_transfer_outbox_last_result_is_ignored_by_gitignore():
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    outbox = ".agentic/transfer/outbox/last_result.txt"
    result = subprocess.run(
        ["git", "check-ignore", "-q", outbox],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
