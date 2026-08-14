from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.project_direction import (
    audit_project_direction_drift,
    load_project_direction,
    render_project_direction,
    validate_project_direction_data,
)


def test_project_direction_yaml_validates() -> None:
    direction = load_project_direction(Path("."))

    assert direction.validate() == []
    assert direction.data["meta"]["authority"] == "docs/planning/PROJECT_DIRECTION.yaml"


def test_project_direction_text_output_contains_sections() -> None:
    direction = load_project_direction(Path("."))

    rendered = render_project_direction(direction, section="all", output_format="text")

    assert "PROJECT DIRECTION" in rendered
    assert "Strategic direction updated after PR" in rendered
    assert "Strategy" in rendered
    assert "Roadmap" in rendered
    assert "Plans" in rendered
    assert "Ideas" in rendered
    assert "p1-planning-consolidation" in rendered
    assert "direction-schema-command-migration" in rendered


def test_project_direction_json_section_output() -> None:
    direction = load_project_direction(Path("."))

    rendered = render_project_direction(direction, section="roadmap", output_format="json")

    assert '"roadmap"' in rendered
    assert '"p1-planning-consolidation"' in rendered
    assert '"strategy"' not in rendered


def test_project_direction_cli_markdown() -> None:
    result = CliRunner().invoke(app, ["project-direction", "--section", "strategy", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# Project Direction" in result.output
    assert "## Strategy" in result.output
    assert "Governed operating model" in result.output


def test_project_direction_cli_json() -> None:
    result = CliRunner().invoke(app, ["project-direction", "--section", "ideas", "--format", "json"])

    assert result.exit_code == 0
    assert '"ideas"' in result.output
    assert "project-direction-gui-panel" in result.output


def _minimal_direction() -> dict[str, object]:
    return {
        "schema_version": 1,
        "meta": {
            "owner": "maintainers",
            "status": "active",
            "updated_after_pr": None,
            "update_policy": "update after successful slice",
            "authority": "docs/planning/PROJECT_DIRECTION.yaml",
        },
        "strategy": [
            {
                "id": "strategy-a",
                "status": "active",
                "title": "Strategy A",
                "source_files": ["docs/planning/PROJECT_DIRECTION.yaml"],
            }
        ],
        "roadmap": [
            {
                "id": "roadmap-a",
                "phase": "unphased",
                "status": "next",
                "title": "Roadmap A",
                "depends_on": ["strategy-a"],
                "acceptance": [],
                "source_files": ["docs/planning/PROJECT_DIRECTION.yaml"],
            }
        ],
        "plans": [],
        "ideas": [],
        "done": [
            {
                "id": "done-a",
                "completed_by_pr": None,
                "completion_exception": "fixture",
                "merge_commit": None,
                "evidence": [],
                "source_files": ["docs/planning/PROJECT_DIRECTION.yaml"],
            }
        ],
        "discarded": [
            {
                "id": "discarded-a",
                "reason": "fixture",
                "discarded_at": "2026-07-05",
                "source_files": ["docs/planning/PROJECT_DIRECTION.yaml"],
            }
        ],
    }


def _write_project_direction_fixture(root: Path, direction: dict[str, object]) -> None:
    path = root / "docs/planning/PROJECT_DIRECTION.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(direction, sort_keys=False), encoding="utf-8")


def test_direction_validate_cli_passes_current_project_direction() -> None:
    result = CliRunner().invoke(app, ["direction", "validate", "--json"])

    assert result.exit_code == 0
    assert '"status": "PASS"' in result.output


def test_rule_registry_hardening_acceptance_mentions_retirement_trigger() -> None:
    direction = load_project_direction(Path("."))
    items = [
        entry
        for section in ("strategy", "roadmap", "plans", "ideas")
        for entry in direction.data[section]
    ]
    item = next(entry for entry in items if entry["id"] == "rule-registry-hardening")

    assert any("retirement_trigger" in line for line in item["acceptance"])


def test_direction_validate_rejects_duplicate_ids(tmp_path: Path) -> None:
    direction = _minimal_direction()
    direction["ideas"] = [
        {
            "id": "strategy-a",
            "status": "candidate",
            "title": "Duplicate",
            "decision_needed": True,
            "source_files": ["docs/planning/PROJECT_DIRECTION.yaml"],
        }
    ]
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")

    result = validate_project_direction_data(direction, root=tmp_path)

    assert result.status == "FAIL"
    assert any(finding.code == "duplicate-id" for finding in result.findings)


def test_direction_audit_drift_reports_active_source_of_closed_item(tmp_path: Path) -> None:
    direction = _minimal_direction()
    done_items = direction["done"]
    assert isinstance(done_items, list)
    done_items[0]["source_files"] = ["docs/planning/CLOSED.md"]
    _write_project_direction_fixture(tmp_path, direction)
    (tmp_path / "docs/planning/CLOSED.md").write_text(
        "# Closed\n\nStatus: active\nStatus-date: 2026-07-11\n",
        encoding="utf-8",
    )

    result = audit_project_direction_drift(tmp_path)

    record = next(
        item for item in result.records if item.classification == "SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE"
    )
    assert record.path == "docs/planning/CLOSED.md"
    assert record.item_id == "done-a"
    assert record.item_status == "done"


def test_direction_audit_drift_reports_open_item_with_current_release_evidence(tmp_path: Path) -> None:
    direction = _minimal_direction()
    roadmap = direction["roadmap"]
    assert isinstance(roadmap, list)
    roadmap[0]["evidence"] = ["GitHub release https://github.example/releases/tag/v1.2.3"]
    _write_project_direction_fixture(tmp_path, direction)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )

    result = audit_project_direction_drift(tmp_path)

    record = next(
        item for item in result.records if item.classification == "OPEN_ITEM_REFERENCES_CURRENT_RELEASE"
    )
    assert record.path == "docs/planning/PROJECT_DIRECTION.yaml"
    assert record.item_id == "roadmap-a"
    assert record.item_status == "next"
    assert record.reference_count == 1


def test_direction_audit_drift_reports_open_item_with_passed_target_release(tmp_path: Path) -> None:
    direction = _minimal_direction()
    roadmap = direction["roadmap"]
    assert isinstance(roadmap, list)
    roadmap[0]["target_release"] = "v1.1.0"
    _write_project_direction_fixture(tmp_path, direction)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )

    result = audit_project_direction_drift(tmp_path)

    record = next(
        item for item in result.records if item.classification == "OPEN_ITEM_TARGET_RELEASE_PASSED"
    )
    assert record.item_id == "roadmap-a"
    assert record.item_status == "next"


def test_direction_validate_rejects_unknown_dependency(tmp_path: Path) -> None:
    direction = _minimal_direction()
    direction["roadmap"][0]["depends_on"] = ["missing-id"]  # type: ignore[index]
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")

    result = validate_project_direction_data(direction, root=tmp_path)

    assert any(finding.code == "unknown-dependency" for finding in result.findings)


def test_direction_validate_requires_updated_after_pr_semantics_when_set(tmp_path: Path) -> None:
    direction = _minimal_direction()
    meta = direction["meta"]
    assert isinstance(meta, dict)
    meta["updated_after_pr"] = 1860

    result = validate_project_direction_data(direction, root=tmp_path)

    assert any(finding.code == "invalid-updated-after-pr-semantics" for finding in result.findings)
    assert any(
        finding.code == "invalid-updated-after-pr-current-main-claim"
        for finding in result.findings
    )


def test_direction_validate_accepts_updated_after_pr_as_strategic_marker(tmp_path: Path) -> None:
    direction = _minimal_direction()
    meta = direction["meta"]
    assert isinstance(meta, dict)
    meta["updated_after_pr"] = 1860
    meta["updated_after_pr_semantics"] = "strategic_direction_refresh"
    meta["updated_after_pr_current_main_claimed"] = False

    result = validate_project_direction_data(direction, root=tmp_path)

    assert not any(finding.code.startswith("invalid-updated-after-pr") for finding in result.findings)


def test_direction_validate_rejects_open_item_with_passed_target_release(tmp_path: Path) -> None:
    direction = _minimal_direction()
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.5.0"\n',
        encoding="utf-8",
    )
    roadmap = direction["roadmap"]
    assert isinstance(roadmap, list)
    roadmap[0]["target_release"] = "v0.4.12"

    result = validate_project_direction_data(direction, root=tmp_path)

    assert any(finding.code == "stale-target-release" for finding in result.findings)


def test_direction_validate_allows_done_item_with_historical_target_release(tmp_path: Path) -> None:
    direction = _minimal_direction()
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.5.0"\n',
        encoding="utf-8",
    )
    roadmap = direction["roadmap"]
    assert isinstance(roadmap, list)
    roadmap[0]["status"] = "done"
    roadmap[0]["target_release"] = "v0.4.12"

    result = validate_project_direction_data(direction, root=tmp_path)

    assert not any(finding.code == "stale-target-release" for finding in result.findings)


def test_direction_validate_allows_deleted_source_mapping(tmp_path: Path) -> None:
    direction = _minimal_direction()
    direction["strategy"][0]["source_files"] = [  # type: ignore[index]
        {"path": "docs/planning/old.md", "deleted_source": True}
    ]
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")

    result = validate_project_direction_data(direction, root=tmp_path)

    assert not any(finding.code == "missing-source-file" for finding in result.findings)


def test_direction_validate_rejects_private_absolute_paths(tmp_path: Path) -> None:
    direction = _minimal_direction()
    direction["strategy"][0]["source_files"] = ["/Users/example/private.md"]  # type: ignore[index]

    result = validate_project_direction_data(direction, root=tmp_path)

    assert any(finding.code == "private-absolute-path" for finding in result.findings)


def test_direction_validate_strict_planning_files_blocks_free_markdown(tmp_path: Path) -> None:
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")
    (tmp_path / "docs/planning/FREE_PLAN.md").write_text("# Free\n", encoding="utf-8")

    result = validate_project_direction_data(
        _minimal_direction(),
        root=tmp_path,
        strict_planning_files=True,
    )

    assert any(finding.code == "forbidden-free-planning-file" for finding in result.findings)


def test_direction_render_cli_writes_tmp_output(tmp_path: Path) -> None:
    output = tmp_path / "direction.md"
    result = CliRunner().invoke(
        app,
        ["direction", "render", "--format", "markdown", "--output", f"tmp/{output.name}"],
    )

    assert result.exit_code == 0
    rendered = Path("tmp") / output.name
    assert rendered.exists()
    try:
        assert "# Project Direction" in rendered.read_text(encoding="utf-8")
    finally:
        rendered.unlink()


def test_direction_render_cli_rejects_committed_output_path() -> None:
    result = CliRunner().invoke(
        app,
        ["direction", "render", "--format", "markdown", "--output", "docs/planning/PROJECT_DIRECTION.md"],
    )

    assert result.exit_code != 0
    assert "output must be under tmp/" in result.output


def test_direction_audit_drift_reports_unlisted_referenced_file(tmp_path: Path) -> None:
    planning = tmp_path / "docs/planning"
    planning.mkdir(parents=True)
    (planning / "PROJECT_DIRECTION.yaml").write_text(
        Path("docs/planning/PROJECT_DIRECTION.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (planning / "PROJECT_DIRECTION.md").write_text("# View\n", encoding="utf-8")
    (planning / "OLD_PLAN.md").write_text("# Old\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("See docs/planning/OLD_PLAN.md\n", encoding="utf-8")

    result = audit_project_direction_drift(tmp_path)

    records = {record.path: record for record in result.records}
    assert records["docs/planning/OLD_PLAN.md"].classification == "unlisted_referenced_file"


def test_direction_audit_drift_cli_json() -> None:
    result = CliRunner().invoke(app, ["direction", "audit-drift", "--json"])

    assert result.exit_code == 0
    assert '"kind": "project_direction_drift_audit"' in result.output
