from pathlib import Path

from agentic_project_kit.evidence_finalize_log import finalize_log


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
