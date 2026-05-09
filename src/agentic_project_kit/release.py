from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import subprocess


@dataclass(frozen=True)
class ReleaseStep:
    name: str
    commands: tuple[str, ...]
    evidence: str


@dataclass(frozen=True)
class ReleasePlan:
    version: str
    steps: tuple[ReleaseStep, ...]
    warnings: tuple[str, ...]


class ReleaseCheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass(frozen=True)
class ReleaseCheckResult:
    name: str
    status: ReleaseCheckStatus
    detail: str


@dataclass(frozen=True)
class ReleaseStateReport:
    version: str
    checks: tuple[ReleaseCheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(check.status != ReleaseCheckStatus.FAIL for check in self.checks)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[Path, Sequence[str]], CommandResult]


def build_release_plan(project_root: Path, version: str | None = None) -> ReleasePlan:
    resolved_version = version or read_project_version(project_root)
    warnings = tuple(validate_version(resolved_version))
    return ReleasePlan(
        version=resolved_version,
        steps=(
            ReleaseStep(
                name="Confirm clean repository state",
                commands=("git status --short", "git log --oneline -8"),
                evidence="No unexpected local changes; recent commits match intended release scope.",
            ),
            ReleaseStep(
                name="Run local quality gates",
                commands=("python -m pytest -q", "ruff check .", "agentic-kit check-docs"),
                evidence="Tests, linting, and state-gate checks pass.",
            ),
            ReleaseStep(
                name="Validate package artifacts",
                commands=(
                    "rm -rf dist build",
                    "find . -maxdepth 3 -name '*.egg-info' -type d -prune -exec rm -rf {} +",
                    "python -m build",
                    "twine check dist/*",
                    "ls -lh dist/",
                ),
                evidence="Wheel and sdist build successfully and pass twine validation.",
            ),
            ReleaseStep(
                name="Check release notes and state files",
                commands=(
                    "grep -n 'v{version}' CHANGELOG.md".format(version=resolved_version),
                    "grep -n 'Current version: {version}' docs/STATUS.md".format(version=resolved_version),
                    "grep -n 'Current version: {version}' docs/handoff/CURRENT_HANDOFF.md".format(
                        version=resolved_version
                    ),
                ),
                evidence="CHANGELOG, STATUS, and CURRENT_HANDOFF mention the target release version.",
            ),
            ReleaseStep(
                name="Verify target tag and release are unused",
                commands=(
                    "git fetch --tags",
                    "git tag -l v{version}".format(version=resolved_version),
                    "git ls-remote --tags origin v{version}".format(version=resolved_version),
                    "gh release view v{version}".format(version=resolved_version),
                ),
                evidence="Local tag, remote tag, and GitHub release lookups show no existing target release.",
            ),
            ReleaseStep(
                name="Create and verify tag",
                commands=(
                    "git tag v{version}".format(version=resolved_version),
                    "git push origin v{version}".format(version=resolved_version),
                    "gh run list --workflow Release --limit 5",
                    "gh release view v{version}".format(version=resolved_version),
                ),
                evidence="Release workflow succeeds and the GitHub release exists.",
            ),
        ),
        warnings=warnings,
    )


def build_release_state_report(
    project_root: Path,
    version: str | None = None,
    command_runner: CommandRunner = run_command,
) -> ReleaseStateReport:
    resolved_version = version or read_project_version(project_root)
    checks = [
        check_semantic_version(resolved_version),
        check_file_contains(project_root / "CHANGELOG.md", f"v{resolved_version}", "CHANGELOG version"),
        check_file_contains(project_root / "docs/STATUS.md", f"Current version: {resolved_version}", "STATUS version"),
        check_file_contains(
            project_root / "docs/handoff/CURRENT_HANDOFF.md",
            f"Current version: {resolved_version}",
            "CURRENT_HANDOFF version",
        ),
        check_local_tag_absent(project_root, resolved_version, command_runner),
        check_remote_tag_absent(project_root, resolved_version, command_runner),
        check_github_release_absent(project_root, resolved_version, command_runner),
    ]
    return ReleaseStateReport(version=resolved_version, checks=tuple(checks))


def check_semantic_version(version: str) -> ReleaseCheckResult:
    warnings = validate_version(version)
    if warnings:
        return ReleaseCheckResult("semantic version", ReleaseCheckStatus.FAIL, warnings[0])
    return ReleaseCheckResult("semantic version", ReleaseCheckStatus.PASS, f"{version} is valid")


def check_file_contains(path: Path, needle: str, name: str) -> ReleaseCheckResult:
    if not path.exists():
        return ReleaseCheckResult(name, ReleaseCheckStatus.FAIL, f"missing file: {path}")
    content = path.read_text(encoding="utf-8")
    if needle not in content:
        return ReleaseCheckResult(name, ReleaseCheckStatus.FAIL, f"missing text: {needle}")
    return ReleaseCheckResult(name, ReleaseCheckStatus.PASS, f"found text: {needle}")


def check_local_tag_absent(project_root: Path, version: str, command_runner: CommandRunner = run_command) -> ReleaseCheckResult:
    tag = f"v{version}"
    result = command_runner(project_root, ["git", "tag", "-l", tag])
    if result.returncode != 0:
        return ReleaseCheckResult("local tag unused", ReleaseCheckStatus.WARN, result.stderr.strip() or "git tag failed")
    if result.stdout.strip():
        return ReleaseCheckResult("local tag unused", ReleaseCheckStatus.FAIL, f"tag already exists: {tag}")
    return ReleaseCheckResult("local tag unused", ReleaseCheckStatus.PASS, f"tag is unused: {tag}")


def check_remote_tag_absent(project_root: Path, version: str, command_runner: CommandRunner = run_command) -> ReleaseCheckResult:
    tag = f"v{version}"
    result = command_runner(project_root, ["git", "ls-remote", "--tags", "origin", tag])
    if result.returncode != 0:
        return ReleaseCheckResult(
            "remote tag unused",
            ReleaseCheckStatus.WARN,
            result.stderr.strip() or "git ls-remote failed",
        )
    if result.stdout.strip():
        return ReleaseCheckResult("remote tag unused", ReleaseCheckStatus.FAIL, f"remote tag already exists: {tag}")
    return ReleaseCheckResult("remote tag unused", ReleaseCheckStatus.PASS, f"remote tag is unused: {tag}")


def check_github_release_absent(project_root: Path, version: str, command_runner: CommandRunner = run_command) -> ReleaseCheckResult:
    tag = f"v{version}"
    result = command_runner(project_root, ["gh", "release", "view", tag])
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode == 0:
        return ReleaseCheckResult("GitHub release unused", ReleaseCheckStatus.FAIL, f"GitHub release already exists: {tag}")
    if _looks_like_missing_github_release(output):
        return ReleaseCheckResult("GitHub release unused", ReleaseCheckStatus.PASS, f"GitHub release is absent: {tag}")
    return ReleaseCheckResult("GitHub release unused", ReleaseCheckStatus.WARN, output or "gh release view failed")


def _looks_like_missing_github_release(output: str) -> bool:
    normalized = output.lower()
    return any(fragment in normalized for fragment in ("not found", "release not found", "http 404"))


def run_command(project_root: Path, command: Sequence[str]) -> CommandResult:
    try:
        result = subprocess.run(
            list(command),
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return CommandResult(returncode=127, stdout="", stderr=f"could not run {command[0]}: {exc}")
    return CommandResult(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)


def read_project_version(project_root: Path) -> str:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        raise FileNotFoundError(f"Missing pyproject.toml: {pyproject}")

    match = re.search(r'^version = "([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find project version in {pyproject}")
    return match.group(1)


def validate_version(version: str) -> list[str]:
    warnings: list[str] = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        warnings.append(f"Version {version!r} is not a simple semantic version like 1.2.3.")
    return warnings


def render_release_plan(plan: ReleasePlan) -> str:
    lines = [f"# Release preparation plan for target v{plan.version}", ""]

    if plan.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in plan.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Steps")
    lines.append("")
    for index, step in enumerate(plan.steps, start=1):
        lines.append(f"### {index}. {step.name}")
        lines.append("")
        lines.append("Commands:")
        lines.append("")
        lines.append("```bash")
        lines.extend(step.commands)
        lines.append("```")
        lines.append("")
        lines.append(f"Evidence: {step.evidence}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_release_state_report(report: ReleaseStateReport) -> str:
    lines = [f"Release state check for target v{report.version}", ""]
    for check in report.checks:
        lines.append(f"[{check.status.value}] {check.name}: {check.detail}")
    lines.append("")
    lines.append("Overall: PASS" if report.ok else "Overall: FAIL")
    return "\n".join(lines) + "\n"
