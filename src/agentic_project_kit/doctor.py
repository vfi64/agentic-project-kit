from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentic_project_kit.checks import check_docs, check_todo

ZENODO_ALL_VERSIONS_DOI = "10.5281/zenodo.20101359"
ZENODO_BADGE_FRAGMENT = "zenodo.20101359.svg"


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
        _version_drift_check(root),
        _citation_drift_check(root),
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


def _citation_drift_check(project_root: Path) -> DoctorCheck:
    if not _has_citation_metadata(project_root):
        return DoctorCheck(
            "citation drift",
            DoctorStatus.WARN,
            "citation metadata absent; skipped DOI validation until a DOI/archive is configured",
        )

    missing: list[str] = []

    readme_path = project_root / "README.md"
    if not _file_contains(readme_path, ZENODO_ALL_VERSIONS_DOI):
        missing.append("README.md DOI")
    if not _file_contains(readme_path, ZENODO_BADGE_FRAGMENT):
        missing.append("README.md Zenodo badge")

    citation_path = project_root / "CITATION.cff"
    if not _citation_doi_matches(citation_path):
        missing.append("CITATION.cff DOI")

    zenodo_path = project_root / ".zenodo.json"
    if not zenodo_path.exists():
        missing.append(".zenodo.json")
    else:
        zenodo_text = zenodo_path.read_text(encoding="utf-8")
        if "agentic-project-kit" not in zenodo_text:
            missing.append(".zenodo.json title")
        if "agentic" not in zenodo_text.lower():
            missing.append(".zenodo.json keywords")

    if missing:
        return DoctorCheck("citation drift", DoctorStatus.FAIL, "citation metadata mismatch in: " + ", ".join(missing))
    return DoctorCheck("citation drift", DoctorStatus.PASS, f"Zenodo DOI metadata matches {ZENODO_ALL_VERSIONS_DOI}")


def _has_citation_metadata(project_root: Path) -> bool:
    readme_path = project_root / "README.md"
    citation_path = project_root / "CITATION.cff"
    zenodo_path = project_root / ".zenodo.json"
    return (
        _file_contains(readme_path, ZENODO_ALL_VERSIONS_DOI)
        or _file_contains(readme_path, ZENODO_BADGE_FRAGMENT)
        or _citation_doi_matches(citation_path)
        or zenodo_path.exists()
    )


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


def _citation_doi_matches(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    accepted = (
        f"doi: {ZENODO_ALL_VERSIONS_DOI}",
        f'doi: "{ZENODO_ALL_VERSIONS_DOI}"',
        f"doi: '{ZENODO_ALL_VERSIONS_DOI}'",
    )
    return any(item in text for item in accepted)
