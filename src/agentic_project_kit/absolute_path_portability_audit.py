from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re


ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+/[^\s`\"')]+"),
    re.compile(r"/home/[A-Za-z0-9._-]+/[^\s`\"')]+"),
    re.compile(r"(?<![\w.-])/tmp/[^\s`\"')]+"),
    re.compile(r"/var/folders/[^\s`\"')]+"),
    re.compile(r"/mnt/data/[^\s`\"')]+"),
)

TEXT_SUFFIXES = {
    ".md",
    ".rst",
    ".txt",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".cff",
    ".sh",
}

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "tmp",
    "dist",
    "build",
}

SKIP_DIR_PREFIXES = (
    ".venv",
)

SKIP_FILENAMES = {
    "Screen-Control_Output.txt",
}

SKIP_PATH_PREFIXES = (
    "docs/reports/",
    ".agentic/transfer/outbox/",
)

SAFE_PATH_PREFIXES = (
    "tests/",
    "docs/reports/",
)

SAFE_PATHS = {
    "README.md",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
}

HISTORICAL_MARKERS = (
    "historical",
    "legacy",
    "obsolete",
    "removed",
    "deprecated",
    "archived",
    "archive",
    "example",
    "fixture",
    "test",
    "log",
    "evidence",
    "sandbox",
)


@dataclass(frozen=True)
class AbsolutePathReference:
    path: str
    line: int
    text: str
    match: str
    classification: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AbsolutePathAuditResult:
    root: str
    references: tuple[AbsolutePathReference, ...]
    blockers: tuple[AbsolutePathReference, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "absolute_path_portability_audit",
            "root": self.root,
            "status": self.status,
            "reference_count": len(self.references),
            "blocker_count": len(self.blockers),
            "references": [item.as_dict() for item in self.references],
            "blockers": [item.as_dict() for item in self.blockers],
        }


def _is_text_file(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES


def _iter_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        relative_parts = path.relative_to(root).parts
        if path.name in SKIP_FILENAMES:
            continue
        if any(part in SKIP_DIR_PARTS for part in relative_parts):
            continue
        if any(part.startswith(prefix) for part in relative_parts for prefix in SKIP_DIR_PREFIXES):
            continue
        if any(relative.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            continue
        if not _is_text_file(path):
            continue
        files.append(path)
    return sorted(files)


def _classify(relative: str, line: str, match: str) -> tuple[str, str]:
    lowered = line.lower()

    if relative == "src/agentic_project_kit/absolute_path_portability_audit.py":
        return "audit_implementation", "absolute path tokens are classifier patterns, not user-facing paths"

    if relative.startswith(SAFE_PATH_PREFIXES):
        return "safe_generated_or_test_context", "test/generated context"

    if relative.startswith("tests/"):
        return "test_fixture", "test fixture"

    if relative.startswith(("src/", "tools/")):
        return "absolute_path_blocker", (
            "source/tool files must not contain user-specific absolute paths; "
            "line-level historical words are not enough to downgrade this"
        )

    if relative in SAFE_PATHS and any(marker in lowered for marker in HISTORICAL_MARKERS):
        return "historical_or_example_context", "stable doc with historical/example marker"

    if any(marker in lowered for marker in HISTORICAL_MARKERS):
        return "historical_or_example_context", "line contains historical/example/evidence marker"

    if match.startswith("/tmp/") or match.startswith("/mnt/data/") or match.startswith("/var/folders/"):
        return "transient_path_reference", "transient local path should not be current repo contract"

    return "absolute_path_blocker", "absolute local path may break portability"


def audit_absolute_path_portability(root: Path = Path(".")) -> AbsolutePathAuditResult:
    root = root.resolve()
    references: list[AbsolutePathReference] = []

    for path in _iter_candidate_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for number, line in enumerate(lines, start=1):
            for pattern in ABSOLUTE_PATH_PATTERNS:
                for match in pattern.finditer(line):
                    matched = match.group(0)
                    classification, reason = _classify(relative, line, matched)
                    references.append(
                        AbsolutePathReference(
                            path=relative,
                            line=number,
                            text=line.strip(),
                            match=matched,
                            classification=classification,
                            reason=reason,
                        )
                    )

    blockers = tuple(
        ref
        for ref in references
        if ref.classification in {"absolute_path_blocker", "transient_path_reference"}
    )
    return AbsolutePathAuditResult(
        root=root.as_posix(),
        references=tuple(references),
        blockers=blockers,
    )


def render_absolute_path_portability_audit(result: AbsolutePathAuditResult) -> str:
    lines = [
        "ABSOLUTE_PATH_PORTABILITY_AUDIT",
        f"STATUS={result.status}",
        f"REFERENCE_COUNT={len(result.references)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]

    for ref in result.blockers:
        lines.append(
            "BLOCKER="
            f"{ref.classification}|{ref.path}:{ref.line}|{ref.match}|{ref.text}"
        )

    for ref in result.references:
        lines.append(
            "REFERENCE="
            f"{ref.classification}|{ref.path}:{ref.line}|{ref.match}|{ref.text}"
        )

    return "\n".join(lines) + "\n"
