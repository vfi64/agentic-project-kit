from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any

from agentic_project_kit.release_state import (
    ReleaseLifecycleStatus,
    build_release_lifecycle_status,
)


GitRunner = Callable[[Path, Sequence[str]], "GitResult"]
ReleaseStatusBuilder = Callable[[Path], ReleaseLifecycleStatus]


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class StatusCurrentStateFinding:
    path: str
    check: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StatusCurrentStateAuditResult:
    root: str
    package_version: str | None
    status_version: str | None
    status_current_verified_release: str | None
    status_current_verified_main: str | None
    validation_status: str | None
    validation_generated_head: str | None
    origin_main: str | None
    release_current_state: str | None
    findings: tuple[StatusCurrentStateFinding, ...]
    blockers: tuple[StatusCurrentStateFinding, ...]
    warnings: tuple[StatusCurrentStateFinding, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "status_current_state_audit",
            "root": self.root,
            "status": self.status,
            "package_version": self.package_version,
            "status_version": self.status_version,
            "status_current_verified_release": self.status_current_verified_release,
            "status_current_verified_main": self.status_current_verified_main,
            "validation_status": self.validation_status,
            "validation_generated_head": self.validation_generated_head,
            "origin_main": self.origin_main,
            "release_current_state": self.release_current_state,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "findings": [finding.as_dict() for finding in self.findings],
            "blockers": [finding.as_dict() for finding in self.blockers],
            "warnings": [finding.as_dict() for finding in self.warnings],
        }


def audit_status_current_state(
    root: Path = Path("."),
    *,
    git_runner: GitRunner | None = None,
    release_status_builder: ReleaseStatusBuilder | None = None,
    max_origin_lag: int = 3,
) -> StatusCurrentStateAuditResult:
    root = root.resolve()
    findings: list[StatusCurrentStateFinding] = []
    blockers: list[StatusCurrentStateFinding] = []
    warnings: list[StatusCurrentStateFinding] = []
    run_git = git_runner or _run_git

    pyproject_version = _project_version(root)
    status_text = _read_text(root / "docs" / "STATUS.md")
    validation = _read_json(root / "docs" / "reports" / "handoff-packages" / "latest" / "validation_report.json")
    current_block = _current_state_block(status_text)
    status_version = _match(r"^Current version:\s*([^\s.]+(?:\.[^\s.]+){2})\.?$", current_block)
    status_release = _match(r"^Current verified release:\s*v?([0-9]+\.[0-9]+\.[0-9]+)\.?", current_block)
    status_verified_version_doi = _status_verified_version_doi(current_block)
    status_main = _current_verified_main(current_block)
    validation_status = _string_or_none(validation.get("status"))
    validation_head = _string_or_none(validation.get("generated_head"))
    origin_main = _origin_main(root, run_git)
    release_status = _build_release_status(root, release_status_builder)
    release_current_state = release_status.current_state if release_status is not None else None

    _finding(findings, blockers, "docs/STATUS.md", "status_file_exists", bool(status_text), "exists" if status_text else "missing")
    _finding(findings, blockers, "pyproject.toml", "package_version_exists", pyproject_version is not None, f"version={pyproject_version}")
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "current_state_block_exists",
        bool(current_block),
        "## Current State block found" if current_block else "## Current State block missing",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_current_version_matches_pyproject",
        bool(pyproject_version and status_version == pyproject_version),
        f"status={status_version}, pyproject={pyproject_version}",
    )
    _audit_status_release_marker(
        findings=findings,
        blockers=blockers,
        release_status=release_status,
        pyproject_version=pyproject_version,
        status_release=status_release,
    )
    _audit_changelog_current_pending_doi(
        findings=findings,
        blockers=blockers,
        root=root,
        pyproject_version=pyproject_version,
        status_version=status_version,
        status_verified_version_doi=status_verified_version_doi,
    )
    _audit_status_main_marker(
        findings=findings,
        blockers=blockers,
        status_text=status_text,
        current_block=current_block,
        status_main=status_main,
        validation_head=validation_head,
    )
    _finding(
        findings,
        blockers,
        "docs/reports/handoff-packages/latest/validation_report.json",
        "validation_report_status_pass",
        validation_status == "PASS",
        f"status={validation_status}",
    )
    _finding(
        findings,
        blockers,
        "docs/reports/handoff-packages/latest/validation_report.json",
        "validation_report_generated_head_exists",
        bool(validation_head),
        f"generated_head={validation_head}",
    )
    _audit_origin_main(
        root=root,
        run_git=run_git,
        findings=findings,
        blockers=blockers,
        warnings=warnings,
        validation_head=validation_head,
        origin_main=origin_main,
        max_origin_lag=max_origin_lag,
    )
    _audit_release_status(
        findings=findings,
        blockers=blockers,
        warnings=warnings,
        release_status=release_status,
        pyproject_version=pyproject_version,
        status_release=status_release,
    )

    return StatusCurrentStateAuditResult(
        root=root.as_posix(),
        package_version=pyproject_version,
        status_version=status_version,
        status_current_verified_release=status_release,
        status_current_verified_main=status_main,
        validation_status=validation_status,
        validation_generated_head=validation_head,
        origin_main=origin_main,
        release_current_state=release_current_state,
        findings=tuple(findings),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def render_status_current_state_audit(result: StatusCurrentStateAuditResult) -> str:
    lines = [
        "STATUS_CURRENT_STATE_AUDIT",
        f"STATUS={result.status}",
        f"PACKAGE_VERSION={result.package_version}",
        f"STATUS_VERSION={result.status_version}",
        f"STATUS_CURRENT_VERIFIED_RELEASE={result.status_current_verified_release}",
        f"STATUS_CURRENT_VERIFIED_MAIN={result.status_current_verified_main}",
        f"VALIDATION_STATUS={result.validation_status}",
        f"VALIDATION_GENERATED_HEAD={result.validation_generated_head}",
        f"ORIGIN_MAIN={result.origin_main}",
        f"RELEASE_CURRENT_STATE={result.release_current_state}",
        f"FINDING_COUNT={len(result.findings)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
        f"WARNING_COUNT={len(result.warnings)}",
    ]
    for item in result.blockers:
        lines.append(f"BLOCKER={item.path}|{item.check}|{item.status}|{item.detail}")
    for item in result.warnings:
        lines.append(f"WARNING={item.path}|{item.check}|{item.status}|{item.detail}")
    return "\n".join(lines) + "\n"


def _run_git(root: Path, args: Sequence[str]) -> GitResult:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return GitResult(completed.returncode, completed.stdout, completed.stderr)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _project_version(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    value = data.get("project", {}).get("version")
    return str(value) if value is not None else None


def _build_release_status(
    root: Path,
    builder: ReleaseStatusBuilder | None,
) -> ReleaseLifecycleStatus | None:
    try:
        return (builder or (lambda project_root: build_release_lifecycle_status(project_root)))(root)
    except Exception:
        return None


def _match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _current_state_block(status_text: str) -> str:
    match = re.search(r"(?ms)^## Current State\s*(.*?)(?=^## |\Z)", status_text)
    return match.group(1).strip() if match else ""


def _status_verified_version_doi(current_block: str) -> tuple[str, int] | None:
    for index, line in enumerate(current_block.splitlines(), start=1):
        match = re.search(r"^Verified Zenodo version DOI:\s*`?([^`.\s]+(?:\.[^`.\s]+)+)`?\.?", line)
        if match:
            return match.group(1).strip(), index
    return None


def _current_changelog_block(changelog_text: str, version: str) -> tuple[str, int]:
    pattern = re.compile(rf"(?ms)^## v{re.escape(version)}\b.*?(?=^## v|\Z)")
    match = pattern.search(changelog_text)
    if not match:
        return "", 0
    start_line = changelog_text[: match.start()].count("\n") + 1
    return match.group(0), start_line


def _pending_doi_lines(block: str, *, start_line: int) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for offset, line in enumerate(block.splitlines()):
        lowered = line.lower()
        if "doi" in lowered and "pending" in lowered:
            lines.append((start_line + offset, line.strip()))
    return lines


def _audit_changelog_current_pending_doi(
    *,
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    root: Path,
    pyproject_version: str | None,
    status_version: str | None,
    status_verified_version_doi: tuple[str, int] | None,
) -> None:
    changelog_path = root / "CHANGELOG.md"
    changelog_text = _read_text(changelog_path)
    if not pyproject_version:
        return
    block, start_line = _current_changelog_block(changelog_text, pyproject_version)
    _finding(
        findings,
        blockers,
        "CHANGELOG.md",
        "changelog_current_version_block_exists",
        True,
        f"version={pyproject_version}; found={bool(block)}",
    )
    if not block:
        return

    pending_lines = _pending_doi_lines(block, start_line=start_line)
    stale_pending = bool(
        pending_lines
        and status_version == pyproject_version
        and status_verified_version_doi is not None
    )
    if stale_pending:
        doi, status_line = status_verified_version_doi
        pending_locations = ", ".join(
            f"CHANGELOG.md:{line_no}:{line_text}" for line_no, line_text in pending_lines
        )
        detail = (
            f"version={pyproject_version}; pending={pending_locations}; "
            f"verified=docs/STATUS.md:{status_line}:Verified Zenodo version DOI {doi}"
        )
    else:
        detail = (
            f"version={pyproject_version}; pending_lines={len(pending_lines)}; "
            f"status_version={status_version}; "
            f"status_verified_doi={status_verified_version_doi[0] if status_verified_version_doi else None}"
        )
    _finding(
        findings,
        blockers,
        "CHANGELOG.md",
        "changelog_stale_pending_doi",
        not stale_pending,
        detail,
    )


_CURRENT_VERIFIED_MAIN_PATTERN = r"^Current verified main:\s*`?([0-9a-f]{7,40})`?"
_CURRENT_VERIFIED_MAIN_HEAD_PATTERN = r"^Current verified main HEAD(?:\s+is)?(?::)?\s*`?([0-9a-f]{7,40})`?"


def _current_verified_main(current_block: str) -> str | None:
    markers = _marker_values(current_block, _CURRENT_VERIFIED_MAIN_PATTERN)
    return markers[0] if markers else None


def _marker_values(text: str, pattern: str) -> list[str]:
    return re.findall(pattern, text, re.MULTILINE)


def _string_or_none(value: object) -> str | None:
    return str(value) if value is not None else None


def _finding(
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    path: str,
    check: str,
    ok: bool,
    detail: str,
) -> None:
    item = StatusCurrentStateFinding(path, check, "PASS" if ok else "BLOCK", detail)
    findings.append(item)
    if not ok:
        blockers.append(item)


def _warning(
    findings: list[StatusCurrentStateFinding],
    warnings: list[StatusCurrentStateFinding],
    path: str,
    check: str,
    detail: str,
) -> None:
    item = StatusCurrentStateFinding(path, check, "WARN", detail)
    findings.append(item)
    warnings.append(item)


def _audit_status_main_marker(
    *,
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    status_text: str,
    current_block: str,
    status_main: str | None,
    validation_head: str | None,
) -> None:
    live_text = status_text.split("## Historical State Snapshots", 1)[0]
    live_markers = _marker_values(live_text, _CURRENT_VERIFIED_MAIN_PATTERN)
    current_block_markers = _marker_values(current_block, _CURRENT_VERIFIED_MAIN_PATTERN)
    live_unique = _unique_values(live_markers)
    current_block_unique = _unique_values(current_block_markers)
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_live_area_current_verified_main_values_consistent",
        len(live_unique) <= 1,
        f"live_values={live_unique}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_current_block_current_verified_main_values_consistent",
        len(current_block_unique) <= 1,
        f"current_block_values={current_block_unique}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_live_area_single_current_verified_main",
        len(live_markers) == 1,
        f"live_marker_count={len(live_markers)}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_current_block_single_current_verified_main",
        len(current_block_markers) == 1,
        f"current_block_marker_count={len(current_block_markers)}",
    )
    live_head_markers = _marker_values(live_text, _CURRENT_VERIFIED_MAIN_HEAD_PATTERN)
    live_head_unique = _unique_values(live_head_markers)
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_md_internal_head_conflict",
        len(live_head_unique) <= 1,
        f"live_head_values={live_head_unique}",
    )
    matches_validation = bool(status_main and validation_head and validation_head.startswith(status_main))
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_current_verified_main_matches_handoff_validation_head",
        matches_validation,
        f"status_main={status_main}, validation_head={validation_head}",
    )


def _audit_status_release_marker(
    *,
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    release_status: ReleaseLifecycleStatus | None,
    pyproject_version: str | None,
    status_release: str | None,
) -> None:
    if release_status is None:
        _finding(
            findings,
            blockers,
            "docs/STATUS.md",
            "status_current_verified_release_matches_pyproject",
            bool(pyproject_version and status_release == pyproject_version),
            f"status_release={status_release}, pyproject={pyproject_version}",
        )
        return
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_current_verified_release_matches_release_status",
        bool(status_release and status_release == release_status.current_verified_version),
        (
            f"status_release={status_release}, "
            f"release_status_current_verified={release_status.current_verified_version}, "
            f"release_state={release_status.current_state}"
        ),
    )


def _unique_values(values: Sequence[str]) -> list[str]:
    return sorted(set(values))


def _origin_main(root: Path, run_git: GitRunner) -> str | None:
    result = run_git(root, ("rev-parse", "--verify", "origin/main"))
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _audit_origin_main(
    *,
    root: Path,
    run_git: GitRunner,
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    warnings: list[StatusCurrentStateFinding],
    validation_head: str | None,
    origin_main: str | None,
    max_origin_lag: int,
) -> None:
    _finding(
        findings,
        blockers,
        "origin/main",
        "origin_main_resolves",
        bool(origin_main),
        f"origin_main={origin_main}",
    )
    if not validation_head or not origin_main:
        return
    ancestor = run_git(root, ("merge-base", "--is-ancestor", validation_head, origin_main))
    _finding(
        findings,
        blockers,
        "origin/main",
        "handoff_validation_head_reachable_from_origin_main",
        ancestor.returncode == 0,
        f"validation_head={validation_head}, origin_main={origin_main}, returncode={ancestor.returncode}",
    )
    if ancestor.returncode != 0:
        return
    lag = run_git(root, ("rev-list", "--count", f"{validation_head}..{origin_main}"))
    if lag.returncode != 0:
        _warning(
            findings,
            warnings,
            "origin/main",
            "origin_lag_not_checked",
            lag.stderr.strip() or "git rev-list failed",
        )
        return
    try:
        lag_count = int(lag.stdout.strip())
    except ValueError:
        _warning(findings, warnings, "origin/main", "origin_lag_not_numeric", f"stdout={lag.stdout.strip()}")
        return
    _finding(
        findings,
        blockers,
        "origin/main",
        "handoff_validation_head_not_too_far_behind_origin_main",
        lag_count <= max_origin_lag,
        f"lag_count={lag_count}, max_origin_lag={max_origin_lag}",
    )


def _audit_release_status(
    *,
    findings: list[StatusCurrentStateFinding],
    blockers: list[StatusCurrentStateFinding],
    warnings: list[StatusCurrentStateFinding],
    release_status: ReleaseLifecycleStatus | None,
    pyproject_version: str | None,
    status_release: str | None,
) -> None:
    if release_status is None:
        _warning(
            findings,
            warnings,
            "release-status",
            "release_status_unavailable",
            "release-status could not be built; release comparison skipped",
        )
        return
    _finding(
        findings,
        blockers,
        "release-status",
        "release_status_current_or_prepared",
        release_status.current_state in {"current_verified", "prepared"} and not release_status.blockers,
        f"current_state={release_status.current_state}, blockers={list(release_status.blockers)}",
    )
    _finding(
        findings,
        blockers,
        "release-status",
        "release_status_version_matches_pyproject",
        bool(pyproject_version and release_status.package_version == pyproject_version),
        f"release_status_package={release_status.package_version}, pyproject={pyproject_version}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "status_release_matches_release_status",
        bool(status_release and status_release == release_status.current_verified_version),
        f"status_release={status_release}, release_status_current_verified={release_status.current_verified_version}",
    )
