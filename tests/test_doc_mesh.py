import json
from pathlib import Path

import pytest
import typer

from agentic_project_kit.cli_commands.checks import doc_mesh_audit_command, doc_mesh_repair_command
from agentic_project_kit.doc_mesh import (
    HISTORICAL_BANNER,
    apply_doc_mesh_repair_plan,
    build_doc_mesh_repair_plan,
    build_doc_mesh_report,
    write_doc_mesh_json_report,
    write_doc_mesh_repair_plan,
)


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
    _write(root / "docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md", "Documentation information architecture.\n")
    _write(root / "docs/WORKFLOW_OUTPUT_CYCLE.md", "Workflow cycle.\n")
    banner = f"{HISTORICAL_BANNER}\n\n" if historical_banner else ""
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


def test_doc_mesh_classifies_changelog_as_release_history(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)

    report = build_doc_mesh_report(tmp_path)
    documents = {document.path: document for document in report.documents}

    assert documents["CHANGELOG.md"].category == "release-history"
    assert documents["CHANGELOG.md"].required is True
    assert documents["CHANGELOG.md"].historical is False


def test_doc_mesh_ignores_historical_changelog_stale_wording(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path)
    _write(tmp_path / "CHANGELOG.md", "## v1.2.2\n- Prepared on a release-preparation branch.\n")

    report = build_doc_mesh_report(tmp_path)

    assert report.ok
    assert not any(finding.code == "stale-current-state-marker" for finding in report.findings)


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


def test_doc_mesh_json_report_output_contains_stable_shape(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    report = build_doc_mesh_report(tmp_path)
    output_path = tmp_path / "reports" / "doc-mesh-report.json"

    write_doc_mesh_json_report(report, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["documents"]
    documents = {document["path"]: document for document in payload["documents"]}
    assert documents["CHANGELOG.md"]["category"] == "release-history"
    assert documents["CHANGELOG.md"]["required"] is True
    assert documents["CHANGELOG.md"]["historical"] is False
    assert payload["findings"] == [
        {
            "code": "historical-banner-missing",
            "message": "historical or roadmap document must be marked as non-current source of truth",
            "path": "docs/reports/status_roadmap_summary_after_pr105_20260512.md",
        }
    ]


def test_doc_mesh_repair_plan_maps_safe_and_manual_repairs(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    _write(tmp_path / "src/agentic_project_kit/__init__.py", '__version__ = "9.9.9"\n')

    report = build_doc_mesh_report(tmp_path)
    plan = build_doc_mesh_repair_plan(report)

    assert not plan.ok
    repairs = {repair.code: repair for repair in plan.repairs}
    assert repairs["historical-banner-missing"].action == "insert_historical_banner"
    assert repairs["historical-banner-missing"].safe is True
    assert repairs["historical-banner-missing"].mode == "automatic"
    assert repairs["version-mismatch"].action == "align_version_marker"
    assert repairs["version-mismatch"].safe is False
    assert repairs["version-mismatch"].mode == "manual"


def test_doc_mesh_repair_plan_json_output_contains_stable_shape(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    report = build_doc_mesh_report(tmp_path)
    plan = build_doc_mesh_repair_plan(report)
    output_path = tmp_path / "reports" / "doc-mesh-repair-plan.json"

    write_doc_mesh_repair_plan(plan, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == {
        "ok": False,
        "repairs": [
            {
                "action": "insert_historical_banner",
                "code": "historical-banner-missing",
                "mode": "automatic",
                "path": "docs/reports/status_roadmap_summary_after_pr105_20260512.md",
                "reason": "Historical banner insertion is mechanical and does not alter semantic content.",
                "safe": True,
            }
        ],
    }


def test_doc_mesh_repair_inserts_historical_banner(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    target = tmp_path / "docs/reports/status_roadmap_summary_after_pr105_20260512.md"

    report = build_doc_mesh_report(tmp_path)
    plan = build_doc_mesh_repair_plan(report)
    result = apply_doc_mesh_repair_plan(tmp_path, plan)

    assert result.changed is True
    assert result.actions[0].changed is True
    assert target.read_text(encoding="utf-8").startswith(f"{HISTORICAL_BANNER}\n\n# Status")
    assert build_doc_mesh_report(tmp_path).ok


def test_doc_mesh_repair_does_not_duplicate_existing_banner(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=True)
    target = tmp_path / "docs/reports/status_roadmap_summary_after_pr105_20260512.md"
    before = target.read_text(encoding="utf-8")

    report = build_doc_mesh_report(tmp_path)
    plan = build_doc_mesh_repair_plan(report)
    result = apply_doc_mesh_repair_plan(tmp_path, plan)

    assert result.changed is False
    assert target.read_text(encoding="utf-8") == before
    assert before.count(HISTORICAL_BANNER) == 1


def test_doc_mesh_repair_skips_manual_findings(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    init_path = tmp_path / "src/agentic_project_kit/__init__.py"
    _write(init_path, '__version__ = "9.9.9"\n')

    report = build_doc_mesh_report(tmp_path)
    plan = build_doc_mesh_repair_plan(report)
    result = apply_doc_mesh_repair_plan(tmp_path, plan)

    assert result.changed is True
    assert init_path.read_text(encoding="utf-8") == '__version__ = "9.9.9"\n'
    assert any(repair.code == "version-mismatch" for repair in result.skipped)
    remaining_report = build_doc_mesh_report(tmp_path)
    assert any(finding.code == "version-mismatch" for finding in remaining_report.findings)
    assert not any(finding.code == "historical-banner-missing" for finding in remaining_report.findings)


def test_doc_mesh_repair_command_writes_result(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    output_path = tmp_path / "doc-mesh-repair-result.json"

    doc_mesh_repair_command(tmp_path, result_path=output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["changed"] is True
    assert payload["actions"][0]["action"] == "insert_historical_banner"
    assert payload["actions"][0]["changed"] is True
    assert payload["skipped"] == []


def test_doc_mesh_command_writes_report_on_failure(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    output_path = tmp_path / "doc-mesh-report.json"

    with pytest.raises(typer.Exit) as exc_info:
        doc_mesh_audit_command(tmp_path, output_path)

    assert exc_info.value.exit_code == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["findings"][0]["code"] == "historical-banner-missing"


def test_doc_mesh_command_writes_repair_plan_on_failure(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)
    output_path = tmp_path / "doc-mesh-repair-plan.json"

    with pytest.raises(typer.Exit) as exc_info:
        doc_mesh_audit_command(tmp_path, repair_plan_path=output_path)

    assert exc_info.value.exit_code == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["repairs"][0]["action"] == "insert_historical_banner"


def test_doc_mesh_command_reports_failure(tmp_path: Path) -> None:
    _write_minimal_mesh(tmp_path, historical_banner=False)

    with pytest.raises(typer.Exit) as exc_info:
        doc_mesh_audit_command(tmp_path)

    assert exc_info.value.exit_code == 1
