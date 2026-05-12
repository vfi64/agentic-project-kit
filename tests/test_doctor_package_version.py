from pathlib import Path

from agentic_project_kit.doctor import DoctorStatus, build_doctor_report


def _write_minimal_project(root: Path, *, pyproject_version: str, init_version: str) -> None:
    (root / "pyproject.toml").write_text(f'[project]\nversion = "{pyproject_version}"\n', encoding="utf-8")
    (root / "README.md").write_text("# Demo\n\ndoctor-fixture-term\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(f"# Changelog\n\n## v{pyproject_version}\n", encoding="utf-8")
    (root / "CITATION.cff").write_text(
        f"cff-version: 1.2.0\nversion: {pyproject_version}\n",
        encoding="utf-8",
    )

    (root / "docs/handoff").mkdir(parents=True)
    (root / "docs/architecture").mkdir(parents=True)
    (root / "docs/STATUS.md").write_text(f"Current version: {pyproject_version}\n", encoding="utf-8")
    (root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        f"Current version: {pyproject_version}\n",
        encoding="utf-8",
    )
    (root / "docs/TEST_GATES.md").write_text("## Gate Matrix\n\n## Outcome Reporting\n", encoding="utf-8")
    (root / "docs/architecture/ARCHITECTURE_CONTRACT.md").write_text(
        "# Architecture Contract and Roadmap\n\n"
        "## 1. Executive Summary\n\n"
        "## 2. How to Use This Document\n\n"
        "## 4. Decision Rules\n\n"
        "## 7. Architectural Contract\n\n"
        "## 17. Acceptance Criteria for Future Work\n",
        encoding="utf-8",
    )
    (root / "docs/DOCUMENTATION_COVERAGE.yaml").write_text(
        "version: 1\n"
        "rules:\n"
        "  - id: doctor-test-minimal\n"
        "    documents:\n"
        "      - path: README.md\n"
        "        terms:\n"
        "          - doctor-fixture-term\n",
        encoding="utf-8",
    )

    package_dir = root / "src/agentic_project_kit"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(f'__version__ = "{init_version}"\n', encoding="utf-8")


def test_doctor_detects_package_init_version_drift(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path, pyproject_version="1.2.3", init_version="1.2.2")

    report = build_doctor_report(tmp_path)

    version_check = report.checks[-1]
    assert not report.ok
    assert version_check.name == "version drift"
    assert version_check.status == DoctorStatus.FAIL
    assert "src/agentic_project_kit/__init__.py" in version_check.detail


def test_doctor_accepts_matching_package_init_version(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path, pyproject_version="1.2.3", init_version="1.2.3")

    report = build_doctor_report(tmp_path)

    version_check = report.checks[-1]
    assert version_check.name == "version drift"
    assert version_check.status == DoctorStatus.PASS
    assert "project state matches version 1.2.3" in version_check.detail
