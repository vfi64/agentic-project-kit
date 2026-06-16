from __future__ import annotations

from pathlib import Path
import shutil

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit.release_state import check_release_state


ROOT = Path(__file__).resolve().parents[1]


def _copy_release_state_files(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for relative in [
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "src/agentic_project_kit/__init__.py",
    ]:
        source = ROOT / relative
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return project


def test_prepare_release_state_updates_expected_files(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    result = prepare_release_state(project, version="0.4.8", date="2026-06-16")

    assert result.ok
    assert result.version == "0.4.8"
    assert result.date == "2026-06-16"
    assert result.changed_paths == [
        "CHANGELOG.md",
        "README.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "pyproject.toml",
        "src/agentic_project_kit/__init__.py",
    ]

    assert 'version = "0.4.8"' in (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "0.4.8"' in (
        project / "src" / "agentic_project_kit" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "Version `0.4.8` is the current release line prepared" in (
        project / "README.md"
    ).read_text(encoding="utf-8")
    assert "Current version: 0.4.8" in (project / "docs" / "STATUS.md").read_text(
        encoding="utf-8"
    )
    assert "Current version: 0.4.8" in (
        project / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    ).read_text(encoding="utf-8")
    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## v0.4.8 - 2026-06-16" in changelog
    assert "Zenodo DOI verification pending" in changelog
    assert "no tag or publication side effects" in changelog


def test_prepare_release_state_is_idempotent(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    first = prepare_release_state(project, version="0.4.8", date="2026-06-16")
    second = prepare_release_state(project, version="0.4.8", date="2026-06-16")

    assert first.changed_paths
    assert second.changed_paths == []


def test_prepare_release_state_dry_run_does_not_write(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)
    before = (project / "pyproject.toml").read_text(encoding="utf-8")

    result = prepare_release_state(project, version="0.4.8", date="2026-06-16", dry_run=True)

    assert result.changed_paths
    assert (project / "pyproject.toml").read_text(encoding="utf-8") == before


def test_release_prepare_cli_updates_temp_project_and_check_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = _copy_release_state_files(tmp_path)
    monkeypatch.chdir(project)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "release",
            "prepare",
            "--version",
            "0.4.8",
            "--date",
            "2026-06-16",
        ],
        catch_exceptions=False,
        prog_name="agentic-kit",
    )

    assert result.exit_code == 0
    check = check_release_state(project, expected_version="0.4.8")
    assert check.ok, check.errors


def test_release_prepare_cli_json_dry_run_on_current_repo() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["release", "prepare", "--version", "0.4.8", "--date", "2026-06-16", "--dry-run", "--json"],
    )

    assert result.exit_code == 0
    assert '"dry_run": true' in result.output
    assert '"version": "0.4.8"' in result.output
