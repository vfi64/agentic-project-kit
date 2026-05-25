from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_finalize_log import finalize_log
from agentic_project_kit.evidence_finalize_log import render_finalize_log_result


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    (root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=root, check=True, capture_output=True, text=True)


def test_finalize_log_rejects_invalid_pass_remote_evidence(tmp_path: Path) -> None:
    run_log = tmp_path / "run.log"
    run_log.write_text("body before finalize\n", encoding="utf-8")
    try:
        finalize_log(
            root=tmp_path,
            run_log=run_log,
            remote_log="docs/reports/terminal/run.log",
            slice_name="FINALIZE TEST",
            scope="TEST",
            mode_check="finalize wrapper test",
            work="PASS",
            evidence="PASS",
            overall="PASS",
            remote_evidence="PENDING",
            pr="NONE",
            ci="not-required",
            merge="not-required",
            command_report="finalize-wrapper-test",
            interpretation="Invalid remote evidence must not pass.",
            safe_step="continue",
        )
    except ValueError as exc:
        assert "remote_evidence" in str(exc)
    else:
        raise AssertionError("invalid remote evidence unexpectedly passed")


def test_finalize_log_rejects_absolute_remote_log(tmp_path: Path) -> None:
    run_log = tmp_path / "run.log"
    run_log.write_text("body before finalize\n", encoding="utf-8")
    try:
        finalize_log(
            root=tmp_path,
            run_log=run_log,
            remote_log=tmp_path / "docs/reports/terminal/run.log",
            slice_name="FINALIZE TEST",
            scope="TEST",
            mode_check="finalize wrapper test",
            work="PASS",
            evidence="PASS",
            overall="PASS",
            remote_evidence="NOT_REQUIRED",
            pr="NONE",
            ci="not-required",
            merge="not-required",
            command_report="finalize-wrapper-test",
            interpretation="Absolute remote log must not pass.",
            safe_step="continue",
        )
    except ValueError as exc:
        assert "repository-relative" in str(exc)
    else:
        raise AssertionError("absolute remote log unexpectedly passed")


def test_finalize_log_render_prints_canonical_summary(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    run_log = tmp_path / "run.log"
    run_log.write_text("body before finalize\n", encoding="utf-8")
    result = finalize_log(
        root=tmp_path,
        run_log=run_log,
        remote_log="docs/reports/terminal/run.log",
        slice_name="VISIBLE SUMMARY TEST",
        scope="TEST / VISIBLE SUMMARY",
        mode_check="visible summary output",
        work="PASS",
        evidence="PASS",
        overall="PASS",
        remote_evidence="NOT_REQUIRED",
        pr="NONE",
        ci="not-required",
        merge="not-required",
        command_report="visible-summary-test",
        interpretation="Finalize-log output must visibly include the canonical summary.",
        safe_step="continue",
    )
    output = render_finalize_log_result(result)
    assert "success: yes" in output
    assert "### CANONICAL SUMMARY ###" in output
    assert "SUMMARY COMM-LOCAL" in output
    assert "NAME: VISIBLE SUMMARY TEST" in output
    assert "REMOTE_EVIDENCE: NOT_REQUIRED" in output
    assert output.rstrip().endswith("### RESULT: PASS ###")


def test_cli_finalize_log_invalid_pass_has_no_traceback(tmp_path: Path) -> None:
    run_log = tmp_path / "run.log"
    run_log.write_text("body before finalize\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "evidence",
            "finalize-log",
            "--root",
            str(tmp_path),
            "--run-log",
            str(run_log),
            "--remote-log",
            "docs/reports/terminal/run.log",
            "--slice",
            "INVALID SUMMARY TEST",
            "--scope",
            "TEST / INVALID SUMMARY",
            "--mode-check",
            "invalid summary output",
            "--remote-evidence",
            "PENDING",
            "--command-report",
            "invalid-summary-test",
            "--interpretation",
            "Invalid remote evidence must fail cleanly.",
            "--safe-step",
            "continue only after clean failure",
        ],
    )
    assert result.exit_code == 1
    assert "EVIDENCE_FINALIZE_LOG" in result.output
    assert "success: no" in result.output
    assert "invalid field: remote_evidence" in result.output
    assert "Traceback" not in result.output
