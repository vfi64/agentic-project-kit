from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from string import Formatter

import yaml

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.cli_executable import default_agentic_kit
from agentic_project_kit.publication_policy import publication_policy_for
from agentic_project_kit.release_version_sources import WORKSPACE_MANIFEST
from agentic_project_kit.release import CommandResult
from agentic_project_kit.release_state import build_release_lifecycle_status
from agentic_project_kit.workspace_detection import is_agentic_project_kit_development_checkout


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
    approval_signature: str = ""
    approval_subject: dict[str, object] | None = None

    @property
    def ok(self) -> bool:
        return all(not _check_blocks(check) for check in self.checks)

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    @property
    def blockers(self) -> tuple[ReleasePublishCheck, ...]:
        return tuple(check for check in self.checks if _check_blocks(check))

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
            "approval_signature": self.approval_signature,
            "approval_subject": self.approval_subject,
        }



def _check_blocks(check: ReleasePublishCheck) -> bool:
    return check.status not in {"PASS", "SKIP"}


def _annotated_tag_command(tag: str) -> tuple[str, ...]:
    return ("git", "tag", "-a", tag, "-m", f"Release {tag}")


def _release_manifest(root: Path) -> dict[str, object]:
    path = root / WORKSPACE_MANIFEST
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"{WORKSPACE_MANIFEST}: cannot read release configuration: {exc}") from exc
    if not isinstance(loaded, dict):
        return {}
    release = loaded.get("release") or {}
    if not isinstance(release, dict):
        raise RuntimeError(f"{WORKSPACE_MANIFEST}:release: expected mapping")
    return release


def _configured_publish_checks(root: Path) -> set[str] | None:
    release = _release_manifest(root)
    value = release.get("publish_checks")
    if value is None:
        return None
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = [str(item) for item in value]
    else:
        raise RuntimeError(f"{WORKSPACE_MANIFEST}:release.publish_checks: expected string or list")
    normalized = {item.strip().lower().replace("_", "-") for item in raw if item.strip()}
    if normalized & {"all", "kit", "standard", "standard-audit-suite"}:
        return {"docs-audit", "command-reference-check"}
    if normalized & {"none", "skip", "external"}:
        return set()
    return normalized


def _should_run_publish_check(root: Path, check_name: str) -> bool:
    configured = _configured_publish_checks(root)
    if configured is not None:
        return check_name in configured
    if is_agentic_project_kit_development_checkout(root):
        return True
    if check_name == "docs-audit":
        return (root / "docs" / "DOCUMENTATION_REGISTRY.yaml").exists()
    if check_name == "command-reference-check":
        # Adopters also receive this generated projection. It does not opt them
        # into the development checkout's pytest-based reference check.
        return False
    return False


def _skip_publish_check(name: str, detail: str) -> ReleasePublishCheck:
    return ReleasePublishCheck(name=name, status="SKIP", detail=detail, returncode=0)


def _github_release_title_template(root: Path) -> str:
    release = _release_manifest(root)
    if "github_release_title_template" not in release:
        return ""
    value = release["github_release_title_template"]
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"{WORKSPACE_MANIFEST}:release.github_release_title_template: expected non-empty string"
        )
    return value.strip()


def _render_github_release_title(template: str, *, version: str, tag: str) -> str:
    if not template:
        return tag
    values = {"version": version, "tag": tag}
    parts: list[str] = []
    try:
        parsed = Formatter().parse(template)
        for literal_text, field_name, format_spec, conversion in parsed:
            parts.append(literal_text)
            if field_name is None:
                continue
            if field_name not in values or format_spec or conversion:
                allowed = ", ".join(sorted(values))
                raise RuntimeError(
                    f"{WORKSPACE_MANIFEST}:release.github_release_title_template: "
                    f"unsupported placeholder {field_name!r}; expected one of {allowed}"
                )
            parts.append(values[field_name])
    except ValueError as exc:
        raise RuntimeError(
            f"{WORKSPACE_MANIFEST}:release.github_release_title_template: invalid format string: {exc}"
        ) from exc
    title = "".join(parts).strip()
    if not title:
        raise RuntimeError(
            f"{WORKSPACE_MANIFEST}:release.github_release_title_template: rendered empty title"
        )
    return title


def _github_release_title(root: Path, *, version: str, tag: str) -> str:
    return _render_github_release_title(
        _github_release_title_template(root),
        version=version,
        tag=tag,
    )


def _local_tag_object_ref(tag: str) -> str:
    return f"refs/tags/{tag}"


def _append_annotated_local_tag_check(
    *,
    checks: list[ReleasePublishCheck],
    tag: str,
    root: Path,
    runner: Runner,
    check_name: str,
) -> bool:
    rc, output = runner(("git", "cat-file", "-t", _local_tag_object_ref(tag)), root)
    if rc != 0:
        checks.append(
            ReleasePublishCheck(
                name=check_name,
                status="FAIL",
                detail="could not inspect local tag object type: " + _last_line(output),
                returncode=rc,
            )
        )
        return False
    object_type = output.strip()
    if object_type != "tag":
        checks.append(
            ReleasePublishCheck(
                name=check_name,
                status="FAIL",
                detail=f"local tag object type is {object_type or 'unknown'}; annotated tag is required",
                returncode=1,
            )
        )
        return False
    return True


def _default_agentic_kit(root: Path) -> str:
    return default_agentic_kit(root)


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


def _release_commit_integrity_check(
    *,
    version: str,
    tag: str,
    root: Path,
    runner: Runner,
) -> ReleasePublishCheck:
    status_rc, status_output = runner(("git", "status", "--porcelain"), root)
    if status_rc != 0:
        return ReleasePublishCheck(
            name="release commit integrity",
            status="FAIL",
            detail="could not inspect worktree status: " + _last_line(status_output),
            returncode=status_rc,
        )
    if status_output.strip():
        return ReleasePublishCheck(
            name="release commit integrity",
            status="FAIL",
            detail="live release requires a clean worktree before tagging",
            returncode=1,
        )

    # KIT-GF-032: the workspace's own version anchors (the Kit's set when self-hosting).
    from agentic_project_kit.release_version_sources import release_version_anchors

    anchors = {anchor.path: anchor.pattern for anchor in release_version_anchors(root, version)}
    mismatches = []
    for relative_path, pattern in anchors.items():
        path = root / relative_path
        if not path.exists() or re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE) is None:
            mismatches.append(relative_path)
    if mismatches:
        return ReleasePublishCheck(
            name="release commit integrity",
            status="FAIL",
            detail="release metadata does not match target version: " + ", ".join(mismatches),
            returncode=1,
        )

    head_rc, head_output = runner(("git", "rev-parse", "HEAD"), root)
    if head_rc != 0:
        return ReleasePublishCheck(
            name="release commit integrity",
            status="FAIL",
            detail="could not resolve release commit: " + _last_line(head_output),
            returncode=head_rc,
        )
    tag_rc, tag_output = runner(("git", "rev-parse", "--verify", _local_tag_target(tag)), root)
    if tag_rc == 0 and tag_output.strip() != head_output.strip():
        return ReleasePublishCheck(
            name="release commit integrity",
            status="FAIL",
            detail=f"existing tag {tag} does not point to current release commit",
            returncode=1,
        )
    return ReleasePublishCheck(
        name="release commit integrity",
        status="PASS",
        detail="clean worktree and release metadata match the target commit",
        returncode=0,
    )


def _release_already_current_verified(
    *,
    version: str,
    root: Path,
    runner: Runner,
) -> bool:
    def state_runner(cwd: Path, args: Sequence[str]) -> CommandResult:
        returncode, output = runner(args, cwd)
        return CommandResult(returncode, output, "")

    try:
        status = build_release_lifecycle_status(
            root,
            version=version,
            command_runner=state_runner,
            include_remote=False,
        )
    except OSError:
        return False
    return status.current_state == "current_verified" and not status.blockers


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


def _first_remote_object_id(output: str) -> str:
    return output.split()[0] if output.split() else ""


def _local_tag_target(tag: str) -> str:
    return f"refs/tags/{tag}^{{}}"


def _remote_tag_target(
    *,
    tag_ref: str,
    root: Path,
    runner: Runner,
) -> tuple[int, str]:
    peeled_rc, peeled_output = runner(("git", "ls-remote", "--exit-code", "origin", f"{tag_ref}^{{}}"), root)
    if peeled_rc == 0:
        return peeled_rc, _first_remote_object_id(peeled_output)
    ref_rc, ref_output = runner(("git", "ls-remote", "--exit-code", "--refs", "origin", tag_ref), root)
    if ref_rc == 0:
        return ref_rc, _first_remote_object_id(ref_output)
    return ref_rc, ref_output




def _remote_tag_annotation_check(
    *,
    tag_ref: str,
    root: Path,
    runner: Runner,
    check_name: str,
) -> ReleasePublishCheck | None:
    rc, output = runner(("git", "ls-remote", "--exit-code", "origin", f"{tag_ref}^{{}}"), root)
    if rc == 0:
        return None
    return ReleasePublishCheck(
        name=check_name,
        status="FAIL",
        detail="remote tag is not an annotated tag or cannot be peeled: " + _last_line(output),
        returncode=1,
    )

def _current_head(root: Path, runner: Runner) -> str:
    rc, output = runner(("git", "rev-parse", "HEAD"), root)
    if rc != 0:
        return ""
    return output.strip()


def _approval_subject(
    *,
    version: str,
    tag: str,
    target_commit: str,
    publication_policy: str,
    planned_actions: Sequence[str],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "release_publish_approval",
        "version": version,
        "tag": tag,
        "target_commit": target_commit,
        "publication_policy": publication_policy,
        "planned_actions": list(planned_actions),
    }


def _approval_signature(subject: dict[str, object]) -> str:
    canonical = json.dumps(subject, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _append_live_release_publish_checks(
    *,
    checks: list[ReleasePublishCheck],
    executable: str,
    version: str,
    tag: str,
    root: Path,
    runner: Runner,
    release_title: str,
) -> None:
    tag_ref = f"refs/tags/{tag}"

    head_rc, head_output = runner(("git", "rev-parse", "HEAD"), root)
    if head_rc != 0:
        checks.append(
            ReleasePublishCheck(
                name=f"execute remote tag target {tag}",
                status="FAIL",
                detail="could not resolve current HEAD: " + _last_line(head_output),
                returncode=head_rc,
            )
        )
        return
    head = head_output.strip()

    tag_exists_rc, tag_exists_output = runner(("git", "rev-parse", "--verify", _local_tag_target(tag)), root)
    if tag_exists_rc == 0:
        if tag_exists_output.strip() != head:
            checks.append(
                ReleasePublishCheck(
                    name=f"execute local tag target {tag}",
                    status="FAIL",
                    detail=f"local tag points to {tag_exists_output.strip() or 'unknown'}, but current HEAD is {head}",
                    returncode=1,
                )
            )
            return
        if not _append_annotated_local_tag_check(
            checks=checks,
            tag=tag,
            root=root,
            runner=runner,
            check_name=f"execute annotated git tag {tag}",
        ):
            return
        checks.append(
            ReleasePublishCheck(
                name=f"execute annotated git tag {tag}",
                status="PASS",
                detail="local annotated tag already exists at current HEAD",
                returncode=0,
            )
        )
    else:
        rc, output = runner(_annotated_tag_command(tag), root)
        checks.append(_check_from_run(f"execute annotated git tag {tag}", rc, output))
        if rc != 0:
            return

    remote_exists_rc, remote_target_or_output = _remote_tag_target(tag_ref=tag_ref, root=root, runner=runner)
    if remote_exists_rc == 0:
        annotation_failure = _remote_tag_annotation_check(
            tag_ref=tag_ref,
            root=root,
            runner=runner,
            check_name=f"execute remote annotated tag {tag}",
        )
        if annotation_failure is not None:
            checks.append(annotation_failure)
            return
        remote_target = remote_target_or_output
        if remote_target != head:
            checks.append(
                ReleasePublishCheck(
                    name=f"execute remote tag target {tag}",
                    status="FAIL",
                    detail=(
                        f"remote tag points to {remote_target or 'unknown'}, "
                        f"but current HEAD is {head}"
                    ),
                    returncode=1,
                )
            )
            return
        checks.append(
            ReleasePublishCheck(
                name=f"execute git push origin {tag}",
                status="PASS",
                detail="remote tag already exists at current HEAD",
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
        create_command = ("gh", "release", "create", tag, "--title", release_title, "--notes", notes)
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


def _append_private_tag_publish_checks(
    *,
    checks: list[ReleasePublishCheck],
    tag: str,
    root: Path,
    runner: Runner,
) -> None:
    tag_ref = f"refs/tags/{tag}"
    head_rc, head_output = runner(("git", "rev-parse", "HEAD"), root)
    if head_rc != 0:
        checks.append(
            ReleasePublishCheck(
                name=f"execute private tag target {tag}",
                status="FAIL",
                detail="could not resolve current HEAD: " + _last_line(head_output),
                returncode=head_rc,
            )
        )
        return
    head = head_output.strip()

    tag_exists_rc, tag_exists_output = runner(("git", "rev-parse", "--verify", _local_tag_target(tag)), root)
    if tag_exists_rc == 0:
        if tag_exists_output.strip() != head:
            checks.append(
                ReleasePublishCheck(
                    name=f"execute private tag target {tag}",
                    status="FAIL",
                    detail=f"local tag points to {tag_exists_output.strip() or 'unknown'}, but current HEAD is {head}",
                    returncode=1,
                )
            )
            return
        if not _append_annotated_local_tag_check(
            checks=checks,
            tag=tag,
            root=root,
            runner=runner,
            check_name=f"execute annotated private tag {tag}",
        ):
            return
        checks.append(
            ReleasePublishCheck(
                name=f"execute annotated private tag {tag}",
                status="PASS",
                detail="local annotated tag already exists at current HEAD",
                returncode=0,
            )
        )
    else:
        rc, output = runner(_annotated_tag_command(tag), root)
        checks.append(_check_from_run(f"execute annotated private tag {tag}", rc, output))
        if rc != 0:
            return

    remote_exists_rc, remote_target_or_output = _remote_tag_target(tag_ref=tag_ref, root=root, runner=runner)
    if remote_exists_rc == 0:
        annotation_failure = _remote_tag_annotation_check(
            tag_ref=tag_ref,
            root=root,
            runner=runner,
            check_name=f"execute remote annotated tag {tag}",
        )
        if annotation_failure is not None:
            checks.append(annotation_failure)
            return
        remote_target = remote_target_or_output
        if remote_target != head:
            checks.append(
                ReleasePublishCheck(
                    name=f"execute private remote tag target {tag}",
                    status="FAIL",
                    detail=f"remote tag points to {remote_target or 'unknown'}, but current HEAD is {head}",
                    returncode=1,
                )
            )
            return
        checks.append(
            ReleasePublishCheck(
                name=f"execute git push origin {tag}",
                status="PASS",
                detail="remote tag already exists at current HEAD",
                returncode=0,
            )
        )
    else:
        rc, output = runner(("git", "push", "origin", tag), root)
        checks.append(_check_from_run(f"execute git push origin {tag}", rc, output))


def evaluate_release_publish_plan(
    root: Path = Path("."),
    *,
    version: str = PACKAGE_VERSION,
    dry_run: bool = True,
    execute: bool = False,
    runner: Runner | None = None,
    allow_execute: bool = False,
    expected_signature: str = "",
) -> ReleasePublishPlan:
    root = root.resolve()
    run = runner or _default_runner
    executable = _default_agentic_kit(root)
    tag = f"v{version}"

    checks: list[ReleasePublishCheck] = []
    policy = publication_policy_for(root)
    private_publication = policy.value == "none"
    release_title = tag

    release_already_current_verified = _release_already_current_verified(version=version, root=root, runner=run)

    if not dry_run and not execute:
        checks.append(
            ReleasePublishCheck(
                name="mode",
                status="FAIL",
                detail="release-publish requires --dry-run or --execute",
            )
        )

    if release_already_current_verified:
        checks.append(
            ReleasePublishCheck(
                name="release-prep dry-run",
                status="PASS",
                detail="Skipped because release lifecycle state is already current_verified.",
                returncode=0,
            )
        )
    else:
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
    if private_publication:
        checks.append(
            ReleasePublishCheck(
                name="publication policy",
                status="PASS",
                detail="publication: none; private release will push an annotated tag only",
                returncode=0,
            )
        )
    else:
        if _should_run_publish_check(root, "docs-audit"):
            checks.append(
                _run_check(
                    name="docs audit",
                    args=(executable, "docs-audit"),
                    root=root,
                    runner=run,
                )
            )
        else:
            checks.append(
                _skip_publish_check(
                    "docs audit",
                    "skipped outside a workspace that declares the Kit documentation registry",
                )
            )
        if _should_run_publish_check(root, "command-reference-check"):
            checks.append(
                _run_check(
                    name="command reference check",
                    args=(executable, "transfer", "command-reference-check"),
                    root=root,
                    runner=run,
                )
            )
        else:
            checks.append(
                _skip_publish_check(
                    "command reference check",
                    "skipped outside a workspace that declares the Kit command reference",
                )
            )
        try:
            release_title = _github_release_title(root, version=version, tag=tag)
        except RuntimeError as exc:
            checks.append(
                ReleasePublishCheck(
                    name="GitHub release title configuration",
                    status="FAIL",
                    detail=str(exc),
                    returncode=1,
                )
            )
        else:
            checks.append(
                ReleasePublishCheck(
                    name="GitHub release title configuration",
                    status="PASS",
                    detail=f"GitHub release title: {release_title}",
                    returncode=0,
                )
            )
    if execute:
        checks.append(
            _release_commit_integrity_check(
                version=version,
                tag=tag,
                root=root,
                runner=run,
            )
        )

    planned_actions = [
        f"verify release-prep evidence for {version}",
        f"verify release metadata authority for {version}",
        f"plan annotated git tag {tag}",
    ]
    if private_publication:
        planned_actions.append(f"plan git push origin {tag}")
        planned_actions.append("skip GitHub Release, PyPI, and Zenodo publication because publication is none")
    else:
        planned_actions.extend([f"plan GitHub release {tag} titled {release_title}", "plan post-release-check after live publish"])

    target_commit = _current_head(root, run)
    subject = _approval_subject(
        version=version,
        tag=tag,
        target_commit=target_commit,
        publication_policy=policy.value,
        planned_actions=planned_actions,
    )
    signature = _approval_signature(subject) if target_commit else ""

    capability_file = root / EXECUTE_CAPABILITY_PATH
    execute_capability_present = capability_file.exists()
    signature_matches = bool(expected_signature) and expected_signature == signature
    if execute and expected_signature and not signature_matches:
        checks.append(
            ReleasePublishCheck(
                name="release publish signature",
                status="FAIL",
                detail="expected signature does not match the current release-publish plan",
                returncode=2,
            )
        )
    if execute and not (allow_execute and (execute_capability_present or signature_matches)):
        checks.append(
            ReleasePublishCheck(
                name="execute capability",
                status="FAIL",
                detail=(
                    "live release publishing requires --allow-execute plus either "
                    f"{EXECUTE_CAPABILITY_PATH} or a matching --expected-signature"
                ),
                returncode=2,
            )
        )

    live_execute_ready = execute and allow_execute and (execute_capability_present or signature_matches) and all(
        not _check_blocks(check) for check in checks
    )
    if live_execute_ready:
        if private_publication:
            planned_actions.extend([f"execute annotated private tag {tag}", f"execute git push origin {tag}"])
            _append_private_tag_publish_checks(
                checks=checks,
                tag=tag,
                root=root,
                runner=run,
            )
        else:
            planned_actions.extend(
                [
                    f"execute annotated git tag {tag}",
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
                release_title=release_title,
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
        execute_enabled=live_execute_ready and all(not _check_blocks(check) for check in checks),
        approval_signature=signature,
        approval_subject=subject,
    )


def render_release_publish_plan(plan: ReleasePublishPlan) -> str:
    lines = [
        "RELEASE_PUBLISH_ORCHESTRATION",
        f"STATUS={plan.status}",
        f"VERSION={plan.version}",
        f"TAG={plan.tag}",
        f"MODE={plan.mode}",
        f"EXECUTE_ENABLED={str(plan.execute_enabled).lower()}",
        f"APPROVAL_SIGNATURE={plan.approval_signature}",
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
