from __future__ import annotations

from collections.abc import Sequence
from datetime import date as Date
import importlib.util
from pathlib import Path
import shutil
import sys

from agentic_project_kit.release import CommandResult, build_release_state_report
from agentic_project_kit.release_prepare import prepare_release_state


ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "0.4.9"
PREVIOUS_VERSION = "0.4.8"
TARGET_DATE = "2026-06-18"


def _copy_release_state_files(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for relative in [
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "src/agentic_project_kit/__init__.py",
    ]:
        source = ROOT / relative
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    # Keep this fixture stable after the repository itself has been bumped to
    # TARGET_VERSION: release preparation must still be tested from a previous
    # release state, not from the already-updated working tree.
    replacements = {
        "pyproject.toml": (f'version = "{TARGET_VERSION}"', f'version = "{PREVIOUS_VERSION}"'),
        "src/agentic_project_kit/__init__.py": (
            f'__version__ = "{TARGET_VERSION}"',
            f'__version__ = "{PREVIOUS_VERSION}"',
        ),
        "README.md": (f"Version `{TARGET_VERSION}`", f"Version `{PREVIOUS_VERSION}`"),
        "CITATION.cff": (f"version: {TARGET_VERSION}", f"version: {PREVIOUS_VERSION}"),
        "docs/STATUS.md": (
            f"Current version: {TARGET_VERSION}",
            f"Current version: {PREVIOUS_VERSION}",
        ),
        "docs/handoff/CURRENT_HANDOFF.md": (
            f"Current version: {TARGET_VERSION}",
            f"Current version: {PREVIOUS_VERSION}",
        ),
    }
    for relative, (needle, replacement) in replacements.items():
        target = project / relative
        target.write_text(target.read_text(encoding="utf-8").replace(needle, replacement), encoding="utf-8")

    changelog = project / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8")
    marker = f"## v{TARGET_VERSION} - "
    previous_marker = f"## v{PREVIOUS_VERSION} - "
    if changelog_text.startswith(marker) and previous_marker in changelog_text:
        changelog_text = previous_marker + changelog_text.split(previous_marker, 1)[1]
        changelog.write_text(changelog_text, encoding="utf-8")

    return project


def test_prepare_release_state_updates_expected_files(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    result = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE)

    assert result.ok
    assert result.version == TARGET_VERSION
    assert result.date == TARGET_DATE
    assert result.changed_paths == [
        "CHANGELOG.md",
        "CITATION.cff",
        "README.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "pyproject.toml",
        "src/agentic_project_kit/__init__.py",
    ]

    assert f'version = "{TARGET_VERSION}"' in (project / "pyproject.toml").read_text(encoding="utf-8")
    assert f'__version__ = "{TARGET_VERSION}"' in (
        project / "src" / "agentic_project_kit" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert f"Version `{TARGET_VERSION}` is the current release line prepared" in (
        project / "README.md"
    ).read_text(encoding="utf-8")
    assert f"version: {TARGET_VERSION}" in (project / "CITATION.cff").read_text(encoding="utf-8")
    assert f"Current version: {TARGET_VERSION}" in (project / "docs" / "STATUS.md").read_text(
        encoding="utf-8"
    )
    assert f"Current version: {TARGET_VERSION}" in (
        project / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    ).read_text(encoding="utf-8")
    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## v{TARGET_VERSION} - {TARGET_DATE}" in changelog
    assert "Zenodo DOI verification pending" in changelog
    assert "unfinished grouped `agentic-kit release prepare/check` route" in changelog
    assert "no tag or publication side effects" in changelog


def test_prepare_release_state_is_idempotent(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    first = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE)
    second = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE)

    assert first.changed_paths
    assert second.changed_paths == []


def test_prepare_release_state_dry_run_does_not_write(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)
    before = (project / "pyproject.toml").read_text(encoding="utf-8")

    result = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE, dry_run=True)

    assert result.changed_paths
    assert (project / "pyproject.toml").read_text(encoding="utf-8") == before


def test_ns_release_metadata_prep_updates_temp_project_and_release_check_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = _copy_release_state_files(tmp_path)
    monkeypatch.chdir(project)
    module = _load_metadata_prep_script()

    class FrozenDate:
        @classmethod
        def today(cls) -> Date:
            return Date(2026, 6, 17)

    monkeypatch.setattr(module, "date", FrozenDate)

    assert module.main([TARGET_VERSION]) == 0
    report = build_release_state_report(project, version=TARGET_VERSION, command_runner=_runner())
    assert report.ok
    assert f"## v{TARGET_VERSION} - 2026-06-17" in (project / "CHANGELOG.md").read_text(encoding="utf-8")


def _load_metadata_prep_script():
    path = ROOT / "tools" / "ns_release_metadata_prep.py"
    spec = importlib.util.spec_from_file_location("ns_release_metadata_prep_for_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runner():
    def run(_project_root: Path, command: Sequence[str]) -> CommandResult:
        if command[:3] == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        if command[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return CommandResult(0, "", "")
        if command[:3] == ["gh", "release", "view"]:
            return CommandResult(1, "", "release not found")
        raise AssertionError(f"unexpected command: {command}")

    return run
