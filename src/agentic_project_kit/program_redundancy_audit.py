from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
import ast
import re


SOURCE_ROOTS = (
    "src/agentic_project_kit",
    "tools",
)

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "tmp",
    "dist",
    "build",
}

TEXT_SUFFIXES = {".py"}

AUDIT_IMPLEMENTATION_PATHS = {
    "src/agentic_project_kit/program_redundancy_audit.py",
    "src/agentic_project_kit/work_order_validator.py",
}

ALLOWED_REPEATED_FUNCTION_NAMES = {
    # Small standalone scripts intentionally keep these local helpers instead of
    # coupling old workflow tools to a shared runtime module.
    "current_branch",
    "run",
}


RISK_PATTERNS = (
    ("shell_true", re.compile(r"\bshell\s*=\s*True\b"), "subprocess shell=True should be justified or avoided"),
    ("os_system", re.compile(r"\bos\.system\s*\("), "os.system should be replaced by subprocess/wrapper logic"),
    ("eval_exec", re.compile(r"\b(eval|exec)\s*\("), "eval/exec requires strong justification"),
    ("bare_except", re.compile(r"^\s*except\s*:\s*$"), "bare except hides failures"),
    ("broad_except_exception", re.compile(r"^\s*except\s+Exception\b"), "broad Exception handler should preserve evidence"),
    ("pass_in_exception", re.compile(r"^\s*pass\s*(#.*)?$"), "pass directly inside exception handling may hide failure"),
    ("todo_fixme", re.compile(r"\b(TODO|FIXME|XXX)\b"), "TODO/FIXME marker in production source needs triage"),
)


@dataclass(frozen=True)
class ProgramFinding:
    path: str
    line: int
    kind: str
    severity: str
    text: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProgramRedundancyAuditResult:
    root: str
    findings: tuple[ProgramFinding, ...]
    blockers: tuple[ProgramFinding, ...]

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
            "kind": "program_redundancy_audit",
            "root": self.root,
            "status": self.status,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [item.as_dict() for item in self.findings],
            "blockers": [item.as_dict() for item in self.blockers],
        }


def _iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for source_root in SOURCE_ROOTS:
        base = root / source_root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not path.is_file():
                continue
            parts = path.relative_to(root).parts
            if any(part in SKIP_DIR_PARTS for part in parts):
                continue
            if path.suffix not in TEXT_SUFFIXES:
                continue
            files.append(path)
    return sorted(files)


def _line_findings(root: Path, path: Path) -> list[ProgramFinding]:
    relative = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    findings: list[ProgramFinding] = []

    for index, line in enumerate(lines, start=1):
        for kind, pattern, reason in RISK_PATTERNS:
            if pattern.search(line):
                severity = "review"
                if relative in AUDIT_IMPLEMENTATION_PATHS:
                    severity = "review"
                    reason = "risk token appears in an audit/validator implementation pattern"
                elif kind in {"shell_true", "os_system", "eval_exec", "bare_except"}:
                    severity = "blocker"
                elif kind == "pass_in_exception":
                    window = "\n".join(lines[max(0, index - 4):index])
                    if "except" in window:
                        severity = "blocker"
                    else:
                        continue
                elif kind == "broad_except_exception":
                    severity = "review"
                findings.append(
                    ProgramFinding(
                        path=relative,
                        line=index,
                        kind=kind,
                        severity=severity,
                        text=line.strip(),
                        reason=reason,
                    )
                )
    return findings


def _duplicate_function_findings(root: Path, files: list[Path]) -> list[ProgramFinding]:
    names: list[tuple[str, str, int]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.append((node.name, relative, node.lineno))

    counts = Counter(name for name, _, _ in names)
    findings: list[ProgramFinding] = []
    for name, relative, line in names:
        if counts[name] < 4:
            continue
        if name.startswith("_") or name in {"main", "as_dict", "returncode", "status"}:
            continue
        if name in ALLOWED_REPEATED_FUNCTION_NAMES:
            continue
        findings.append(
            ProgramFinding(
                path=relative,
                line=line,
                kind="repeated_function_name",
                severity="review",
                text=name,
                reason=f"function name appears {counts[name]} times across source; check for duplicated logic",
            )
        )
    return findings


def _duplicate_command_findings(root: Path, files: list[Path]) -> list[ProgramFinding]:
    command_pattern = re.compile(r'(?:(\w+)\.)?command\(["\']([^"\']+)["\']\)')
    occurrences: list[tuple[str, str, str, int, str]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            match = command_pattern.search(line)
            if match:
                app_name = match.group(1) or "app"
                command_name = match.group(2)
                occurrences.append((app_name, command_name, relative, index, line.strip()))

    counts = Counter((app_name, command_name, relative) for app_name, command_name, relative, _, _ in occurrences)
    findings: list[ProgramFinding] = []
    for app_name, command_name, relative, line, text in occurrences:
        count = counts[(app_name, command_name, relative)]
        if count <= 1:
            continue
        findings.append(
            ProgramFinding(
                path=relative,
                line=line,
                kind="duplicate_cli_command_name",
                severity="blocker",
                text=text,
                reason=(
                    f"CLI command name {command_name!r} is registered {count} times "
                    f"on {app_name!r} in {relative}"
                ),
            )
        )
    return findings


def audit_program_redundancy(root: Path = Path(".")) -> ProgramRedundancyAuditResult:
    root = root.resolve()
    files = _iter_source_files(root)

    findings: list[ProgramFinding] = []
    for path in files:
        findings.extend(_line_findings(root, path))
    findings.extend(_duplicate_function_findings(root, files))
    findings.extend(_duplicate_command_findings(root, files))

    blockers = tuple(item for item in findings if item.severity == "blocker")
    return ProgramRedundancyAuditResult(
        root=root.as_posix(),
        findings=tuple(findings),
        blockers=blockers,
    )


def render_program_redundancy_audit(result: ProgramRedundancyAuditResult) -> str:
    lines = [
        "PROGRAM_REDUNDANCY_AUDIT",
        f"STATUS={result.status}",
        f"FINDING_COUNT={len(result.findings)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for item in result.blockers:
        lines.append(
            f"BLOCKER={item.kind}|{item.path}:{item.line}|{item.text}|{item.reason}"
        )
    for item in result.findings:
        lines.append(
            f"FINDING={item.severity}|{item.kind}|{item.path}:{item.line}|{item.text}|{item.reason}"
        )
    return "\n".join(lines) + "\n"
