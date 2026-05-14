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
