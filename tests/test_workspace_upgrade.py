from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workspace import load_workspace
import agentic_project_kit.workspace_upgrade as workspace_upgrade


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


def _fake_v0_to_v1(manifest: dict[str, object]) -> dict[str, object]:
    migrated = dict(manifest)
    migrated["kit_schema_version"] = 1
    migrated.setdefault("project", {"name": "legacy", "type": "generic"})
    migrated.setdefault("profile", "generic")
    migrated.setdefault("modules", {})
    migrated.setdefault("transfer", {"visibility": "repo"})
    migrated.setdefault("paths", {"docs_root": "docs"})
    migrated.setdefault("gates", {"extra": [], "skip": []})
    return migrated


def test_upgrade_no_manifest_message(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "no workspace manifest; run workspace init" in result.output


def test_upgrade_at_latest_is_noop_exit_zero(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
project: {name: current, type: generic}
profile: generic
""",
    )
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "already at latest schema (v1); nothing to upgrade" in result.output
    assert "WRITTEN=false" in result.output


def test_upgrade_newer_schema_names_kit_upgrade(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "kit_schema_version: 2\n")

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "manifest schema v2 is newer than this kit; upgrade the kit" in result.output


def test_upgrade_stepwise_with_backup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(workspace_upgrade, "WORKSPACE_UPGRADE_STEPS", {0: _fake_v0_to_v1})
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 0
project: {name: legacy, type: generic}
""",
    )

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--execute"],
    )

    assert result.exit_code == 0, result.output
    assert "v0 -> v1" in result.output
    assert "WRITTEN=true" in result.output
    backup = tmp_path / ".agentic" / "config.yaml.bak.v0"
    assert backup.exists()
    assert "kit_schema_version: 0" in backup.read_text(encoding="utf-8")
    manifest_text = (tmp_path / ".agentic" / "config.yaml").read_text(encoding="utf-8")
    assert "kit_schema_version: 1" in manifest_text
    assert load_workspace(tmp_path).profile == "generic"


def test_upgrade_dry_run_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(workspace_upgrade, "WORKSPACE_UPGRADE_STEPS", {0: _fake_v0_to_v1})
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 0
project: {name: dry-run, type: generic}
""",
    )
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "upgrade", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "Manifest diff for v0 -> v1" in result.output
    assert "--- .agentic/config.yaml@v0" in result.output
    assert "+++ .agentic/config.yaml@v1" in result.output
    assert "-kit_schema_version: 0" in result.output
    assert "+kit_schema_version: 1" in result.output


def test_upgrade_json_shape(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "kit_schema_version: 1\nprofile: generic\n")

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "workspace_upgrade_plan"
    assert payload["mode"] == "dry-run"
    assert payload["written"] is False
    assert payload["message"] == "already at latest schema (v1); nothing to upgrade"
