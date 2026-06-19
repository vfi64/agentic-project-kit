from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
import subprocess

Runner = Callable[[Sequence[str], Path], tuple[int, str]]

PROTECTED_PATH_MARKERS: tuple[str, ...] = (
    "docs/handoff/",
    "docs/STATUS.md",
    "docs/governance/",
    "docs/planning/",
    "docs/reference/",
    ".github/workflows/",
    ".agentic/",
    "CITATION.cff",
    "CHANGELOG.md",
    "pyproject.toml",
)


@dataclass(frozen=True)
class PatchPreflightFinding:
    severity: str
    code: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PatchPreflightReport:
    root: str
    label: str
    changed_files: tuple[str, ...]
    added_lines: int
    deleted_lines: int
    protected_files: tuple[str, ...]
    findings: tuple[PatchPreflightFinding, ...]
    strict: bool

    @property
    def ok(self) -> bool:
        if self.strict:
            return not any(finding.severity == "BLOCK" for finding in self.findings)
        return True

    @property
    def status(self) -> str:
        if not self.ok:
            return "FAIL"
        if self.findings:
            return "WARN"
        return "PASS"

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "patch_preflight_report",
            "root": self.root,
            "label": self.label,
            "status": self.status,
            "strict": self.strict,
            "changed_file_count": len(self.changed_files),
            "added_lines": self.added_lines,
            "deleted_lines": self.deleted_lines,
            "protected_files": list(self.protected_files),
            "changed_files": list(self.changed_files),
            "findings": [finding.as_dict() for finding in self.findings],
        }


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


def _git_numstat(root: Path, base_ref: str, runner: Runner) -> tuple[int, str]:
    return runner(("git", "diff", "--numstat", base_ref, "--"), root)


def _git_status(root: Path, runner: Runner) -> tuple[int, str]:
    return runner(("git", "status", "--porcelain=v1", "--untracked-files=all"), root)


def _parse_numstat(output: str) -> tuple[tuple[str, ...], int, int]:
    changed: list[str] = []
    added = 0
    deleted = 0
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_s, del_s, path = parts[0], parts[1], parts[-1]
        if add_s.isdigit():
            added += int(add_s)
        if del_s.isdigit():
            deleted += int(del_s)
        changed.append(path)
    return tuple(changed), added, deleted


def _parse_status_paths(output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return tuple(paths)


def _is_protected(path: str) -> bool:
    return any(path == marker or path.startswith(marker) for marker in PROTECTED_PATH_MARKERS)


def build_patch_preflight_report(
    root: Path = Path("."),
    *,
    label: str = "patch",
    base_ref: str = "HEAD",
    max_files: int = 6,
    max_diff_lines: int = 400,
    strict: bool = False,
    runner: Runner | None = None,
) -> PatchPreflightReport:
    root = root.resolve()
    run = runner or _default_runner

    findings: list[PatchPreflightFinding] = []
    numstat_rc, numstat_out = _git_numstat(root, base_ref, run)
    if numstat_rc != 0:
        findings.append(PatchPreflightFinding("BLOCK", "git_diff_failed", numstat_out.strip()[:500]))
        changed: tuple[str, ...] = ()
        added = 0
        deleted = 0
    else:
        changed, added, deleted = _parse_numstat(numstat_out)

    status_rc, status_out = _git_status(root, run)
    if status_rc == 0:
        for path in _parse_status_paths(status_out):
            if path not in changed:
                changed = (*changed, path)
    else:
        findings.append(PatchPreflightFinding("WARN", "git_status_failed", status_out.strip()[:500]))

    protected = tuple(path for path in changed if _is_protected(path))
    diff_lines = added + deleted

    if len(changed) > max_files:
        findings.append(
            PatchPreflightFinding(
                "BLOCK" if strict else "WARN",
                "changed_file_count",
                f"{len(changed)} files exceed limit {max_files}",
            )
        )
    if diff_lines > max_diff_lines:
        findings.append(
            PatchPreflightFinding(
                "BLOCK" if strict else "WARN",
                "diff_size",
                f"{diff_lines} changed lines exceed limit {max_diff_lines}",
            )
        )
    if protected:
        findings.append(
            PatchPreflightFinding(
                "WARN",
                "protected_paths_touched",
                ", ".join(protected[:20]),
            )
        )

    return PatchPreflightReport(
        root=root.as_posix(),
        label=label,
        changed_files=tuple(sorted(changed)),
        added_lines=added,
        deleted_lines=deleted,
        protected_files=tuple(sorted(protected)),
        findings=tuple(findings),
        strict=strict,
    )


def render_patch_preflight_report(report: PatchPreflightReport) -> str:
    lines = [
        "PATCH_PREFLIGHT",
        f"STATUS={report.status}",
        f"LABEL={report.label}",
        f"STRICT={str(report.strict).lower()}",
        f"CHANGED_FILE_COUNT={len(report.changed_files)}",
        f"ADDED_LINES={report.added_lines}",
        f"DELETED_LINES={report.deleted_lines}",
        f"PROTECTED_FILE_COUNT={len(report.protected_files)}",
    ]
    for finding in report.findings:
        lines.append(f"FINDING={finding.severity}|{finding.code}|{finding.detail}")
    for path in report.protected_files:
        lines.append(f"PROTECTED={path}")
    return "\n".join(lines) + "\n"
