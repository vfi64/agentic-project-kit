"""KIT-GF-032 slice A: release version anchors of an external workspace.

Regression from the agp-Cockpit retest (Kit 1.0.14, GF-E038): with
``publication: none`` release-check failed on the Kit's own files
(``src/agentic_project_kit/__init__.py``, CITATION.cff, docs/STATUS.md,
docs/handoff/CURRENT_HANDOFF.md) and the README version marker.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from agentic_project_kit.release import (
    CommandResult,
    ReleaseCheckStatus,
    build_release_plan,
    build_release_state_report,
)
from agentic_project_kit.release_publish_orchestration import _release_commit_integrity_check
from agentic_project_kit.release_version_sources import (
    is_kit_self_hosting,
    package_version_file,
    release_version_anchors,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(root: Path, publication: str = "none") -> None:
    _write(
        root / ".agentic/config.yaml",
        "kit_schema_version: 2\nprofile: generic\n"
        f"publication: {publication}\n"
        "hygiene:\n  doc_lifecycle: warn\n  review_budgets:\n"
        "    governance: 180\n    reference: 365\n    workflow: 270\n",
    )


def _cockpit_like(root: Path, version: str = "0.1.1", publication: str = "none") -> None:
    """Shape of agp-Cockpit: indirect __version__, own CHANGELOG, no CITATION."""
    _manifest(root, publication)
    _write(root / "pyproject.toml", f'[project]\nname = "agp-cockpit"\nversion = "{version}"\n')
    _write(root / "src/agp_cockpit/__init__.py",
           'from agp_cockpit.version import APP_VERSION\n\n__version__ = APP_VERSION\n')
    _write(root / "src/agp_cockpit/version.py", f'APP_VERSION = "{version}"\n')
    _write(root / "CHANGELOG.md", f"# Changelog\n\n## v{version} - 2026-10-03\n\n- change\n")
    _write(root / "docs/STATUS.md", "# Status\n\nNo version line here.\n")


def _tag_runner(seen: list[tuple[str, ...]]):
    def runner(_root: Path, command: Sequence[str]) -> CommandResult:
        seen.append(tuple(command))
        if list(command[:3]) == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        raise AssertionError(f"unexpected command: {command}")
    return runner


def _names(report) -> list[str]:
    return [check.name for check in report.checks]


def _cockpit_extra_version_manifest(root: Path) -> None:
    manifest = root / ".agentic/config.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + "release:\n"
        + "  version_anchors:\n"
        + "    - kind: source_constant\n"
        + "      path: src/agp_cockpit/version.py\n"
        + "      name: APP_VERSION\n"
        + "      label: APP_VERSION\n"
        + "    - kind: json_table\n"
        + "      path: docs/releases/versions.json\n"
        + "      label: AGP_VERSION_MAP_V1 app version\n"
        + "      list: releases\n"
        + "      version_field: app\n"
        + "      row:\n"
        + "        app: '{version}'\n",
        encoding="utf-8",
    )
    _write(root / "src/agp_cockpit/version.py", 'APP_VERSION = "0.1.0"\n')
    _write(
        root / "docs/releases/versions.json",
        '{\n  "marker": "AGP_VERSION_MAP_V1",\n  "releases": [{"app": "0.1.0"}]\n}\n',
    )


def test_layout_detection(tmp_path: Path):
    assert is_kit_self_hosting(tmp_path)                       # legacy root, no manifest
    _manifest(tmp_path)
    assert not is_kit_self_hosting(tmp_path)                   # external workspace
    _write(tmp_path / "src/agentic_project_kit/__init__.py", '__version__ = "1.0.0"\n')
    assert is_kit_self_hosting(tmp_path)                       # the Kit itself


def test_external_workspace_release_check_passes_without_kit_files(tmp_path: Path):
    _cockpit_like(tmp_path)
    seen: list[tuple[str, ...]] = []
    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner(seen))
    assert report.ok, [(c.name, c.status, c.detail) for c in report.checks]
    names = _names(report)
    assert "pyproject version" in names and "CHANGELOG version" in names
    for kit_only in ("package __version__", "README version", "CITATION version", "STATUS version",
                     "CURRENT_HANDOFF version"):
        assert kit_only not in names
    assert not any("agentic_project_kit" in check.detail for check in report.checks)


def test_external_workspace_still_fails_on_its_own_stale_files(tmp_path: Path):
    _cockpit_like(tmp_path, version="0.1.0")
    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner([]))
    failed = {c.name for c in report.checks if c.status == ReleaseCheckStatus.FAIL}
    assert failed == {"pyproject version", "CHANGELOG version"}


def test_literal_package_version_is_an_anchor(tmp_path: Path):
    _cockpit_like(tmp_path)
    _write(tmp_path / "src/agp_cockpit/_version.py", '__version__ = "0.1.0"\n')
    assert package_version_file(tmp_path) == "src/agp_cockpit/_version.py"
    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner([]))
    check = next(c for c in report.checks if c.name == "package __version__")
    assert check.status == ReleaseCheckStatus.FAIL


def test_keep_a_changelog_heading_and_no_prefix_false_positive(tmp_path: Path):
    _cockpit_like(tmp_path)
    _write(tmp_path / "CHANGELOG.md", "## [10.1.1] - 2026-01-01\n")
    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner([]))
    assert next(c for c in report.checks if c.name == "CHANGELOG version").status == ReleaseCheckStatus.FAIL
    _write(tmp_path / "CHANGELOG.md", "## [0.1.1] - 2026-10-03\n")
    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner([]))
    assert next(c for c in report.checks if c.name == "CHANGELOG version").status == ReleaseCheckStatus.PASS


def test_status_files_count_only_with_a_version_line(tmp_path: Path):
    _cockpit_like(tmp_path)
    _write(tmp_path / "docs/STATUS.md", "Current version: 0.1.0\n")
    paths = [a.path for a in release_version_anchors(tmp_path, "0.1.1")]
    assert "docs/STATUS.md" in paths and "docs/handoff/CURRENT_HANDOFF.md" not in paths


def test_zenodo_policy_requires_citation(tmp_path: Path):
    _cockpit_like(tmp_path, publication="github+pypi+zenodo")
    paths = [a.path for a in release_version_anchors(tmp_path, "0.1.1")]
    assert "CITATION.cff" in paths
    _cockpit_like(tmp_path, publication="github")
    assert "CITATION.cff" not in [a.path for a in release_version_anchors(tmp_path, "0.1.1")]


def test_release_plan_lists_only_the_workspace_files(tmp_path: Path):
    _cockpit_like(tmp_path)
    step = next(s for s in build_release_plan(tmp_path, "0.1.1").steps
                if s.name == "Check release notes and state files")
    text = " ".join(step.commands) + step.evidence
    assert "pyproject.toml" in text and "CHANGELOG.md" in text
    for kit_only in ("CITATION.cff", "README.md", "docs/STATUS.md", "CURRENT_HANDOFF"):
        assert kit_only not in text


def test_release_commit_integrity_uses_the_workspace_anchors(tmp_path: Path):
    _cockpit_like(tmp_path)

    def runner(command: Sequence[str], _root: Path):
        if tuple(command) == ("git", "status", "--porcelain"):
            return 0, ""
        if tuple(command) == ("git", "rev-parse", "HEAD"):
            return 0, "abc\n"
        return 1, "no such tag"

    check = _release_commit_integrity_check(version="0.1.1", tag="v0.1.1", root=tmp_path, runner=runner)
    assert check.status == "PASS", check.detail
    _write(tmp_path / "CHANGELOG.md", "## v0.1.0 - 2026-10-02\n")
    check = _release_commit_integrity_check(version="0.1.1", tag="v0.1.1", root=tmp_path, runner=runner)
    assert check.status == "FAIL" and "CHANGELOG.md" in check.detail and "CITATION" not in check.detail


def test_manifest_declared_version_anchors_join_release_check_and_integrity(tmp_path: Path):
    _cockpit_like(tmp_path, version="0.1.1")
    _cockpit_extra_version_manifest(tmp_path)

    report = build_release_state_report(tmp_path, "0.1.1", command_runner=_tag_runner([]))

    failed = {c.name for c in report.checks if c.status == ReleaseCheckStatus.FAIL}
    assert failed == {"APP_VERSION", "AGP_VERSION_MAP_V1 app version"}
    paths = [a.path for a in release_version_anchors(tmp_path, "0.1.1")]
    assert "src/agp_cockpit/version.py" in paths
    assert "docs/releases/versions.json" in paths

    def runner(command: Sequence[str], _root: Path):
        if tuple(command) == ("git", "status", "--porcelain"):
            return 0, ""
        if tuple(command) == ("git", "rev-parse", "HEAD"):
            return 0, "abc\n"
        return 1, "no such tag"

    check = _release_commit_integrity_check(version="0.1.1", tag="v0.1.1", root=tmp_path, runner=runner)
    assert check.status == "FAIL"
    assert "src/agp_cockpit/version.py" in check.detail
    assert "docs/releases/versions.json" in check.detail
