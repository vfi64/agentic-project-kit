from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workspace import load_workspace


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


def _write_manifest(root: Path, text: str) -> None:
    _write(root / ".agentic" / "config.yaml", text)


def test_upgrade_no_manifest_message(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "no workspace manifest; run workspace init" in result.output


def test_upgrade_at_latest_is_noop_exit_zero(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 2
project: {name: current, type: generic}
profile: generic
hygiene:
  doc_lifecycle: warn
  review_budgets:
    governance: 180
    reference: 365
    workflow: 270
""",
    )
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "already at latest schema (v2); nothing to upgrade" in result.output
    assert "WRITTEN=false" in result.output


def test_upgrade_newer_schema_names_kit_upgrade(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "kit_schema_version: 3\n")

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "manifest schema v3 is newer than this kit; upgrade the kit" in result.output


def test_upgrade_stepwise_with_backup(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
project: {name: legacy, type: generic}
profile: generic
""",
    )

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--execute"],
    )

    assert result.exit_code == 0, result.output
    assert "v1 -> v2" in result.output
    assert "WRITTEN=true" in result.output
    backup = tmp_path / ".agentic" / "config.yaml.bak.v1"
    assert backup.exists()
    assert "kit_schema_version: 1" in backup.read_text(encoding="utf-8")
    manifest_text = (tmp_path / ".agentic" / "config.yaml").read_text(encoding="utf-8")
    assert "kit_schema_version: 2" in manifest_text
    assert "hygiene:" in manifest_text
    assert "doc_lifecycle: warn" in manifest_text
    assert load_workspace(tmp_path).profile == "generic"
    assert load_workspace(tmp_path).manifest_schema_version == 2


def test_upgrade_dry_run_writes_nothing(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
project: {name: dry-run, type: generic}
profile: generic
""",
    )
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "Manifest diff for v1 -> v2" in result.output
    assert "--- .agentic/config.yaml@v1" in result.output
    assert "+++ .agentic/config.yaml@v2" in result.output
    assert "-kit_schema_version: 1" in result.output
    assert "+kit_schema_version: 2" in result.output
    assert "+hygiene:" in result.output


def test_upgrade_v1_to_v2_preserves_explicit_hygiene_values(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
project: {name: strict-docs, type: generic}
profile: generic
hygiene:
  doc_lifecycle: strict
""",
    )

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--execute"],
    )

    assert result.exit_code == 0, result.output
    workspace = load_workspace(tmp_path)
    assert workspace.manifest_schema_version == 2
    assert workspace.hygiene_doc_lifecycle == "strict"
    assert dict(workspace.hygiene_review_budgets) == {
        "governance": 180,
        "reference": 365,
        "workflow": 270,
    }


def test_upgrade_json_shape(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 2
profile: generic
hygiene:
  doc_lifecycle: warn
  review_budgets:
    governance: 180
    reference: 365
    workflow: 270
""",
    )

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "workspace_upgrade_plan"
    assert payload["mode"] == "dry-run"
    assert payload["written"] is False
    assert payload["message"] == "already at latest schema (v2); nothing to upgrade"
