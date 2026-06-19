from __future__ import annotations

from pathlib import Path

from agentic_project_kit import doctor as doctor_module
from agentic_project_kit.standard_gates_audit_suite import (
    StandardGateCheck,
    StandardGatesAuditSuiteResult,
)


def test_doctor_includes_standard_audit_suite_pass(tmp_path: Path, monkeypatch) -> None:
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

