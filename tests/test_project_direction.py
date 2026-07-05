from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.project_direction import load_project_direction, render_project_direction


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
