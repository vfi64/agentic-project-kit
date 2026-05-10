from pathlib import Path

from agentic_project_kit.contract import build_contract_data, render_contract_yaml
from agentic_project_kit.doctor import DoctorStatus, build_doctor_report, render_doctor_report


def _write_state_docs(root: Path, version: str = "1.2.3") -> None:
    (root / "docs/handoff").mkdir(parents=True)
    (root / "docs/architecture").mkdir(parents=True)
    (root / "docs/STATUS.md").write_text(
        f"Current version: {version}\n\n## Current Goal\nMaintain project state.\n\n## Next Safe Step\nRun gates.\n",
        encoding="utf-8",
    )
    (root / "docs/TEST_GATES.md").write_text("## Gate Matrix\npytest\n\n## Outcome Reporting\nreport exits\n", encoding="utf-8")
    (root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        f"# Current Handoff\n\nCurrent version: {version}\n\n## Current\nClean.\n\n## Next\nContinue.\n",
        encoding="utf-8",
    )
    (root / "docs/architecture/ARCHITECTURE_CONTRACT.md").write_text(
        "# Architecture Contract and Roadmap\n\n"
        "## 1. Executive Summary\n\n"
        "## 2. How to Use This Document\n\n"
        "## 4. Decision Rules\n\n"
        "## 7. Architectural Contract\n\n"
        "## 16. Acceptance Criteria for Future Work\n",
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


def _write_project_contract(root: Path) -> None:
    (root / ".agentic").mkdir(parents=True)
    data = build_contract_data(
        name="demo",
        description="Demo project",
        project_type="python-cli",
        profiles=("generic-git-repo", "python-cli"),
        policy_packs=("starter", "solo-maintainer"),
    )
    (root / ".agentic/project.yaml").write_text(render_contract_yaml(data), encoding="utf-8")


def _write_version_files(root: Path, version: str = "1.2.3", *, quoted_citation: bool = False) -> None:
    (root / "pyproject.toml").write_text(f"[project]\nversion = \"{version}\"\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(f"# Changelog\n\n## v{version}\n", encoding="utf-8")
    citation_version = f'"{version}"' if quoted_citation else version
    (root / "CITATION.cff").write_text(f"cff-version: 1.2.0\nversion: {citation_version}\n", encoding="utf-8")


def _write_readme(root: Path) -> None:
    (root / "README.md").write_text("# Demo\n\ndoctor-fixture-term\n", encoding="utf-8")


def test_doctor_report_passes_with_minimal_state_docs(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path)

    report = build_doctor_report(tmp_path)

    assert report.ok
    assert [check.status for check in report.checks] == [
        DoctorStatus.WARN,
        DoctorStatus.PASS,
        DoctorStatus.WARN,
        DoctorStatus.WARN,
        DoctorStatus.WARN,
        DoctorStatus.PASS,
        DoctorStatus.WARN,
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


def test_doctor_report_reports_valid_project_contract(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path)
    _write_project_contract(tmp_path)

    report = build_doctor_report(tmp_path)

    contract_check = report.checks[4]
    assert contract_check.name == "project contract"
    assert contract_check.status == DoctorStatus.PASS
    assert "profiles: generic-git-repo, python-cli" in contract_check.detail


def test_doctor_report_fails_on_invalid_project_contract(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/project.yaml").write_text(
        "version: 1\nproject: {}\nprofiles: [missing]\npolicy_packs: [starter]\ngovernance: {}\n",
        encoding="utf-8",
    )

    report = build_doctor_report(tmp_path)

    assert not report.ok
    contract_check = report.checks[4]
    assert contract_check.name == "project contract"
    assert contract_check.status == DoctorStatus.FAIL
    assert "project.name is required" in contract_check.detail
    assert "unknown profile: missing" in contract_check.detail


def test_doctor_report_passes_when_versions_match(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path, "1.2.3")
    _write_version_files(tmp_path, "1.2.3")

    report = build_doctor_report(tmp_path)

    assert report.ok
    version_check = report.checks[-1]
    assert version_check.name == "version drift"
    assert version_check.status == DoctorStatus.PASS
    assert "1.2.3" in version_check.detail


def test_doctor_report_accepts_quoted_citation_versions(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path, "1.2.3")
    _write_version_files(tmp_path, "1.2.3", quoted_citation=True)

    report = build_doctor_report(tmp_path)

    assert report.ok
    assert report.checks[-1].status == DoctorStatus.PASS


def test_doctor_report_fails_on_version_drift(tmp_path: Path):
    _write_readme(tmp_path)
    _write_state_docs(tmp_path, "1.2.2")
    _write_version_files(tmp_path, "1.2.3")

    report = build_doctor_report(tmp_path)

    assert not report.ok
    version_check = report.checks[-1]
    assert version_check.name == "version drift"
    assert version_check.status == DoctorStatus.FAIL
    assert "docs/STATUS.md" in version_check.detail
    assert "docs/handoff/CURRENT_HANDOFF.md" in version_check.detail
