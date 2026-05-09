from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


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
                evidence="CHANGELOG, STATUS, and CURRENT_HANDOFF mention the release version.",
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
    lines = [f"# Release preparation plan for v{plan.version}", ""]

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
