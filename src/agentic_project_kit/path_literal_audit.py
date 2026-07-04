from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class PathLiteralPattern:
    name: str
    literal: str


PATH_LITERAL_PATTERNS = (
    PathLiteralPattern("quoted_docs", '"' + 'docs/'),
    PathLiteralPattern("path_docs", 'Path(' + '"' + 'docs'),
    PathLiteralPattern("quoted_tmp", '"' + 'tmp/'),
    PathLiteralPattern("path_tmp", 'Path(' + '"' + 'tmp'),
)


@dataclass(frozen=True)
class PathLiteralModuleCount:
    path: str
    total: int
    patterns: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PathLiteralAuditResult:
    root: str
    patterns: tuple[PathLiteralPattern, ...]
    modules: tuple[PathLiteralModuleCount, ...]

    @property
    def status(self) -> str:
        return "REPORT"

    @property
    def returncode(self) -> int:
        return 0

    @property
    def affected_module_count(self) -> int:
        return len(self.modules)

    @property
    def literal_count(self) -> int:
        return sum(module.total for module in self.modules)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "path_literal_audit",
            "root": self.root,
            "status": self.status,
            "affected_module_count": self.affected_module_count,
            "literal_count": self.literal_count,
            "patterns": [asdict(pattern) for pattern in self.patterns],
            "modules": [module.as_dict() for module in self.modules],
        }


def audit_path_literals(
    root: Path = Path("."),
    *,
    patterns: tuple[PathLiteralPattern, ...] = PATH_LITERAL_PATTERNS,
) -> PathLiteralAuditResult:
    root = root.resolve()
    modules: list[PathLiteralModuleCount] = []
    src_root = root / "src"
    if src_root.exists():
        for path in sorted(src_root.rglob("*.py")):
            if not path.is_file() or path.is_symlink():
                continue
            counts = _count_path_literals(path, patterns)
            total = sum(counts.values())
            if total == 0:
                continue
            modules.append(
                PathLiteralModuleCount(
                    path=path.relative_to(root).as_posix(),
                    total=total,
                    patterns=counts,
                )
            )

    modules.sort(key=lambda module: (-module.total, module.path))
    return PathLiteralAuditResult(
        root=root.as_posix(),
        patterns=patterns,
        modules=tuple(modules),
    )


def render_path_literal_audit(result: PathLiteralAuditResult) -> str:
    lines = [
        "PATH_LITERAL_AUDIT",
        f"STATUS={result.status}",
        f"AFFECTED_MODULES={result.affected_module_count}",
        f"LITERAL_COUNT={result.literal_count}",
    ]
    for module in result.modules:
        pattern_summary = "|".join(
            f"{pattern.name}={module.patterns.get(pattern.name, 0)}"
            for pattern in result.patterns
        )
        lines.append(f"MODULE={module.total}|{module.path}|{pattern_summary}")
    return "\n".join(lines) + "\n"


def render_path_literal_evidence_report(
    result: PathLiteralAuditResult,
    *,
    command: str = "agentic-kit audit-path-literals",
    generated_on: date | None = None,
) -> str:
    generated = generated_on or date.today()
    pattern_headers = [pattern.name for pattern in result.patterns]
    lines = [
        "# Path Literal Audit Evidence",
        "",
        f"Generated: {generated.isoformat()}",
        f"Command: `{command}`",
        "Mode: REPORT-ONLY; this evidence does not gate the standard suite.",
        "",
        f"Affected modules: {result.affected_module_count}",
        f"Literal count: {result.literal_count}",
        "",
        "| module | total | " + " | ".join(pattern_headers) + " |",
        "|---|---:|" + "|".join("---:" for _ in pattern_headers) + "|",
    ]
    for module in result.modules:
        counts = [str(module.patterns.get(name, 0)) for name in pattern_headers]
        lines.append(f"| {module.path} | {module.total} | " + " | ".join(counts) + " |")
    return "\n".join(lines) + "\n"


def _count_path_literals(
    path: Path,
    patterns: tuple[PathLiteralPattern, ...],
) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    return {
        pattern.name: text.count(pattern.literal)
        for pattern in patterns
    }
