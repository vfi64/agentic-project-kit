from pathlib import Path

from agentic_project_kit.doctor import DoctorStatus, build_doctor_report, render_doctor_report


def _write_state_docs(root: Path) -> None:
    (root / "docs/handoff").mkdir(parents=True)
    (root / "docs/STATUS.md").write_text("## Current Goal\nMaintain project state.\n\n## Next Safe Step\nRun gates.\n", encoding="utf-8")
    (root / "docs/TEST_GATES.md").write_text("## Gate Matrix\npytest\n\n## Outcome Reporting\nreport exits\n", encoding="utf-8")
    (root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        "# Current Handoff\n\n## Current\nClean.\n\n## Next\nContinue.\n",
        encoding="utf-8",
    )


def test_doctor_report_passes_with_minimal_state_docs(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    _write_state_docs(tmp_path)

    report = build_doctor_report(tmp_path)

    assert report.ok
    assert [check.status for check in report.checks] == [
        DoctorStatus.WARN,
        DoctorStatus.PASS,
        DoctorStatus.WARN,
        DoctorStatus.WARN,
        DoctorStatus.PASS,
        DoctorStatus.WARN,
    ]
    assert "Overall: PASS" in render_doctor_report(report)


def test_doctor_report_fails_without_required_readme(tmp_path: Path):
    _write_state_docs(tmp_path)

    report = build_doctor_report(tmp_path)

    assert not report.ok
    assert report.checks[1].name == "README.md"
    assert report.checks[1].status == DoctorStatus.FAIL
    assert "Overall: FAIL" in render_doctor_report(report)
