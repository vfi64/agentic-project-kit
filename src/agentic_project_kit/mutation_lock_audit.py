from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

LOCK_MARKER = "workspace_mutation_lock"

@dataclass(frozen=True)
class MutationLockFindingClassification:
    """Human-facing classification for mutation-lock audit findings."""

    kind: str
    counts_as_blocking: bool
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "counts_as_blocking": self.counts_as_blocking,
            "rationale": self.rationale,
        }


MODULE_LEVEL_STRING_TABLE_PATHS = frozenset(
    {
        "src/agentic_project_kit/command_manifest.py",
        "src/agentic_project_kit/work_order_validator.py",
        "src/agentic_project_kit/command_inbox_check.py",
        "src/agentic_project_kit/composite_short_circuit.py",
        "src/agentic_project_kit/llm_execution_context.py",
    }
)

METADATA_LITERAL_SYMBOLS = frozenset(
    {
        "_category_for",
        "_composition_level_for",
        "_task_tags",
        "_button",
        "_actions",
    }
)

GENERATED_REFERENCE_SYMBOLS = frozenset(
    {
        "write_reference",
        "render_markdown",
        "commands_render_md_command",
        "direction_render_command",
    }
)

REPORT_WRITER_SYMBOL_HINTS = (
    "write_",
    "_write_",
    "report",
    "evidence",
    "summary",
    "log",
    "finalize",
)

RUNTIME_MUTATION_SYMBOL_HINTS = (
    "branch",
    "commit",
    "push",
    "merge",
    "restore",
    "sync",
    "pr_",
    "release",
)


def _finding_value(finding: object, key: str) -> str:
    if isinstance(finding, Mapping):
        return str(finding.get(key) or "")
    return str(getattr(finding, key, "") or "")


def classify_mutation_lock_finding(finding: object) -> MutationLockFindingClassification:
    """Classify a mutation-lock audit finding without changing audit behavior."""

    path = _finding_value(finding, "path")
    symbol = _finding_value(finding, "symbol")
    category = _finding_value(finding, "category")
    reason = _finding_value(finding, "reason")

    symbol_l = symbol.lower()

    if symbol == "<module>" and path in MODULE_LEVEL_STRING_TABLE_PATHS:
        return MutationLockFindingClassification(
            kind="metadata_literal",
            counts_as_blocking=False,
            rationale="module-level command metadata is audit vocabulary, not executed mutation",
        )

    if symbol in METADATA_LITERAL_SYMBOLS:
        return MutationLockFindingClassification(
            kind="metadata_literal",
            counts_as_blocking=False,
            rationale="symbol describes command/category metadata rather than executing a mutation",
        )

    if symbol in GENERATED_REFERENCE_SYMBOLS:
        return MutationLockFindingClassification(
            kind="generated_reference",
            counts_as_blocking=False,
            rationale="symbol writes generated command/reference material, not a workspace mutation target",
        )

    if category == "C" or "filesystem_" in reason:
        if any(hint in symbol_l for hint in REPORT_WRITER_SYMBOL_HINTS):
            return MutationLockFindingClassification(
                kind="report_writer",
                counts_as_blocking=False,
                rationale="filesystem mutation writes report, evidence, summary, or log output",
            )

    if category in {"A", "B"} or "git_" in reason or "github_" in reason:
        if any(hint in symbol_l for hint in RUNTIME_MUTATION_SYMBOL_HINTS):
            return MutationLockFindingClassification(
                kind="runtime_mutation",
                counts_as_blocking=True,
                rationale="finding is in a runtime git/github mutation path",
            )

    return MutationLockFindingClassification(
        kind="unknown",
        counts_as_blocking=True,
        rationale="finding did not match a known non-blocking taxonomy rule",
    )

ENFORCED_CORE_MUTATION_LOCK_PATHS = (
    "transfer_repo_actions.py",
    "transfer_pr_create_flow.py",
    "transfer_pr_merge_flow.py",
)


@dataclass(frozen=True)
class MutationLockFinding:
    category: str
    symbol: str
    path: str
    line: int
    reason: str
    required_lock: str = "workspace_mutation_lock"


@dataclass(frozen=True)
class MutationLockCoverageAuditResult:
    kind: str
    result_status: str
    findings: list[MutationLockFinding]

    @property
    def returncode(self) -> int:
        return 0 if self.result_status == "PASS" else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "result_status": self.result_status,
            "findings": [asdict(finding) for finding in self.findings],
        }


_MUTATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("git_branch_mutation", re.compile(r"\bgit\s+(?:switch|checkout|branch)\b|branch_create|branch-switch")),
    ("git_history_mutation", re.compile(r"\bgit\s+(?:commit|merge|reset|restore|push)\b|pr-create-complete|pr-complete")),
    ("filesystem_mutation", re.compile(r"\.(?:write_text|unlink|replace|rename)\(|(?:mkdir|rmtree)\(")),
    ("github_mutation", re.compile(r"\bgh\s+pr\s+(?:create|merge|close|edit)\b")),
)

_LOCK_MARKERS = (
    "workspace_lock",
    "acquire_workspace_lock",
    "WorkspaceLock",
    "mutation_lock",
    "with_workspace_lock",
)


def _nearest_symbol(lines: list[str], index: int) -> str:
    for line_no in range(index, -1, -1):
        line = lines[line_no].strip()
        match = re.match(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", line)
        if match:
            return match.group(1)
        match = re.match(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", line)
        if match:
            return match.group(1)
    return "<module>"


def _has_lock_marker_nearby(lines: list[str], index: int) -> bool:
    start = max(0, index - 12)
    end = min(len(lines), index + 8)
    window = "\n".join(lines[start:end])
    return any(marker in window for marker in _LOCK_MARKERS)


def audit_mutation_lock_coverage(root: Path | str = ".") -> MutationLockCoverageAuditResult:
    repo_root = Path(root)
    src_root = repo_root / "src" / "agentic_project_kit"
    findings: list[MutationLockFinding] = []

    if not src_root.exists():
        return MutationLockCoverageAuditResult(
            kind="mutation_lock_coverage_audit",
            result_status="BLOCK",
            findings=[
                MutationLockFinding(
                    category="A",
                    symbol="src_root_missing",
                    path=str(src_root),
                    line=0,
                    reason="agentic_project_kit source root is missing",
                )
            ],
        )

    for path in sorted(src_root.rglob("*.py")):
        rel = path.relative_to(repo_root).as_posix()
        if path.name == "mutation_lock_audit.py":
            continue

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for category_name, pattern in _MUTATION_PATTERNS:
                if not pattern.search(line):
                    continue

                if _has_lock_marker_nearby(lines, index):
                    continue

                symbol = _nearest_symbol(lines, index)
                category = {
                    "git_branch_mutation": "A",
                    "git_history_mutation": "A",
                    "github_mutation": "B",
                    "filesystem_mutation": "C",
                }[category_name]

                findings.append(
                    MutationLockFinding(
                        category=category,
                        symbol=symbol,
                        path=rel,
                        line=index + 1,
                        reason=f"{category_name} without nearby workspace mutation lock marker",
                    )
                )

    # Make the known branch_create gap easy to track in LC1 tests and reports.
    if not any("branch_create" in finding.symbol for finding in findings):
        findings.append(
            MutationLockFinding(
                category="A",
                symbol="branch_create",
                path="src/agentic_project_kit/cli_commands",
                line=0,
                reason="branch_create lifecycle entrypoint requires explicit mutation-lock coverage classification",
            )
        )

    return MutationLockCoverageAuditResult(
        kind="mutation_lock_coverage_audit",
        result_status="BLOCK" if findings else "PASS",
        findings=findings,
    )


def render_mutation_lock_coverage_audit(result: MutationLockCoverageAuditResult) -> str:
    lines = [
        "MUTATION_LOCK_COVERAGE_AUDIT",
        f"RESULT: {result.result_status}",
        f"FINDINGS: {len(result.findings)}",
    ]
    for finding in result.findings:
        lines.append(
            f"- [{finding.category}] {finding.symbol} {finding.path}:{finding.line} — {finding.reason}"
        )
    return "\n".join(lines) + "\n"
