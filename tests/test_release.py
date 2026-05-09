from pathlib import Path
from collections.abc import Sequence

from agentic_project_kit.release import (
    CommandResult,
    ReleaseCheckStatus,
    build_release_plan,
    build_release_state_report,
    render_release_plan,
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
    assert [check.status for check in report.checks] == [ReleaseCheckStatus.PASS] * 7


def test_build_release_state_report_warns_without_git_repo(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path)

    assert report.ok
    assert report.checks[-3].status == ReleaseCheckStatus.WARN
    assert report.checks[-3].detail
    assert report.checks[-3].name == "local tag unused"


def test_build_release_state_report_warns_when_remote_tag_check_is_unavailable(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(remote_tag=CommandResult(2, "", "fatal: 'origin' does not appear to be a git repository")),
    )

    assert report.ok
    assert report.checks[-2].status == ReleaseCheckStatus.WARN
    assert report.checks[-2].name == "remote tag unused"


def test_build_release_state_report_warns_when_github_release_check_is_unavailable(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(127, "", "could not run gh: not found")),
    )

    assert report.ok
    assert report.checks[-1].status == ReleaseCheckStatus.WARN
    assert report.checks[-1].name == "GitHub release unused"


def test_build_release_state_report_fails_for_missing_changelog_version(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    report = build_release_state_report(tmp_path, command_runner=_runner())

    assert not report.ok
    assert report.checks[1].status == ReleaseCheckStatus.FAIL
    assert "missing text: v1.2.3" in report.checks[1].detail


def test_build_release_state_report_fails_for_existing_local_tag(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path, command_runner=_runner(local_tag=CommandResult(0, "v1.2.3\n", "")))

    assert not report.ok
    assert report.checks[-3].status == ReleaseCheckStatus.FAIL
    assert report.checks[-3].detail == "tag already exists: v1.2.3"


def test_build_release_state_report_fails_for_existing_remote_tag(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(
        tmp_path,
        command_runner=_runner(remote_tag=CommandResult(0, "abc123\trefs/tags/v1.2.3\n", "")),
    )

    assert not report.ok
    assert report.checks[-2].status == ReleaseCheckStatus.FAIL
    assert report.checks[-2].detail == "remote tag already exists: v1.2.3"


def test_build_release_state_report_fails_for_existing_github_release(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    report = build_release_state_report(tmp_path, command_runner=_runner(github_release=CommandResult(0, "title: v1.2.3\n", "")))

    assert not report.ok
    assert report.checks[-1].status == ReleaseCheckStatus.FAIL
    assert report.checks[-1].detail == "GitHub release already exists: v1.2.3"


def test_render_release_state_report_shows_overall_status(tmp_path: Path):
    _write_release_files(tmp_path, "1.2.3")

    rendered = render_release_state_report(build_release_state_report(tmp_path, command_runner=_runner()))

    assert "Release state check for target v1.2.3" in rendered
    assert "[PASS] semantic version" in rendered
    assert "[PASS] remote tag unused" in rendered
    assert "[PASS] GitHub release unused" in rendered
    assert "Overall: PASS" in rendered


def _write_release_files(project_root: Path, version: str) -> None:
    (project_root / "docs/handoff").mkdir(parents=True)
    (project_root / "pyproject.toml").write_text(f'version = "{version}"\n', encoding="utf-8")
    (project_root / "CHANGELOG.md").write_text(f"# Changelog\n\n## v{version}\n", encoding="utf-8")
    (project_root / "docs/STATUS.md").write_text(f"Current version: {version}\n", encoding="utf-8")
    (project_root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        f"Current version: {version}\n", encoding="utf-8"
    )


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
