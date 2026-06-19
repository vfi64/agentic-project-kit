from __future__ import annotations

from pathlib import Path

from agentic_project_kit import doctor as doctor_module
from agentic_project_kit.standard_gates_audit_suite import (
    StandardGateCheck,
    StandardGatesAuditSuiteResult,
)



def _make_toolkit_checkout(path: Path) -> None:
    (path / "src" / "agentic_project_kit").mkdir(parents=True)
    (path / "docs" / "reference").mkdir(parents=True)
    (path / "docs" / "reference" / "agentic-kit-commands.json").write_text("[]\n", encoding="utf-8")
    (path / "pyproject.toml").write_text("[project]\nname='agentic-project-kit'\nversion='9.9.9'\n", encoding="utf-8")


def test_doctor_includes_standard_audit_suite_pass(tmp_path: Path, monkeypatch) -> None:
    _make_toolkit_checkout(tmp_path)
    def fake(project_root: Path) -> StandardGatesAuditSuiteResult:
        return StandardGatesAuditSuiteResult(
            root=project_root.as_posix(),
            version="9.9.9",
            checks=(StandardGateCheck("audit-doc-currency", "PASS", "ok", 0),),
        )

    monkeypatch.setattr(doctor_module, "evaluate_standard_gates_audit_suite", fake)

    report = doctor_module.build_doctor_report(tmp_path)

    assert any(
        check.name == "standard audit suite"
        and check.status is doctor_module.DoctorStatus.PASS
        for check in report.checks
    )


def test_doctor_fails_when_standard_audit_suite_fails(tmp_path: Path, monkeypatch) -> None:
    _make_toolkit_checkout(tmp_path)
    def fake(project_root: Path) -> StandardGatesAuditSuiteResult:
        return StandardGatesAuditSuiteResult(
            root=project_root.as_posix(),
            version="9.9.9",
            checks=(StandardGateCheck("audit-doc-currency", "FAIL", "drift", 1),),
        )

    monkeypatch.setattr(doctor_module, "evaluate_standard_gates_audit_suite", fake)

    report = doctor_module.build_doctor_report(tmp_path)

    assert any(
        check.name == "standard audit suite"
        and check.status is doctor_module.DoctorStatus.FAIL
        and "audit-doc-currency" in check.detail
        for check in report.checks
    )

def test_doctor_warns_when_standard_audit_suite_executable_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    _make_toolkit_checkout(tmp_path)
    def fake(project_root: Path) -> StandardGatesAuditSuiteResult:
        raise FileNotFoundError("agentic-kit")

    monkeypatch.setattr(doctor_module, "evaluate_standard_gates_audit_suite", fake)

    report = doctor_module.build_doctor_report(tmp_path)

    assert any(
        check.name == "standard audit suite"
        and check.status is doctor_module.DoctorStatus.WARN
        and "agentic-kit executable is unavailable" in check.detail
        for check in report.checks
    )

def test_doctor_skips_standard_audit_suite_outside_toolkit_checkout(tmp_path: Path, monkeypatch) -> None:
    called = False

    def fake(project_root: Path) -> StandardGatesAuditSuiteResult:
        nonlocal called
        called = True
        raise AssertionError("standard suite must not run outside toolkit checkout")

    monkeypatch.setattr(doctor_module, "evaluate_standard_gates_audit_suite", fake)

    report = doctor_module.build_doctor_report(tmp_path)

    assert called is False
    assert any(
        check.name == "standard audit suite"
        and check.status is doctor_module.DoctorStatus.WARN
        and "outside the agentic-project-kit development checkout" in check.detail
        for check in report.checks
    )


def test_doctor_runs_standard_audit_suite_inside_toolkit_checkout(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "src" / "agentic_project_kit").mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "reference" / "agentic-kit-commands.json").write_text("[]\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='9.9.9'\n", encoding="utf-8")
    called = False

    def fake(project_root: Path) -> StandardGatesAuditSuiteResult:
        nonlocal called
        called = True
        return StandardGatesAuditSuiteResult(
            root=project_root.as_posix(),
            version="9.9.9",
            checks=(StandardGateCheck("audit-doc-currency", "PASS", "ok", 0),),
        )

    monkeypatch.setattr(doctor_module, "evaluate_standard_gates_audit_suite", fake)

    report = doctor_module.build_doctor_report(tmp_path)

    assert called is True
    assert any(
        check.name == "standard audit suite"
        and check.status is doctor_module.DoctorStatus.PASS
        for check in report.checks
    )

