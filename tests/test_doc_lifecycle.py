import json
from datetime import date, timedelta
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.checks import doc_lifecycle_audit_command
from agentic_project_kit.doc_lifecycle import (
    build_doc_lifecycle_report,
    build_doc_lifecycle_strict_findings,
    render_doc_lifecycle_report,
    write_doc_lifecycle_json_report,
)
from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REGISTRY_PATH, REQUIRED_CLASS_RULE_FIELDS


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_manifest(root: Path, content: str) -> None:
    _write(root / ".agentic" / "config.yaml", content)


def _class_rules() -> dict[str, dict[str, str]]:
    return {name: {field: f"{name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS} for name in DOCUMENT_CLASSES}


def _write_registry(root: Path) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": [
            {"path": "docs/ideas/EXAMPLE.md", "class": "planning", "owner": "maintainers"},
            {"path": "docs/strategy/NOW.md", "class": "operational/automation", "owner": "maintainers"},
        ],
    }
    _write(root / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _write_registry_documents(root: Path, documents: list[dict[str, str]]) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": documents,
    }
    _write(root / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _write_valid_docs(root: Path) -> None:
    _write(root / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    _write(root / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current\nReview policy: review before milestones\n")


def test_doc_lifecycle_accepts_classified_documents(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    report = build_doc_lifecycle_report(tmp_path)
    assert report.ok
    assert report.registry_summary is None
    assert [document.path for document in report.documents] == ["docs/ideas/EXAMPLE.md", "docs/strategy/NOW.md"]


def test_doc_lifecycle_reports_missing_and_invalid_status(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    _write(tmp_path / "docs/planning/MISSING.md", "# Missing\n\nDecision status: unclear\n")
    report = build_doc_lifecycle_report(tmp_path)
    codes = {finding.code for finding in report.findings}
    assert {"invalid-status", "missing-status", "missing-decision-status"} <= codes


def test_doc_lifecycle_requires_review_policy_for_active_and_idea_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current\n")
    report = build_doc_lifecycle_report(tmp_path)
    assert any(finding.code == "missing-review-policy" for finding in report.findings)


def test_doc_lifecycle_requires_lifecycle_note_for_closed_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/roadmap/DONE.md", "# Done\n\nStatus: implemented\nDecision status: done\n")
    report = build_doc_lifecycle_report(tmp_path)
    assert any(finding.code == "missing-lifecycle-note" for finding in report.findings)


def test_doc_lifecycle_includes_registry_summary_when_available(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    _write_registry(tmp_path)
    report = build_doc_lifecycle_report(tmp_path)
    rendered = render_doc_lifecycle_report(report)
    assert report.ok
    assert report.registry_summary is not None
    assert report.registry_summary["registry_path"] == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert report.registry_summary["document_count"] == 2
    assert report.registry_summary["broad_migration_allowed"] is False
    assert "Documentation registry:" in rendered
    assert "class:operational/automation: 1" in rendered


def test_doc_lifecycle_json_report_has_stable_shape(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    report = build_doc_lifecycle_report(tmp_path)
    output_path = tmp_path / "reports" / "doc-lifecycle-report.json"
    write_doc_lifecycle_json_report(report, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["findings"] == []
    assert payload["registry_summary"] is None
    assert payload["documents"][0]["path"] == "docs/ideas/EXAMPLE.md"


def test_doc_lifecycle_json_report_includes_registry_summary(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    _write_registry(tmp_path)
    output_path = tmp_path / "reports" / "doc-lifecycle-report.json"
    write_doc_lifecycle_json_report(build_doc_lifecycle_report(tmp_path), output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["registry_summary"]["class_counts"]["planning"] == 1


def test_doc_lifecycle_audit_command_exits_nonzero_on_findings(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    with pytest.raises(typer.Exit) as exc_info:
        doc_lifecycle_audit_command(tmp_path)
    assert exc_info.value.exit_code == 1


def test_doc_lifecycle_cli_command_reports_pass(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Documentation lifecycle audit" in result.output
    assert "Overall: PASS" in result.output


def test_doc_lifecycle_cli_command_writes_report(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    output_path = tmp_path / "doc-lifecycle-report.json"
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--report", str(output_path)])
    assert result.exit_code == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["findings"][0]["code"] == "invalid-status"


def test_doc_lifecycle_reports_missing_registry_headers_without_blocking(tmp_path: Path) -> None:
    _write(tmp_path / "docs/governance/RULE.md", "# Rule\n")
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert report.ok
    finding = next(item for item in report.findings if item.code == "HEADER_MISSING")
    assert finding.severity == "WARN"
    assert finding.document_class == "governance/system"


def test_doc_lifecycle_reports_header_registry_status_mismatch(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/governance/RULE.md",
        "# Rule\n\nStatus: superseded\nStatus-date: 2026-07-11\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert any(item.code == "HEADER_REGISTRY_MISMATCH" for item in report.findings)


def test_doc_lifecycle_strict_cli_blocks_header_registry_status_mismatch(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/governance/RULE.md",
        "# Rule\n\nStatus: superseded\nStatus-date: 2026-07-11\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--strict", "--json"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["strict"]["ok"] is False
    assert payload["strict"]["blocker_count"] == 1
    assert payload["strict"]["blockers"][0]["code"] == "HEADER_REGISTRY_MISMATCH"


def test_doc_lifecycle_reports_missing_superseded_target(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/governance/OLD.md",
        "# Old\n\nStatus: superseded\nStatus-date: 2026-07-11\nSuperseded-by: docs/governance/NEW.md\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/OLD.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "superseded",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert any(item.code == "SUPERSEDED_TARGET_MISSING" for item in report.findings)


def test_doc_lifecycle_strict_blocks_release_due_selector(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/governance/RELEASE.md",
        "# Release\n\nStatus: active\nStatus-date: 2026-07-11\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RELEASE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "release:>=0.5.0",
            }
        ],
    )

    result = CliRunner().invoke(
        app,
        [
            "doc-lifecycle-audit",
            "--root",
            str(tmp_path),
            "--current-version",
            "0.5.0",
            "--strict",
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["strict"]["blockers"][0]["code"] == "REVIEW_DUE_RELEASE"


def test_doc_lifecycle_stale_budget_boundary_uses_injected_now(tmp_path: Path) -> None:
    now = date(2026, 7, 11)
    at_budget = now - timedelta(days=180)
    over_budget = now - timedelta(days=181)
    _write(
        tmp_path / "docs/governance/OK.md",
        f"# OK\n\nStatus: active\nStatus-date: {at_budget.isoformat()}\n",
    )
    _write(
        tmp_path / "docs/governance/STALE.md",
        f"# Stale\n\nStatus: active\nStatus-date: {over_budget.isoformat()}\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/OK.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            },
            {
                "path": "docs/governance/STALE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            },
        ],
    )

    report = build_doc_lifecycle_report(tmp_path, now=now)

    stale_findings = [item for item in report.findings if item.code == "STALE_BY_BUDGET"]
    assert [item.path for item in stale_findings] == ["docs/governance/STALE.md"]
    assert stale_findings[0].age_days == 181


def test_doc_lifecycle_stale_budget_uses_workspace_hygiene_budget(tmp_path: Path) -> None:
    now = date(2026, 7, 11)
    old_status_date = now - timedelta(days=31)
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
hygiene:
  review_budgets:
    governance: 30
""",
    )
    _write(
        tmp_path / "docs/governance/STALE.md",
        f"# Stale\n\nStatus: active\nStatus-date: {old_status_date.isoformat()}\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/STALE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path, now=now)

    stale = next(item for item in report.findings if item.code == "STALE_BY_BUDGET")
    assert report.review_budgets["governance"] == 30
    assert stale.message.endswith("governance budget is 30 days")


def test_doc_lifecycle_hygiene_off_suppresses_lifecycle_findings(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
hygiene:
  doc_lifecycle: 'off'
""",
    )
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")

    report = build_doc_lifecycle_report(tmp_path)

    assert report.hygiene_mode == "off"
    assert report.documents[0].path == "docs/ideas/ISSUE.md"
    assert report.findings == ()
    assert report.ok


def test_doc_lifecycle_workspace_strict_mode_blocks_cli_without_flag(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
hygiene:
  doc_lifecycle: strict
""",
    )
    _write(
        tmp_path / "docs/governance/RULE.md",
        "# Rule\n\nStatus: superseded\nStatus-date: 2026-07-11\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["hygiene"]["doc_lifecycle"] == "strict"
    assert payload["strict"]["source"] == "workspace hygiene"
    assert payload["strict"]["blockers"][0]["code"] == "HEADER_REGISTRY_MISMATCH"


def test_time_based_findings_never_fail_strict(tmp_path: Path) -> None:
    now = date(2026, 7, 12)
    old_status_date = now - timedelta(days=181)
    _write(
        tmp_path / "docs/governance/STALE.md",
        f"# Stale\n\nStatus: active\nStatus-date: {old_status_date.isoformat()}\n",
    )
    _write(
        tmp_path / "docs/governance/DATE.md",
        "# Date\n\nStatus: active\nStatus-date: 2026-07-12\n",
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/STALE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
            },
            {
                "path": "docs/governance/DATE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "date:2026-07-12",
            },
        ],
    )

    report = build_doc_lifecycle_report(tmp_path, now=now)

    codes = {finding.code for finding in report.findings}
    assert {"STALE_BY_BUDGET", "REVIEW_DUE_DATE"} <= codes
    assert build_doc_lifecycle_strict_findings(tmp_path, report=report) == ()


def test_doc_lifecycle_exempts_reports_archive_and_examples_from_header_audit(tmp_path: Path) -> None:
    for relative in (
        "docs/reports/REPORT.md",
        "docs/archive/OLD.md",
        "docs/examples/EXAMPLE.md",
    ):
        _write(tmp_path / relative, "# Exempt\n")
    _write_registry_documents(
        tmp_path,
        [
            {"path": "docs/reports/REPORT.md", "class": "evidence/log", "owner": "maintainers"},
            {"path": "docs/archive/OLD.md", "class": "historical archive", "owner": "maintainers"},
            {"path": "docs/examples/EXAMPLE.md", "class": "user-facing description", "owner": "maintainers"},
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert report.findings == ()


def test_doc_lifecycle_audit_json_groups_findings_by_code(tmp_path: Path) -> None:
    _write(tmp_path / "docs/governance/RULE.md", "# Rule\n")
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
            }
        ],
    )

    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["findings_by_code"]["HEADER_MISSING"][0]["class"] == "governance/system"


def test_doc_lifecycle_reports_due_and_invalid_review_after_signals(tmp_path: Path) -> None:
    now = date(2026, 7, 11)
    _write(tmp_path / "docs/governance/DATE.md", "# Date\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write(tmp_path / "docs/governance/FUTURE.md", "# Future\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write(tmp_path / "docs/governance/RELEASE.md", "# Release\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write(tmp_path / "docs/governance/INVALID.md", "# Invalid\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/DATE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "date:2026-07-11",
            },
            {
                "path": "docs/governance/FUTURE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "date:2026-07-12",
            },
            {
                "path": "docs/governance/RELEASE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "release:>=0.4.12",
            },
            {
                "path": "docs/governance/INVALID.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "after next release",
            },
        ],
    )

    report = build_doc_lifecycle_report(tmp_path, now=now, current_version="0.4.12")

    by_path = {(finding.path, finding.code) for finding in report.findings}
    assert ("docs/governance/DATE.md", "REVIEW_DUE_DATE") in by_path
    assert ("docs/governance/RELEASE.md", "REVIEW_DUE_RELEASE") in by_path
    assert ("docs/governance/INVALID.md", "REVIEW_AFTER_INVALID") in by_path
    assert ("docs/governance/FUTURE.md", "REVIEW_DUE_DATE") not in by_path
    assert report.ok


def test_doc_lifecycle_reports_due_direction_review_after(tmp_path: Path) -> None:
    _write(tmp_path / "docs/governance/RULE.md", "# Rule\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write(
        tmp_path / "docs/planning/PROJECT_DIRECTION.yaml",
        yaml.safe_dump(
            {
                "schema_version": 1,
                "meta": {"status": "active", "authority": "docs/planning/PROJECT_DIRECTION.yaml"},
                "strategy": [],
                "roadmap": [],
                "plans": [],
                "ideas": [],
                "done": [{"id": "finished", "source_files": ["docs/governance/RULE.md"]}],
                "discarded": [],
            },
            sort_keys=False,
        ),
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "direction:finished",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert any(finding.code == "REVIEW_DUE_DIRECTION" for finding in report.findings)
    assert report.ok


def test_doc_lifecycle_strict_blocks_direction_and_closed_item_sources(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/governance/RULE.md",
        "# Rule\n\nStatus: active\nStatus-date: 2026-07-11\n",
    )
    _write(
        tmp_path / "docs/planning/PROJECT_DIRECTION.yaml",
        yaml.safe_dump(
            {
                "schema_version": 1,
                "meta": {"status": "active", "authority": "docs/planning/PROJECT_DIRECTION.yaml"},
                "strategy": [],
                "roadmap": [],
                "plans": [],
                "ideas": [],
                "done": [{"id": "finished", "source_files": ["docs/governance/RULE.md"]}],
                "discarded": [],
            },
            sort_keys=False,
        ),
    )
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "direction:finished",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)
    strict_findings = build_doc_lifecycle_strict_findings(tmp_path, report=report)

    codes = {finding.code for finding in strict_findings}
    assert {"REVIEW_DUE_DIRECTION", "SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE"} <= codes


def test_doc_lifecycle_reports_unknown_direction_review_after_as_invalid(tmp_path: Path) -> None:
    _write(tmp_path / "docs/governance/RULE.md", "# Rule\n\nStatus: active\nStatus-date: 2026-07-11\n")
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/governance/RULE.md",
                "class": "governance/system",
                "owner": "maintainers",
                "status": "active",
                "review_after": "direction:missing",
            }
        ],
    )

    report = build_doc_lifecycle_report(tmp_path)

    assert any(finding.code == "REVIEW_AFTER_INVALID" for finding in report.findings)
    assert report.ok


def test_audit_doc_orphans_reports_unreferenced_registered_docs(tmp_path: Path) -> None:
    _write(tmp_path / "docs/kept.md", "# Kept\n")
    _write(tmp_path / "docs/orphan.md", "# Orphan\n")
    _write(tmp_path / "docs/index.md", "See docs/kept.md\n")
    _write_registry_documents(
        tmp_path,
        [
            {"path": "docs/kept.md", "class": "user-facing description", "owner": "maintainers"},
            {"path": "docs/orphan.md", "class": "user-facing description", "owner": "maintainers"},
        ],
    )

    result = CliRunner().invoke(app, ["audit-doc-orphans", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [candidate["path"] for candidate in payload["candidates"]] == ["docs/orphan.md"]


def test_audit_doc_orphans_exempts_configured_and_canonical_paths(tmp_path: Path) -> None:
    exempt_paths = [
        "README.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "SECURITY.md",
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/planning/PROJECT_DIRECTION.md",
        "docs/archive/OLD.md",
        "docs/reports/REPORT.md",
        "docs/examples/EXAMPLE.md",
        "docs/required/KEEP.md",
    ]
    for relative in exempt_paths:
        _write(tmp_path / relative, "# Exempt\n")
    _write(
        tmp_path / "docs/DOC_REGISTRY_SCOPE.yaml",
        yaml.safe_dump(
            {"schema_version": 1, "required_files": ["docs/required/KEEP.md"], "required_paths": [], "exempt_paths": []},
            sort_keys=False,
        ),
    )
    _write_registry_documents(
        tmp_path,
        [{"path": relative, "class": "user-facing description", "owner": "maintainers"} for relative in exempt_paths],
    )

    result = CliRunner().invoke(app, ["audit-doc-orphans", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["candidates"] == []


def test_doc_lifecycle_suggest_review_after_reports_version_targets(tmp_path: Path) -> None:
    _write(tmp_path / "docs/roadmap/PLAN.md", "# Plan\n\nTarget v0.4.13\n")
    _write_registry_documents(
        tmp_path,
        [
            {
                "path": "docs/roadmap/PLAN.md",
                "class": "planning",
                "owner": "maintainers",
            }
        ],
    )

    result = CliRunner().invoke(
        app,
        ["doc-lifecycle-audit", "--root", str(tmp_path), "--suggest-review-after", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["suggestions"] == [
        {
            "matched_text": "Target v0.4.13",
            "path": "docs/roadmap/PLAN.md",
            "review_after": "release:>=0.4.13",
        }
    ]
