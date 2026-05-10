from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from agentic_project_kit.checks import check_docs, check_todo
from agentic_project_kit.contract import (
    CONTRACT_PATH,
    contract_summary,
    load_project_contract,
    validate_project_contract,
)


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
    contract_data = _load_contract_for_doctor(root)
    checks = [
        _path_check(root, "pyproject.toml", required=False),
        _path_check(root, "README.md", required=True),
        _path_check(root, "sentinel.yaml", required=False),
        _path_check(root, ".github/workflows/ci.yml", required=False),
        _project_contract_check(root, contract_data),
        _policy_pack_check(root, contract_data),
        _docs_check(root),
        _todo_check(root),
        _version_drift_check(root),
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


def _load_contract_for_doctor(project_root: Path) -> dict[str, Any] | None | ValueError:
    try:
        return load_project_contract(project_root)
    except ValueError as exc:
        return exc


def _project_contract_check(project_root: Path, data: dict[str, Any] | None | ValueError) -> DoctorCheck:
    if isinstance(data, ValueError):
        return DoctorCheck("project contract", DoctorStatus.FAIL, str(data))
    if data is None:
        return DoctorCheck("project contract", DoctorStatus.WARN, f"{CONTRACT_PATH} absent")
    errors = validate_project_contract(data)
    if errors:
        return DoctorCheck("project contract", DoctorStatus.FAIL, "; ".join(errors))
    return DoctorCheck("project contract", DoctorStatus.PASS, contract_summary(data))


def _policy_pack_check(project_root: Path, data: dict[str, Any] | None | ValueError) -> DoctorCheck:
    if isinstance(data, ValueError):
        return DoctorCheck("policy pack checks", DoctorStatus.WARN, "skipped because project contract is invalid")
    if data is None:
        return DoctorCheck("policy pack checks", DoctorStatus.WARN, f"skipped because {CONTRACT_PATH} is absent")

    contract_errors = validate_project_contract(data)
    if contract_errors:
        return DoctorCheck("policy pack checks", DoctorStatus.WARN, "skipped because project contract failed validation")

    policy_packs = _contract_string_list(data, "policy_packs")
    failures: list[str] = []
    passed: list[str] = []

    for policy_pack in policy_packs:
        errors = _policy_pack_errors(project_root, policy_pack)
        if errors:
            failures.extend(f"{policy_pack}: {error}" for error in errors)
        else:
            passed.append(policy_pack)

    if failures:
        return DoctorCheck("policy pack checks", DoctorStatus.FAIL, "; ".join(failures))
    if not passed:
        return DoctorCheck("policy pack checks", DoctorStatus.WARN, "no policy packs selected")
    return DoctorCheck("policy pack checks", DoctorStatus.PASS, "active: " + ", ".join(passed))


def _policy_pack_errors(project_root: Path, policy_pack: str) -> list[str]:
    checks: dict[str, tuple[str, ...]] = {
        "starter": ("README.md", "AGENTS.md", "docs/STATUS.md"),
        "prototype": ("README.md", "docs/STATUS.md"),
        "solo-maintainer": (
            "docs/STATUS.md",
            "docs/handoff/CURRENT_HANDOFF.md",
            "sentinel.yaml",
            ".agentic/todo.yaml",
        ),
        "agentic-development": (
            "AGENTS.md",
            "docs/TEST_GATES.md",
            "docs/handoff/CURRENT_HANDOFF.md",
            "docs/architecture/ARCHITECTURE_CONTRACT.md",
        ),
        "release-managed": ("CHANGELOG.md", "CITATION.cff", ".zenodo.json"),
        "documentation-governed": (
            "docs/DOCUMENTATION_COVERAGE.yaml",
            "docs/architecture/ARCHITECTURE_CONTRACT.md",
        ),
    }
    required_paths = checks.get(policy_pack, ())
    return [f"missing {path}" for path in required_paths if not (project_root / path).exists()]


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


def _version_drift_check(project_root: Path) -> DoctorCheck:
    version = _read_pyproject_version(project_root / "pyproject.toml")
    if version is None:
        return DoctorCheck("version drift", DoctorStatus.WARN, "pyproject.toml absent or version unavailable")

    missing: list[str] = []
    current_text = f"Current version: {version}"
    changelog_text = f"v{version}"

    if not _file_contains(project_root / "docs/STATUS.md", current_text):
        missing.append("docs/STATUS.md")
    if not _file_contains(project_root / "docs/handoff/CURRENT_HANDOFF.md", current_text):
        missing.append("docs/handoff/CURRENT_HANDOFF.md")
    if not _file_contains(project_root / "CHANGELOG.md", changelog_text):
        missing.append("CHANGELOG.md")

    citation_path = project_root / "CITATION.cff"
    if citation_path.exists() and not _citation_version_matches(citation_path, version):
        missing.append("CITATION.cff")

    if missing:
        return DoctorCheck("version drift", DoctorStatus.FAIL, "version mismatch in: " + ", ".join(missing))
    return DoctorCheck("version drift", DoctorStatus.PASS, f"project state matches version {version}")


def _read_pyproject_version(path: Path) -> str | None:
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    version = project.get("version")
    if isinstance(version, str) and version:
        return version
    return None


def _file_contains(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text(encoding="utf-8")


def _citation_version_matches(path: Path, version: str) -> bool:
    text = path.read_text(encoding="utf-8")
    accepted = (
        f"version: {version}",
        f'version: "{version}"',
        f"version: '{version}'",
    )
    return any(item in text for item in accepted)


def _contract_string_list(data: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = data.get(field_name)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())
