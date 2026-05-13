from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.doc_mesh import build_doc_mesh_report


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_minimal_mesh(root: Path, *, version: str = "1.2.3", historical_banner: bool = True) -> None:
    _write(root / "pyproject.toml", f'[project]\nversion = "{version}"\n')
    _write(root / "src/agentic_project_kit/__init__.py", f'__version__ = "{version}"\n')
    _write(root / "README.md", f'Version `{version}` is current.\n')
    _write(root / "CHANGELOG.md", f'## v{version}\n')
    _write(root / "CITATION.cff", f'version: {version}\n')
    _write(root / "docs/STATUS.md", f'Current version: {version}\nCurrent release state.\n')
    _write(root / "docs/handoff/CURRENT_HANDOFF.md", f'Current version: {version}\nCurrent handoff.\n')
    _write(root / "AGENTS.md", "Agent rules.\n")
    _write(root / "docs/TEST_GATES.md", "Test gates.\n")
    _write(root / "docs/DOCUMENTATION_COVERAGE.yaml", "version: 1\nrules: []\n")
    _write(root / "sentinel.yaml", "documents: []\n")
    _write(root / ".agentic/project.yaml", "name: demo\n")
    _write(root / "docs/architecture/ARCHITECTURE_CONTRACT.md", "Architecture contract.\n")
    _write(root / "docs/WORKFLOW_OUTPUT_CYCLE.md", "Workflow cycle.\n")
    banner = "This file is historical audit evidence, not the current source of truth.\n\n" if historical_banner else ""
    _write(
        root / "docs/reports/status_roadmap_summary_after_pr105_20260512.md",
        banner + "# Status and roadmap summary after PR 105\n",
    )


def test_doc_mesh_accepts_consistent_minimal_project(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)

    report = build_doc_mesh_report(tmp_path)

    assert report.ok
    assert not report.findings


def test_doc_mesh_detects_version_mismatch(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)
    _write(tmp_path / "src/agentic_project_kit/__init__.py", '__version__ = "9.9.9"\n')

    report = build_doc_mesh_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "version-mismatch" for finding in report.findings)


def test_doc_mesh_detects_historical_report_without_banner(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)

    report = build_doc_mesh_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "historical-banner-missing" for finding in report.findings)


def test_doc_mesh_detects_stale_current_state_marker(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)
    _write(tmp_path / "docs/STATUS.md", "Current version: 1.2.3\nThis is a release candidate.\n")

    report = build_doc_mesh_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "stale-current-state-marker" for finding in report.findings)


def test_doc_mesh_detects_release_doi_list_drift(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)
    _write(
        tmp_path / "README.md",
        "Version `1.2.3` is current.\n"
        "The archived v1.2.3 release has the verified version-specific DOI: `10.5281/zenodo.111`.\n",
    )
    _write(
        tmp_path / "CITATION.cff",
        "version: 1.2.3\n"
        "# Verified v1.2.3 version DOI: 10.5281/zenodo.111\n"
        "# Verified v1.2.4 version DOI: 10.5281/zenodo.222\n",
    )

    report = build_doc_mesh_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "release-doi-list-mismatch" for finding in report.findings)


def test_doc_mesh_cli_reports_failure(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    runner = CliRunner()

    result = runner.invoke(app, ["doc-mesh-audit", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Documentation mesh audit" in result.stdout
    assert "historical-banner-missing" in result.stdout
