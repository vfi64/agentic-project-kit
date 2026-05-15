from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.patterns import PatternCatalogError, load_pattern_catalog, load_pattern_detail


def test_load_pattern_catalog_reads_local_catalog() -> None:
    catalog = load_pattern_catalog(Path("."))

    assert catalog.version == 1
    assert [entry.id for entry in catalog.patterns] == ["bounded-workflow-evidence", "hidden-autopilot"]
    assert catalog.patterns[0].kind == "pattern"
    assert catalog.patterns[1].kind == "anti-pattern"


def test_load_pattern_catalog_rejects_duplicate_ids(tmp_path: Path) -> None:
    catalog_dir = tmp_path / ".agentic" / "patterns"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "catalog.yaml").write_text(
        "version: 1\n"
        "patterns:\n"
        "  - id: duplicate\n"
        "    title: First\n"
        "    kind: pattern\n"
        "    summary: First summary.\n"
        "    doc: docs/patterns/first.md\n"
        "  - id: duplicate\n"
        "    title: Second\n"
        "    kind: pattern\n"
        "    summary: Second summary.\n"
        "    doc: docs/patterns/second.md\n",
        encoding="utf-8",
    )

    with pytest.raises(PatternCatalogError, match="duplicate pattern id: duplicate"):
        load_pattern_catalog(tmp_path)


def test_load_pattern_catalog_rejects_invalid_kind(tmp_path: Path) -> None:
    catalog_dir = tmp_path / ".agentic" / "patterns"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "catalog.yaml").write_text(
        "version: 1\n"
        "patterns:\n"
        "  - id: demo\n"
        "    title: Demo\n"
        "    kind: advice\n"
        "    summary: Demo summary.\n"
        "    doc: docs/patterns/demo.md\n",
        encoding="utf-8",
    )

    with pytest.raises(PatternCatalogError, match="invalid pattern kind: advice"):
        load_pattern_catalog(tmp_path)


def test_load_pattern_detail_reads_markdown_document() -> None:
    catalog = load_pattern_catalog(Path("."))
    detail = load_pattern_detail(Path("."), catalog.patterns[0])

    assert detail.entry.id == "bounded-workflow-evidence"
    assert "# Bounded workflow evidence" in detail.markdown
    assert "must not automatically approve" in detail.markdown


def test_patterns_list_cli_lists_catalog_entries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["patterns", "list"])

    assert result.exit_code == 0, result.output
    assert "bounded-workflow-evidence" in result.output
    assert "Bounded workflow evidence" in result.output
    assert "hidden-autopilot" in result.output
    assert "anti-pattern" in result.output


def test_patterns_show_cli_prints_markdown_detail() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["patterns", "show", "bounded-workflow-evidence"])

    assert result.exit_code == 0, result.output
    assert "# Bounded workflow evidence" in result.output
    assert "must not automatically approve" in result.output


def test_patterns_show_cli_rejects_unknown_id() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["patterns", "show", "does-not-exist"])

    assert result.exit_code != 0
    assert "unknown pattern id: does-not-exist" in result.output
