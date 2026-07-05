from __future__ import annotations

from pathlib import Path

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


def test_direction_validate_cli_passes_current_project_direction() -> None:
    result = CliRunner().invoke(app, ["direction", "validate", "--json"])

    assert result.exit_code == 0
    assert '"status": "PASS"' in result.output


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


def test_direction_validate_rejects_unknown_dependency(tmp_path: Path) -> None:
    direction = _minimal_direction()
    direction["roadmap"][0]["depends_on"] = ["missing-id"]  # type: ignore[index]
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/PROJECT_DIRECTION.yaml").write_text("x\n", encoding="utf-8")

    result = validate_project_direction_data(direction, root=tmp_path)

    assert any(finding.code == "unknown-dependency" for finding in result.findings)


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
