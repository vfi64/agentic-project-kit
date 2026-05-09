from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentic_project_kit.checks import check_docs, check_todo


class DoctorStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: DoctorStatus
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    project_root: Path
    checks: list[DoctorCheck]

    @property
    def ok(self) -> bool:
        return all(check.status is not DoctorStatus.FAIL for check in self.checks)


def build_doctor_report(project_root: Path) -> DoctorReport:
    """Build a compact health report for an agentic project checkout."""
    root = project_root.resolve()
    checks = [
        _path_check(root, "pyproject.toml", required=False),
        _path_check(root, "README.md", required=True),
        _path_check(root, "sentinel.yaml", required=False),
        _path_check(root, ".github/workflows/ci.yml", required=False),
        _docs_check(root),
        _todo_check(root),
    ]
    return DoctorReport(project_root=root, checks=checks)


def render_doctor_report(report: DoctorReport) -> str:
    lines = [f"Agentic project doctor report for {report.project_root}", ""]
    for check in report.checks:
        lines.append(f"[{check.status.value}] {check.name}: {check.detail}")
    lines.extend(["", f"Overall: {'PASS' if report.ok else 'FAIL'}"])
    return "\n".join(lines)


def _path_check(project_root: Path, relative_path: str, *, required: bool) -> DoctorCheck:
    path = project_root / relative_path
    if path.exists():
        return DoctorCheck(relative_path, DoctorStatus.PASS, "present")
    if required:
        return DoctorCheck(relative_path, DoctorStatus.FAIL, "missing")
    return DoctorCheck(relative_path, DoctorStatus.WARN, "missing optional project file")


def _docs_check(project_root: Path) -> DoctorCheck:
    errors = check_docs(project_root)
    if errors:
        return DoctorCheck("documentation gates", DoctorStatus.FAIL, "; ".join(errors))
    return DoctorCheck("documentation gates", DoctorStatus.PASS, "passed")


def _todo_check(project_root: Path) -> DoctorCheck:
    sentinel_path = project_root / "sentinel.yaml"
    if not sentinel_path.exists():
        return DoctorCheck("todo gates", DoctorStatus.WARN, "sentinel.yaml absent; skipped TODO validation")
    errors = check_todo(project_root)
    if errors:
        return DoctorCheck("todo gates", DoctorStatus.FAIL, "; ".join(errors))
    return DoctorCheck("todo gates", DoctorStatus.PASS, "passed")
