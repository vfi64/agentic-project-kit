from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import subprocess

from agentic_project_kit import __version__ as PACKAGE_VERSION


Runner = Callable[[Sequence[str], Path], tuple[int, str]]

EXECUTE_CAPABILITY_PATH = ".agentic/release/ENABLE_LIVE_PUBLISH"


@dataclass(frozen=True)
class ReleasePublishCheck:
    name: str
    status: str
    detail: str
    returncode: int | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReleasePublishPlan:
    version: str
    tag: str
    root: str
    mode: str
    checks: tuple[ReleasePublishCheck, ...]
    planned_actions: tuple[str, ...]
    execute_enabled: bool

    @property
    def ok(self) -> bool:
        return all(check.status == "PASS" for check in self.checks)

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    @property
    def blockers(self) -> tuple[ReleasePublishCheck, ...]:
        return tuple(check for check in self.checks if check.status != "PASS")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "release_publish_orchestration",
            "version": self.version,
            "tag": self.tag,
            "root": self.root,
            "mode": self.mode,
            "status": self.status,
            "execute_enabled": self.execute_enabled,
            "check_count": len(self.checks),
            "blocker_count": len(self.blockers),
            "checks": [check.as_dict() for check in self.checks],
            "blockers": [check.as_dict() for check in self.blockers],
            "planned_actions": list(self.planned_actions),
        }


def _default_agentic_kit(root: Path) -> str:
    local = root / ".venv" / "bin" / "agentic-kit"
    if local.exists():
        return local.as_posix()
    found = shutil.which("agentic-kit")
    return found or "agentic-kit"


def _default_runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def _last_line(output: str) -> str:
    stripped = output.strip()
    if not stripped:
        return "no output"
    return stripped.splitlines()[-1][:500]


def _run_check(
    *,
    name: str,
    args: Sequence[str],
    root: Path,
    runner: Runner,
) -> ReleasePublishCheck:
    returncode, output = runner(args, root)
    return ReleasePublishCheck(
        name=name,
        status="PASS" if returncode == 0 else "FAIL",
        detail=_last_line(output),
        returncode=returncode,
    )


def evaluate_release_publish_plan(
    root: Path = Path("."),
    *,
    version: str = PACKAGE_VERSION,
    dry_run: bool = True,
    execute: bool = False,
    runner: Runner | None = None,
    allow_execute: bool = False,
) -> ReleasePublishPlan:
    root = root.resolve()
    run = runner or _default_runner
    executable = _default_agentic_kit(root)
    tag = f"v{version}"

    checks: list[ReleasePublishCheck] = []

    if not dry_run and not execute:
        checks.append(
            ReleasePublishCheck(
                name="mode",
                status="FAIL",
                detail="release-publish requires --dry-run or --execute",
            )
        )

    checks.append(
        _run_check(
            name="release-prep dry-run",
            args=(
                executable,
                "release-prep",
                "--version",
                version,
                "--summary-line",
                f"Release metadata prepared for v{version}; publish and DOI verification remain separate guarded steps.",
                "--dry-run",
            ),
            root=root,
            runner=run,
        )
    )
    checks.append(
        _run_check(
            name="release metadata authority gate",
            args=(
                executable,
                "release-metadata-authority-gate",
                "--version",
                version,
                "--base-ref",
                "origin/main",
            ),
            root=root,
            runner=run,
        )
    )
    checks.append(
        _run_check(
            name="docs audit",
            args=(executable, "docs-audit"),
            root=root,
            runner=run,
        )
    )
    checks.append(
        _run_check(
            name="command reference check",
            args=(executable, "transfer", "command-reference-check"),
            root=root,
            runner=run,
        )
    )

    capability_file = root / EXECUTE_CAPABILITY_PATH
    execute_capability_present = capability_file.exists()

    if execute and not (allow_execute and execute_capability_present):
        checks.append(
            ReleasePublishCheck(
                name="execute capability",
                status="FAIL",
                detail=(
                    "live release publishing requires --allow-execute and "
                    f"{EXECUTE_CAPABILITY_PATH}; dry-run remains the default supported path"
                ),
                returncode=2,
            )
        )

    planned_actions = [
        f"verify release-prep evidence for {version}",
        f"verify release metadata authority for {version}",
        f"plan git tag {tag}",
        f"plan GitHub release {tag}",
        "plan post-release-check after live publish",
    ]
    if execute and allow_execute and execute_capability_present:
        planned_actions.extend(
            [
                f"execute git tag {tag}",
                f"execute git push origin {tag}",
                f"execute GitHub release publish for {tag}",
                f"execute post-release-check --version {version}",
            ]
        )
        live_commands: tuple[tuple[str, ...], ...] = (
            ("git", "tag", tag),
            ("git", "push", "origin", tag),
            ("gh", "release", "view", tag),
            (executable, "post-release-check", "--version", version),
        )
        for command in live_commands:
            checks.append(
                _run_check(
                    name="execute " + " ".join(command),
                    args=command,
                    root=root,
                    runner=run,
                )
            )
    else:
        planned_actions.append("perform no tag, release, DOI, or metadata write in dry-run/fail-closed mode")

    return ReleasePublishPlan(
        version=version,
        tag=tag,
        root=root.as_posix(),
        mode="execute" if execute else "dry-run" if dry_run else "unspecified",
        checks=tuple(checks),
        planned_actions=tuple(planned_actions),
        execute_enabled=bool(execute and allow_execute and execute_capability_present),
    )


def render_release_publish_plan(plan: ReleasePublishPlan) -> str:
    lines = [
        "RELEASE_PUBLISH_ORCHESTRATION",
        f"STATUS={plan.status}",
        f"VERSION={plan.version}",
        f"TAG={plan.tag}",
        f"MODE={plan.mode}",
        f"EXECUTE_ENABLED={str(plan.execute_enabled).lower()}",
        f"CHECK_COUNT={len(plan.checks)}",
        f"BLOCKER_COUNT={len(plan.blockers)}",
    ]
    for blocker in plan.blockers:
        lines.append(f"BLOCKER={blocker.name}|{blocker.returncode}|{blocker.detail}")
    for check in plan.checks:
        lines.append(f"CHECK={check.status}|{check.name}|{check.returncode}|{check.detail}")
    for action in plan.planned_actions:
        lines.append(f"PLAN={action}")
    return "\n".join(lines) + "\n"
