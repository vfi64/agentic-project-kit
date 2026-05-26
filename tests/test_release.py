from pathlib import Path
from collections.abc import Sequence

import yaml

from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REGISTRY_PATH, REQUIRED_CLASS_RULE_FIELDS
from agentic_project_kit.release import (
    ReleaseCheckResult,
    ReleaseStateReport,
    CommandResult,
    ReleaseCheckStatus,
    build_release_plan,
    build_release_preflight_report,
    build_release_state_report,
    render_release_plan,
    render_release_preflight_report,
    render_release_state_report,
    validate_version,
)


def test_build_release_plan_reads_pyproject_version(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    plan = build_release_plan(tmp_path)

    assert plan.version == "1.2.3"
    assert [step.name for step in plan.steps] == [
        "Confirm clean repository state",
        "Run local quality gates",
        "Validate package artifacts",
        "Check release notes and state files",
        "Verify target tag and release are unused",
        "Create and verify tag",
    ]


def test_build_release_plan_accepts_explicit_version(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    plan = build_release_plan(tmp_path, version="2.0.0")

    assert plan.version == "2.0.0"
    assert "git tag -l v2.0.0" in plan.steps[-2].commands
    assert "git ls-remote --tags origin v2.0.0" in plan.steps[-2].commands
    assert "gh release view v2.0.0" in plan.steps[-2].commands
    assert "git tag v2.0.0" in plan.steps[-1].commands


def test_render_release_plan_contains_commands_and_evidence(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    rendered = render_release_plan(build_release_plan(tmp_path))

    assert "# Release preparation plan for target v1.2.3" in rendered
    assert "python -m pytest -q" in rendered
    assert "ruff check ." in rendered
    assert "agentic-kit check-docs" in rendered
    assert "twine check dist/*" in rendered
    assert "grep -n 'version = \"1.2.3\"' pyproject.toml" in rendered
    assert "grep -n 'Version `1.2.3`' README.md" in rendered
    assert "grep -n 'version: 1.2.3' CITATION.cff" in rendered
    assert "git tag -l v1.2.3" in rendered
    assert "git ls-remote --tags origin v1.2.3" in rendered
    assert "gh release view v1.2.3" in rendered
    assert "Evidence:" in rendered


def test_validate_version_warns_for_non_semantic_version():
    assert validate_version("1.2") == ["Version '1.2' is not a simple semantic version like 1.2.3."]


def test_build_release_state_report_passes_for_unused_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path, command_runner=_runner())

    assert report.ok
    assert [check.status for check in report.checks] == [ReleaseCheckStatus.PASS] * 12
    assert report.registry_summary is None


def test_build_release_state_report_includes_registry_summary_when_available(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    _write_minimal_registry(tmp_path)

    report = build_release_state_report(tmp_path, command_runner=_runner())
    rendered = render_release_state_report(report)

    assert report.ok
    assert report.registry_summary is not None
    assert report.registry_summary["document_count"] == 2
    assert "Documentation registry:" in rendered
    assert "- registry: docs/DOCUMENTATION_REGISTRY.yaml" in rendered
    assert "- documents: 2" in rendered
    assert "- broad_migration_allowed: False" in rendered
    assert "- class:release: 1" in rendered
    assert "Overall: PASS" in rendered


def test_build_release_state_report_allows_local_tag_warning_without_remote_warnings(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(local_tag=CommandResult(2, "", "fatal: not a git repository")),
    )

    assert report.ok
    check = _check_by_name(report, "local tag unused")
    assert check.status == ReleaseCheckStatus.WARN
    assert check.detail == "fatal: not a git repository"
    assert _check_by_name(report, "release publish readiness").status == ReleaseCheckStatus.PASS


def test_build_release_state_report_warns_when_remote_tag_check_is_unavailable(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(remote_tag=CommandResult(2, "", "fatal: 'origin' does not appear to be a git repository")),
    )

    assert not report.ok
    assert report.outcome == ReleaseCheckStatus.BLOCK
    assert _check_by_name(report, "remote tag unused").status == ReleaseCheckStatus.WARN
    readiness = _check_by_name(report, "release publish readiness")
    assert readiness.status == ReleaseCheckStatus.BLOCK
    assert "do not tag or publish" in readiness.detail


def test_build_release_state_report_warns_when_github_release_check_is_unavailable(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(127, "", "could not run gh: not found")),
    )

    assert not report.ok
    assert report.outcome == ReleaseCheckStatus.BLOCK
    assert _check_by_name(report, "GitHub release unused").status == ReleaseCheckStatus.WARN
    readiness = _check_by_name(report, "release publish readiness")
    assert readiness.status == ReleaseCheckStatus.BLOCK
    assert "do not tag or publish" in readiness.detail


def test_build_release_state_report_fails_for_missing_changelog_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    report = build_release_state_report(tmp_path, command_runner=_runner())

    assert not report.ok
    check = _check_by_name(report, "CHANGELOG version")
    assert check.status == ReleaseCheckStatus.FAIL
    assert "missing text: v1.2.3" in check.detail


def test_build_release_state_report_fails_for_missing_readme_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")

    report = build_release_state_report(tmp_path, command_runner=_runner())

    assert not report.ok
    check = _check_by_name(report, "README version")
    assert check.status == ReleaseCheckStatus.FAIL
    assert "missing text: Version `1.2.3`" in check.detail


def test_build_release_state_report_fails_for_missing_citation_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    (tmp_path / "CITATION.cff").write_text("cff-version: 1.2.0\n", encoding="utf-8")

    report = build_release_state_report(tmp_path, command_runner=_runner())

    assert not report.ok
    check = _check_by_name(report, "CITATION version")
    assert check.status == ReleaseCheckStatus.FAIL
    assert "missing text: version: 1.2.3" in check.detail


def test_build_release_state_report_fails_for_missing_pyproject_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    (tmp_path / "pyproject.toml").write_text('version = "1.2.2"\n', encoding="utf-8")

    report = build_release_state_report(tmp_path, version="1.2.3", command_runner=_runner())

    assert not report.ok
    assert report.checks[1].status == ReleaseCheckStatus.FAIL
    assert 'missing text: version = "1.2.3"' in report.checks[1].detail


def test_build_release_state_report_fails_for_existing_local_tag(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path, command_runner=_runner(local_tag=CommandResult(0, "v1.2.3\n", "")))

    assert not report.ok
    check = _check_by_name(report, "local tag unused")
    assert check.status == ReleaseCheckStatus.FAIL
    assert check.detail == "tag already exists: v1.2.3"


def test_build_release_state_report_fails_for_existing_remote_tag(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(remote_tag=CommandResult(0, "abc123\trefs/tags/v1.2.3\n", "")),
    )

    assert not report.ok
    check = _check_by_name(report, "remote tag unused")
    assert check.status == ReleaseCheckStatus.FAIL
    assert check.detail == "remote tag already exists: v1.2.3"
    assert _check_by_name(report, "release publish readiness").status == ReleaseCheckStatus.FAIL


def test_build_release_state_report_fails_for_existing_github_release(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path, command_runner=_runner(github_release=CommandResult(0, "title: v1.2.3\n", "")))

    assert not report.ok
    check = _check_by_name(report, "GitHub release unused")
    assert check.status == ReleaseCheckStatus.FAIL
    assert check.detail == "GitHub release already exists: v1.2.3"
    assert _check_by_name(report, "release publish readiness").status == ReleaseCheckStatus.FAIL


def test_render_release_state_report_shows_overall_status(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    rendered = render_release_state_report(build_release_state_report(tmp_path, command_runner=_runner()))

    assert "Release state check for target v1.2.3" in rendered
    assert "[PASS] semantic version" in rendered
    assert "[PASS] pyproject version" in rendered
    assert "[PASS] README version" in rendered
    assert "[PASS] CITATION version" in rendered
    assert "[PASS] remote tag unused" in rendered
    assert "[PASS] GitHub release unused" in rendered
    assert "[PASS] release publish readiness" in rendered
    assert "Overall: PASS" in rendered


def test_render_release_state_report_blocks_when_remote_check_warns(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(remote_tag=CommandResult(2, "", "network unavailable")),
    )
    rendered = render_release_state_report(report)

    assert "[WARN] remote tag unused: network unavailable" in rendered
    assert "[BLOCK] release publish readiness" in rendered
    assert "Overall: BLOCK" in rendered


def test_build_release_preflight_report_blocks_on_remote_warnings(tmp_path: Path):
    report = build_release_preflight_report(
        tmp_path,
        "1.2.3",
        command_runner=_runner(github_release=CommandResult(127, "", "could not run gh: not found")),
    )
    rendered = render_release_preflight_report(report)

    assert not report.ok
    assert report.outcome == ReleaseCheckStatus.BLOCK
    assert "[WARN] GitHub release unused" in rendered
    assert "[BLOCK] release publish readiness" in rendered
    assert "Overall: BLOCK" in rendered


def _write_release_files(project_root: Path, version: str) -> None:
    (project_root / "docs/handoff").mkdir(parents=True)
    (project_root / "pyproject.toml").write_text(f'version = "{version}"\n', encoding="utf-8")
    (project_root / "CHANGELOG.md").write_text(f"# Changelog\n\n## v{version}\n", encoding="utf-8")
    (project_root / "README.md").write_text(f"## Current status\n\nVersion `{version}`\n", encoding="utf-8")
    (project_root / "CITATION.cff").write_text(f"cff-version: 1.2.0\nversion: {version}\n", encoding="utf-8")
    (project_root / "docs/STATUS.md").write_text(f"Current version: {version}\n", encoding="utf-8")
    (project_root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        f"Current version: {version}\n", encoding="utf-8"
    )

    package_dir = project_root / "src/agentic_project_kit"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "__init__.py").write_text(f'__version__ = "{version}"\\n', encoding="utf-8")


def _class_rules() -> dict[str, dict[str, str]]:
    return {
        class_name: {field: f"{class_name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS}
        for class_name in DOCUMENT_CLASSES
    }


def _write_minimal_registry(project_root: Path) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": [
            {"path": "CHANGELOG.md", "class": "release", "owner": "maintainers"},
            {"path": "docs/STATUS.md", "class": "planning", "owner": "maintainers"},
        ],
    }
    (project_root / REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (project_root / REGISTRY_PATH).write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")


def _check_by_name(report: ReleaseStateReport, name: str) -> ReleaseCheckResult:
    for check in report.checks:
        if check.name == name:
            return check
    raise AssertionError(f"missing release check: {name}")


def _runner(
    *,
    local_tag: CommandResult = CommandResult(0, "", ""),
    remote_tag: CommandResult = CommandResult(0, "", ""),
    github_release: CommandResult = CommandResult(1, "", "release not found"),
):
    def run(_project_root: Path, command: Sequence[str]) -> CommandResult:
        if command[:3] == ["git", "tag", "-l"]:
            return local_tag
        if command[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return remote_tag
        if command[:3] == ["gh", "release", "view"]:
            return github_release
        raise AssertionError(f"unexpected command: {command}")

    return run
