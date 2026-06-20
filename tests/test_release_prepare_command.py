from __future__ import annotations

from collections.abc import Sequence
from datetime import date as Date
from pathlib import Path
import shutil

from agentic_project_kit.release import CommandResult, build_release_state_report
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit import release_metadata_prep


ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "0.4.11"
PREVIOUS_VERSION = "0.4.10"
TARGET_DATE = "2026-06-18"
SUMMARY_LINES = [
    "Release metadata prepared through the explicit summary-line release-prep contract.",
    "Publish, DOI verification, and closeout remain separate guarded steps.",
]


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
        "README.md": (f"Current version: {TARGET_VERSION}", f"Current version: {PREVIOUS_VERSION}"),
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

    result = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE, summary_lines=SUMMARY_LINES)

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
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert readme.count("Current version:") == 1
    assert f"Current version: {TARGET_VERSION}" in readme
    citation = (project / "CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {TARGET_VERSION}" in citation
    assert f'date-released: "{TARGET_DATE}"' in citation
    assert f"Current version: {TARGET_VERSION}" in (project / "docs" / "STATUS.md").read_text(
        encoding="utf-8"
    )
    assert f"Current version: {TARGET_VERSION}" in (
        project / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    ).read_text(encoding="utf-8")
    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## v{TARGET_VERSION} - {TARGET_DATE}" in changelog
    assert SUMMARY_LINES[0] in changelog
    assert SUMMARY_LINES[1] in changelog
    assert "./ns release-prep" not in changelog.split(f"## v{TARGET_VERSION}", 1)[1].split("\n## v", 1)[0]


def test_prepare_release_state_is_idempotent(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    first = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE, summary_lines=SUMMARY_LINES)
    second = prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE, summary_lines=SUMMARY_LINES)

    assert first.changed_paths
    assert second.changed_paths == []


def test_prepare_release_state_dry_run_does_not_write(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)
    before = (project / "pyproject.toml").read_text(encoding="utf-8")

    result = prepare_release_state(
        project,
        version=TARGET_VERSION,
        date=TARGET_DATE,
        summary_lines=SUMMARY_LINES,
        dry_run=True,
    )

    assert result.changed_paths
    assert (project / "pyproject.toml").read_text(encoding="utf-8") == before


def test_ns_release_metadata_prep_updates_temp_project_and_release_check_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = _copy_release_state_files(tmp_path)
    monkeypatch.chdir(project)

    class FrozenDate:
        @classmethod
        def today(cls) -> Date:
            return Date(2026, 6, 17)

    monkeypatch.setattr(release_metadata_prep, "date", FrozenDate)

    assert release_metadata_prep.main([TARGET_VERSION]) == 0
    report = build_release_state_report(project, version=TARGET_VERSION, command_runner=_runner())
    assert report.ok
    assert f"## v{TARGET_VERSION} - 2026-06-17" in (project / "CHANGELOG.md").read_text(encoding="utf-8")


def test_prepare_release_state_requires_explicit_changelog_summary_lines(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    try:
        prepare_release_state(project, version=TARGET_VERSION, date=TARGET_DATE, summary_lines=[])
    except ValueError as exc:
        assert "summary_lines are required" in str(exc)
    else:
        raise AssertionError("prepare_release_state accepted missing summary_lines")


def test_release_prep_generated_changelog_rejects_removed_ns_route_references(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)

    try:
        prepare_release_state(
            project,
            version=TARGET_VERSION,
            date=TARGET_DATE,
            summary_lines=["Recorded deterministic release prep through ./ns release-prep."],
        )
    except ValueError as exc:
        assert "removed ./ns release routes" in str(exc)
    else:
        raise AssertionError("prepare_release_state accepted removed ./ns release route reference")


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
