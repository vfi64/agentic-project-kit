from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


DEFAULT_CENTRAL_TARGET = "docs/planning/PROJECT_DIRECTION.yaml"
DEFAULT_MANIFESTS = (
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/DOCUMENTATION_COVERAGE.yaml",
    "docs/DOC_REGISTRY_SCOPE.yaml",
)
SCAN_SUFFIXES = {".md", ".py", ".yaml", ".yml"}
SCAN_ROOTS = ("docs", "src", "tests")
EXTRA_SCAN_FILES = ("README.md",)


@dataclass(frozen=True)
class RemovedSourceFinding:
    path: str
    exists: bool
    registered_refs: list[str] = field(default_factory=list)
    source_file_style_refs: list[str] = field(default_factory=list)
    live_refs: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            not self.exists
            and not self.registered_refs
            and not self.source_file_style_refs
            and not self.live_refs
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "exists": self.exists,
            "registered_refs": self.registered_refs,
            "source_file_style_refs": self.source_file_style_refs,
            "live_refs": self.live_refs,
            "ok": self.ok,
        }


@dataclass(frozen=True)
class RemovedSourceAuditResult:
    result_status: str
    central_target: str
    audited_count: int
    findings: list[RemovedSourceFinding]

    @property
    def ok(self) -> bool:
        return self.result_status == "PASS"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "result_status": self.result_status,
            "central_target": self.central_target,
            "audited_count": self.audited_count,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if "docs/reports" in path.as_posix():
                continue
            if path.suffix in SCAN_SUFFIXES:
                files.append(path)
    for extra in EXTRA_SCAN_FILES:
        path = root / extra
        if path.exists() and path.is_file():
            files.append(path)
    return sorted(set(files))


def _line_refs(path: Path, root: Path, needle: str) -> list[str]:
    refs: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return refs
    rel = _rel(path, root)
    for lineno, line in enumerate(lines, start=1):
        if needle in line:
            refs.append(f"{rel}:{lineno}:{line.strip()}")
    return refs


def _extract_removed_source_paths(root: Path, central_target: str) -> list[str]:
    central_path = root / central_target
    if not central_path.exists():
        return []
    text = central_path.read_text(encoding="utf-8")
    candidates = re.findall(r"^\s*path:\s+(docs/[^\s#]+)\s*$", text, flags=re.MULTILINE)
    removed: list[str] = []
    for candidate in candidates:
        pattern = rf"status:\s*removed_source|removed_source:\s*\n(?:.|\n){{0,240}}path:\s+{re.escape(candidate)}"
        window_start = max(0, text.find(candidate) - 260)
        window_end = min(len(text), text.find(candidate) + len(candidate) + 260)
        window = text[window_start:window_end]
        if re.search(pattern, window):
            removed.append(candidate)
    return sorted(set(removed))


def _source_file_style_refs(root: Path, central_target: str, removed_path: str) -> list[str]:
    path = root / central_target
    if not path.exists():
        return []
    refs: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(rf"^\s*-\s+{re.escape(removed_path)}\s*$")
    for lineno, line in enumerate(lines, start=1):
        if pattern.match(line):
            refs.append(f"{central_target}:{lineno}:{line.strip()}")
    return refs


def _manifest_refs(root: Path, removed_path: str, manifests: tuple[str, ...] = DEFAULT_MANIFESTS) -> list[str]:
    refs: list[str] = []
    for manifest in manifests:
        path = root / manifest
        if path.exists():
            refs.extend(_line_refs(path, root, removed_path))
    return refs


def _live_refs(root: Path, central_target: str, removed_path: str) -> list[str]:
    refs: list[str] = []
    for path in _iter_scan_files(root):
        rel = _rel(path, root)
        if rel == central_target:
            continue
        if rel.startswith("docs/reports/"):
            continue
        refs.extend(_line_refs(path, root, removed_path))
    return refs


def build_removed_source_audit(
    root: Path,
    paths: list[str] | None = None,
    central_target: str = DEFAULT_CENTRAL_TARGET,
) -> RemovedSourceAuditResult:
    root = root.resolve()
    audit_paths = sorted(set(paths or _extract_removed_source_paths(root, central_target)))
    findings = [
        RemovedSourceFinding(
            path=removed_path,
            exists=(root / removed_path).exists(),
            registered_refs=_manifest_refs(root, removed_path),
            source_file_style_refs=_source_file_style_refs(root, central_target, removed_path),
            live_refs=_live_refs(root, central_target, removed_path),
        )
        for removed_path in audit_paths
    ]
    status = "PASS" if all(finding.ok for finding in findings) else "FAIL"
    return RemovedSourceAuditResult(
        result_status=status,
        central_target=central_target,
        audited_count=len(findings),
        findings=findings,
    )


def render_removed_source_audit(result: RemovedSourceAuditResult) -> str:
    lines = [
        "REMOVED_SOURCE_AUDIT",
        f"STATUS={result.result_status}",
        f"CENTRAL_TARGET={result.central_target}",
        f"AUDITED={result.audited_count}",
    ]
    for finding in result.findings:
        lines.append(f"- PATH={finding.path} OK={finding.ok}")
        if finding.exists:
            lines.append("  EXISTS=yes")
        for label, refs in (
            ("REGISTERED_REF", finding.registered_refs),
            ("SOURCE_FILES_STYLE_REF", finding.source_file_style_refs),
            ("LIVE_REF", finding.live_refs),
        ):
            for ref in refs:
                lines.append(f"  {label} {ref}")
    return "\n".join(lines) + "\n"
