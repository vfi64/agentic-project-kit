from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_adopt import (
    PRIVATE_PUBLIC_BOUNDARY,
    analyze_workspace_adoption,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    dirs = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    return dirs, files


def test_adopt_detects_python_node_generic(tmp_path: Path) -> None:
    python_repo = tmp_path / "python-repo"
    node_repo = tmp_path / "node-repo"
    generic_repo = tmp_path / "generic-repo"
    _write(python_repo / "pyproject.toml", "[project]\nname = 'demo-python'\n")
    _write(node_repo / "package.json", '{"name": "demo-node"}\n')
    generic_repo.mkdir()

    python_report = analyze_workspace_adoption(python_repo)
    node_report = analyze_workspace_adoption(node_repo)
    generic_report = analyze_workspace_adoption(generic_repo)

    assert python_report.project.name == "demo-python"
    assert python_report.project.type == "python"
    assert python_report.project.profile == "python-default"
    assert node_report.project.name == "demo-node"
    assert node_report.project.type == "node"
    assert node_report.project.profile == "generic"
    assert generic_report.project.name == "generic-repo"
    assert generic_report.project.type == "generic"
    assert generic_report.project.profile == "generic"


def test_adopt_proposed_manifest_passes_p2_validation(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", "[project]\nname = 'valid-manifest'\n")
    report = analyze_workspace_adoption(tmp_path)
    _write(tmp_path / ".agentic" / "config.yaml", report.manifest_yaml)

    workspace = load_workspace(tmp_path)

    assert workspace.project_name == "valid-manifest"
    assert workspace.project_type == "python"
    assert workspace.profile == "python-default"


def test_adopt_reports_foreign_agentic_dir(tmp_path: Path) -> None:
    _write(tmp_path / ".agentic" / "other-tool.txt", "foreign\n")

    report = analyze_workspace_adoption(tmp_path)

    assert report.agentic.status == "foreign_agentic_directory"
    assert "FOREIGN" in report.agentic.message


def test_adopt_reports_already_initialized(tmp_path: Path) -> None:
    _write(
        tmp_path / ".agentic" / "config.yaml",
        """
kit_schema_version: 1
project: {name: initialized, type: generic}
profile: generic
""",
    )

    report = analyze_workspace_adoption(tmp_path)

    assert report.agentic.status == "already_initialized"
    assert report.agentic.manifest_version == 1


def test_adopt_makes_no_writes(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "README.md", "# Docs\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: ci\n")
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "adopt", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before


def test_adopt_prints_privacy_boundary(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "adopt", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert PRIVATE_PUBLIC_BOUNDARY in result.output
    assert "no secrets, credentials, private chat fragments" in result.output


def test_adopt_json_shape(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "guide.md", "# Guide\n")
    _write(tmp_path / "docs" / "ops" / "runbook.md", "# Runbook\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: ci\n")

    result = CliRunner().invoke(
        app,
        ["workspace", "adopt", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "workspace_adopt_report"
    assert payload["result_status"] == "PASS"
    assert payload["agentic"]["status"] == "ready_for_workspace_init"
    assert payload["project"]["type"] == "generic"
    assert payload["ci_workflows"] == [".github/workflows/ci.yml"]
    assert payload["init_tree"][0] == ".agentic/"
    docs_counts = {
        row["docs_path"]: row["registration_candidates"]
        for row in payload["docs_preview"]
    }
    assert docs_counts == {"docs/": 1, "docs/ops/": 1}
    assert payload["privacy_boundary"] == PRIVATE_PUBLIC_BOUNDARY
