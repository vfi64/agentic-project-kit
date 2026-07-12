from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report, render_doc_lifecycle_report
from agentic_project_kit.doc_lifecycle_sweep import (
    build_doc_lifecycle_bootstrap_payload,
    build_doc_lifecycle_propose_delete_payload,
    build_doc_lifecycle_sweep_payload,
)

runner = CliRunner()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_registry(root: Path, documents: list[dict[str, str]]) -> None:
    _write(
        root / "docs" / "DOCUMENTATION_REGISTRY.yaml",
        yaml.safe_dump(
            {
                "version": 1,
                "status": {"lifecycle": "initial", "broad_migration_allowed": False},
                "documents": documents,
            },
            sort_keys=False,
        ),
    )


def _write_direction(root: Path, source_file: str) -> None:
    _write(
        root / "docs" / "planning" / "PROJECT_DIRECTION.yaml",
        yaml.safe_dump(
            {
                "schema_version": 1,
                "meta": {
                    "status": "active",
                    "authority": "docs/planning/PROJECT_DIRECTION.yaml",
                },
                "strategy": [],
                "roadmap": [],
                "plans": [],
                "ideas": [],
                "done": [
                    {
                        "id": "CLOSED",
                        "title": "Closed item",
                        "completed_by_pr": 1,
                        "source_files": [source_file],
                    }
                ],
                "discarded": [],
            },
            sort_keys=False,
        ),
    )


def test_sweep_plan_reports_one_action_per_finding(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "planning" / "CURRENT.md", "# Current\n\nStatus: active\n")
    _write_registry(
        tmp_path,
        [
            {
                "path": "docs/planning/CURRENT.md",
                "class": "planning",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "sweep", "--root", str(tmp_path), "--dry-run", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_lifecycle_sweep"
    assert payload["mode"] == "dry-run"
    assert payload["mutation"] == "none"
    action_by_id = {item["id"]: item for item in payload["actions"]}
    assert action_by_id["docs/planning/CURRENT.md:HEADER_MISSING"]["action"] == "confirm-current"


def test_sweep_execute_archive_updates_file_registry_and_direction(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "planning" / "OLD.md",
        "# Old\n\nStatus: active\nStatus-date: 2026-01-01\n",
    )
    _write_registry(
        tmp_path,
        [
            {
                "path": "docs/planning/OLD.md",
                "class": "planning",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )
    _write_direction(tmp_path, "docs/planning/OLD.md")

    payload = build_doc_lifecycle_sweep_payload(
        tmp_path,
        execute=True,
        only="docs/planning/OLD.md:SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE",
        today=date(2026, 7, 12),
    )

    assert payload["result_status"] == "PASS"
    assert payload["applied"][0]["action"] == "archive"
    assert not (tmp_path / "docs" / "planning" / "OLD.md").exists()
    archived = tmp_path / "docs" / "archive" / "OLD.md"
    assert archived.exists()
    archived_text = archived.read_text(encoding="utf-8")
    assert "Status: superseded" in archived_text
    assert "Status-date: 2026-07-12" in archived_text
    registry = yaml.safe_load((tmp_path / "docs" / "DOCUMENTATION_REGISTRY.yaml").read_text(encoding="utf-8"))
    assert registry["documents"][0]["path"] == "docs/archive/OLD.md"
    assert registry["documents"][0]["class"] == "historical archive"
    direction = yaml.safe_load((tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.yaml").read_text(encoding="utf-8"))
    assert direction["done"][0]["source_files"] == ["docs/archive/OLD.md"]


def test_sweep_confirm_current_roundtrip_updates_status_date(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "planning" / "CURRENT.md",
        "# Current\n\nDecision status: accepted\nReview policy: required\n",
    )
    _write_registry(
        tmp_path,
        [
            {
                "path": "docs/planning/CURRENT.md",
                "class": "planning",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    payload = build_doc_lifecycle_sweep_payload(
        tmp_path,
        execute=True,
        only="docs/planning/CURRENT.md:HEADER_MISSING",
        today=date(2026, 7, 12),
    )

    assert payload["result_status"] == "PASS"
    text = (tmp_path / "docs" / "planning" / "CURRENT.md").read_text(encoding="utf-8")
    assert "Status: active" in text
    assert "Status-date: 2026-07-12" in text
    report = build_doc_lifecycle_report(tmp_path, now=date(2026, 7, 12))
    assert not any(
        finding.path == "docs/planning/CURRENT.md" and finding.code == "HEADER_MISSING"
        for finding in report.findings
    )


def test_sweep_defer_suppresses_lifecycle_findings_until_date(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "planning" / "REVIEW.md", "# Review\n")
    _write_registry(
        tmp_path,
        [
            {
                "path": "docs/planning/REVIEW.md",
                "class": "planning",
                "owner": "maintainers",
            }
        ],
    )

    payload = build_doc_lifecycle_sweep_payload(
        tmp_path,
        execute=True,
        only="docs/planning/REVIEW.md:missing-status",
        until="2026-08-01",
        today=date(2026, 7, 12),
    )
    report = build_doc_lifecycle_report(tmp_path, now=date(2026, 7, 12))
    rendered = render_doc_lifecycle_report(report)

    assert payload["result_status"] == "PASS"
    assert not any(finding.path == "docs/planning/REVIEW.md" for finding in report.findings)
    assert report.deferred[0].path == "docs/planning/REVIEW.md"
    assert "DEFERRED" in rendered


def test_lifecycle_bootstrap_dry_run_and_execute(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "planning" / "NEW.md"
    _write(target, "# New\n\nbody\n")

    dry_run = build_doc_lifecycle_bootstrap_payload(
        tmp_path,
        execute=False,
        today=date(2026, 7, 12),
    )
    assert dry_run["candidate_count"] == 1
    assert "Status: unreviewed" not in target.read_text(encoding="utf-8")

    execute = build_doc_lifecycle_bootstrap_payload(
        tmp_path,
        execute=True,
        today=date(2026, 7, 12),
    )
    assert execute["applied_count"] == 1
    text = target.read_text(encoding="utf-8")
    assert "Status: unreviewed" in text
    assert "Status-date: 2026-07-12" in text


def test_lifecycle_propose_delete_reports_old_unreferenced_archive_only(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "archive" / "OLD.md",
        "# Old\n\nStatus: superseded\nStatus-date: 2025-01-01\n",
    )
    _write(
        tmp_path / "docs" / "archive" / "REFERENCED.md",
        "# Referenced\n\nStatus: superseded\nStatus-date: 2025-01-01\n",
    )
    _write(tmp_path / "docs" / "planning" / "INDEX.md", "See docs/archive/REFERENCED.md\n")

    payload = build_doc_lifecycle_propose_delete_payload(tmp_path, today=date(2026, 7, 12))

    assert [candidate["path"] for candidate in payload["candidates"]] == ["docs/archive/OLD.md"]


def test_sweep_execute_requires_only(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "planning" / "CURRENT.md", "# Current\n\nStatus: active\n")
    _write_registry(
        tmp_path,
        [
            {
                "path": "docs/planning/CURRENT.md",
                "class": "planning",
                "owner": "maintainers",
                "status": "active",
            }
        ],
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "sweep", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["reason"] == "missing_only"
