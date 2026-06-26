from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
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


def _current_changelog_release_metadata(root: Path, version: str) -> tuple[str | None, tuple[str, ...]]:
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return None, ()
    text = changelog.read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^##\s+v{re.escape(version)}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})\n\n(.*?)(?=^##\s+v|\Z)",
        text,
    )
    if not match:
        return None, ()
    summary_lines = tuple(
        line.strip()[2:].strip()
        for line in match.group(2).splitlines()
        if line.strip().startswith("- ")
    )
    return match.group(1), summary_lines


def _release_prep_dry_run_args(executable: str, version: str, root: Path) -> tuple[str, ...]:
    release_date, summary_lines = _current_changelog_release_metadata(root, version)
    args: list[str] = [
        executable,
        "release-prep",
        "--version",
        version,
        "--dry-run",
        "--json",
    ]
    if release_date:
        args.extend(["--date", release_date])
    if summary_lines:
        for line in summary_lines:
            args.extend(["--summary-line", line])
    else:
        args.extend(
            [
                "--summary-line",
                f"Release metadata prepared for v{version}; publish and DOI verification remain separate guarded steps.",
            ]
        )
    return tuple(args)


def _run_release_prep_consistency_check(
    *,
    executable: str,
    version: str,
    root: Path,
    runner: Runner,
) -> ReleasePublishCheck:
    args = _release_prep_dry_run_args(executable, version, root)
    returncode, output = runner(args, root)
    if returncode != 0:
        return ReleasePublishCheck(
            name="release-prep dry-run",
            status="FAIL",
            detail=_last_line(output),
            returncode=returncode,
        )
    try:
        payload = json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        return ReleasePublishCheck(
            name="release-prep dry-run",
            status="FAIL",
            detail=f"release-prep dry-run did not return JSON: {exc}",
            returncode=1,
        )
    changed_paths = payload.get("changed_paths") if isinstance(payload, dict) else None
    if not isinstance(changed_paths, list):
        return ReleasePublishCheck(
            name="release-prep dry-run",
            status="FAIL",
            detail="release-prep dry-run JSON missing changed_paths",
            returncode=1,
        )
    if changed_paths:
        return ReleasePublishCheck(
            name="release-prep dry-run",
            status="FAIL",
            detail="release-prep dry-run would change paths: " + ", ".join(str(path) for path in changed_paths),
            returncode=1,
        )
    return ReleasePublishCheck(
        name="release-prep dry-run",
        status="PASS",
        detail="No release metadata anchor files changed.",
        returncode=0,
    )


def _github_release_notes(root: Path, version: str) -> str:
    release_date, summary_lines = _current_changelog_release_metadata(root, version)
    if not summary_lines:
        return f"Release v{version}."
    heading = f"Release v{version}"
    if release_date:
        heading += f" - {release_date}"
    body = "\n".join(f"- {line}" for line in summary_lines)
    return f"{heading}\n\n{body}"


def _check_from_run(name: str, returncode: int, output: str, *, pass_detail: str = "") -> ReleasePublishCheck:
    return ReleasePublishCheck(
        name=name,
        status="PASS" if returncode == 0 else "FAIL",
        detail=pass_detail or _last_line(output),
        returncode=returncode,
    )


def _append_live_release_publish_checks(
    *,
    checks: list[ReleasePublishCheck],
    executable: str,
    version: str,
    tag: str,
    root: Path,
    runner: Runner,
) -> None:
    tag_ref = f"refs/tags/{tag}"

    tag_exists_rc, _tag_exists_output = runner(("git", "rev-parse", "--verify", tag_ref), root)
    if tag_exists_rc == 0:
        checks.append(
            ReleasePublishCheck(
                name=f"execute git tag {tag}",
                status="PASS",
                detail="local tag already exists",
                returncode=0,
            )
        )
    else:
        rc, output = runner(("git", "tag", tag), root)
        checks.append(_check_from_run(f"execute git tag {tag}", rc, output))
        if rc != 0:
            return

    remote_exists_rc, _remote_exists_output = runner(("git", "ls-remote", "--exit-code", "--tags", "origin", tag), root)
    if remote_exists_rc == 0:
        checks.append(
            ReleasePublishCheck(
                name=f"execute git push origin {tag}",
                status="PASS",
                detail="remote tag already exists",
                returncode=0,
            )
        )
    else:
        rc, output = runner(("git", "push", "origin", tag), root)
        checks.append(_check_from_run(f"execute git push origin {tag}", rc, output))
        if rc != 0:
            return

    release_view_rc, release_view_output = runner(("gh", "release", "view", tag), root)
    if release_view_rc == 0:
        checks.append(
            ReleasePublishCheck(
                name=f"execute gh release view {tag}",
                status="PASS",
                detail="GitHub release already exists",
                returncode=0,
            )
        )
    else:
        notes = _github_release_notes(root, version)
        create_command = ("gh", "release", "create", tag, "--title", tag, "--notes", notes)
        create_rc, create_output = runner(create_command, root)
        checks.append(_check_from_run(f"execute gh release create {tag}", create_rc, create_output))
        if create_rc != 0:
            return
        verify_rc, verify_output = runner(("gh", "release", "view", tag), root)
        checks.append(_check_from_run(f"execute gh release view {tag}", verify_rc, verify_output, pass_detail="GitHub release exists"))
        if verify_rc != 0:
            return

    rc, output = runner((executable, "post-release-check", "--version", version), root)
    checks.append(_check_from_run(f"execute post-release-check --version {version}", rc, output))


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
        _run_release_prep_consistency_check(
            executable=executable,
            version=version,
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
                f"execute GitHub release create/view for {tag}",
                f"execute post-release-check --version {version}",
            ]
        )
        _append_live_release_publish_checks(
            checks=checks,
            executable=executable,
            version=version,
            tag=tag,
            root=root,
            runner=run,
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
