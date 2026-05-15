import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def _write_workflow_files(root: Path, workflow_state: str = "IDLE", request_state: str = "READY") -> None:
    agentic_dir = root / ".agentic"
    agentic_dir.mkdir(parents=True)
    (agentic_dir / "workflow_state").write_text(workflow_state + "\n", encoding="utf-8")
    (agentic_dir / "current_work.yaml").write_text(
        "name: test-workflow\n"
        f"state: {request_state}\n"
        "timeout_seconds: 60\n"
        "steps:\n"
        "  - pytest\n",
        encoding="utf-8",
    )


def test_workflow_request_updates_current_work_without_changing_workflow_state(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path)

    result = runner.invoke(app, ["workflow", "request", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Current workflow request file: .agentic/current_work.yaml" in result.output
    assert "Workflow request state: REQUESTED" in result.output
    assert "Next state: IDLE" in result.output
    assert (tmp_path / ".agentic" / "workflow_state").read_text(encoding="utf-8").strip() == "IDLE"
    assert "state: REQUESTED" in (tmp_path / ".agentic" / "current_work.yaml").read_text(encoding="utf-8")


def test_workflow_request_is_idempotent_for_existing_current_work_request(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="REQUESTED")

    result = runner.invoke(app, ["workflow", "request", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".agentic" / "workflow_state").read_text(encoding="utf-8").strip() == "IDLE"
    assert "state: REQUESTED" in (tmp_path / ".agentic" / "current_work.yaml").read_text(encoding="utf-8")


def test_workflow_request_refuses_non_idle_workflow_state(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, workflow_state="UPLOADED")

    result = runner.invoke(app, ["workflow", "request", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "refusing to request workflow from state: UPLOADED" in result.output
    assert "state: READY" in (tmp_path / ".agentic" / "current_work.yaml").read_text(encoding="utf-8")


def test_workflow_status_reports_current_work_state(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="REQUESTED")

    result = runner.invoke(app, ["workflow", "status", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "workflow_state=IDLE" in result.output
    assert "current_work=present" in result.output
    assert "current_work_state=REQUESTED" in result.output



def test_workflow_status_explain_reports_idle_ready_next_step(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="READY")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "workflow_state=IDLE" in result.output
    assert "Interpretation:" in result.output
    assert "No active workflow request." in result.output
    assert "Recommended next step:" in result.output
    assert "Define one concrete slice before requesting workflow automation." in result.output
    assert "Run: agentic-kit workflow request" in result.output
    assert "Then run: agentic-kit workflow run" in result.output


def test_workflow_status_explain_reports_requested_next_step(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="REQUESTED")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "current_work_state=REQUESTED" in result.output
    assert "A workflow request is pending." in result.output
    assert "Run: agentic-kit workflow run" in result.output


def test_workflow_status_explain_reports_uploaded_cleanup_next_step(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, workflow_state="UPLOADED", request_state="READY")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "workflow_state=UPLOADED" in result.output
    assert "cleanup is pending" in result.output
    assert "Run: agentic-kit workflow cleanup" in result.output


def test_workflow_status_explain_reports_failed_inspection_next_step(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, workflow_state="FAILED", request_state="READY")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "workflow_state=FAILED" in result.output
    assert "The last workflow step failed." in result.output
    assert "Run: agentic-kit workflow fail-report" in result.output
    assert "Inspect docs/reports/CURRENT_WORKFLOW_OUTPUT.md and git status before cleanup or retry." in result.output
    assert "Do not rerun workflow automation until the failure cause is understood." in result.output



def test_workflow_status_explain_dirty_tree_stops_automation(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="READY")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Working tree has uncommitted changes." in result.output
    assert "Run: git status --short" in result.output
    assert "Do not start workflow automation until the working tree is clean or intentionally staged." in result.output
    assert "Run: agentic-kit workflow request" not in result.output



def test_workflow_fail_report_refuses_non_failed_state(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, workflow_state="IDLE", request_state="READY")

    result = runner.invoke(app, ["workflow", "fail-report", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "fail-report requires FAILED state, got IDLE" in result.output


def test_workflow_status_explain_states_read_only(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="READY")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "This command is read-only." in result.output


def test_workflow_status_explain_describes_current_report(tmp_path: Path) -> None:
    _write_workflow_files(tmp_path, request_state="READY")
    report = tmp_path / "docs" / "reports" / "CURRENT_WORKFLOW_OUTPUT.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Current workflow output\n", encoding="utf-8")
    result = runner.invoke(app, ["workflow", "status", "--explain", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "current_report=docs/reports/CURRENT_WORKFLOW_OUTPUT.md" in result.output
    assert "current_report points to the latest local workflow-output summary." in result.output



def test_workflow_go_requests_and_runs_one_bounded_step(tmp_path: Path, monkeypatch) -> None:
    _write_workflow_files(tmp_path)
    calls: list[tuple[Path, list[str] | None]] = []

    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
        calls.append((root, extra_args))
        return 0

    import agentic_project_kit.cli_commands.workflow as workflow_module

    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
    result = runner.invoke(app, ["workflow", "go", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Workflow request state: REQUESTED" in result.output
    assert "Running one bounded workflow step." in result.output
    assert "state: REQUESTED" in (tmp_path / ".agentic" / "current_work.yaml").read_text(encoding="utf-8")
    assert calls == [(tmp_path.resolve(), None)]


def test_workflow_go_refuses_non_idle_workflow_state(tmp_path: Path, monkeypatch) -> None:
    _write_workflow_files(tmp_path, workflow_state="FAILED")
    calls: list[tuple[Path, list[str] | None]] = []

    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
        calls.append((root, extra_args))
        return 0

    import agentic_project_kit.cli_commands.workflow as workflow_module

    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
    result = runner.invoke(app, ["workflow", "go", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "refusing to start workflow from state: FAILED" in result.output
    assert calls == []


def test_workflow_upload_output_uploads_latest_bounded_output(tmp_path: Path, monkeypatch) -> None:
    _write_workflow_files(tmp_path)
    calls: list[tuple[Path, list[str] | None]] = []

    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
        calls.append((root, extra_args))
        return 0

    import agentic_project_kit.cli_commands.workflow as workflow_module

    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
    result = runner.invoke(app, ["workflow", "upload-output", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Uploading latest bounded workflow output evidence." in result.output
    assert calls == [(tmp_path.resolve(), ["--upload-output"])]


def test_workflow_upload_output_refuses_already_uploaded_state(tmp_path: Path, monkeypatch) -> None:
    _write_workflow_files(tmp_path, workflow_state="UPLOADED")
    calls: list[tuple[Path, list[str] | None]] = []

    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
        calls.append((root, extra_args))
        return 0

    import agentic_project_kit.cli_commands.workflow as workflow_module

    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
    result = runner.invoke(app, ["workflow", "upload-output", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "output evidence is already uploaded" in result.output
    assert calls == []
