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

CORE_RUNTIME_MUTATOR_SYMBOLS = frozenset(
    {
        "admin_refresh_pr",
        "_admin_refresh_pr_unlocked",
        "branch_create",
        "branch_delete",
        "branch_switch",
        "commit_paths",
        "_commit_paths_unlocked",
        "pr_create",
        "_pr_create_unlocked",
        "pr_merge_safe",
        "_pr_merge_safe_unlocked",
        "pull_current",
        "push_current",
        "_push_current_unlocked",
    }
)


def _finding_value(finding: object, key: str) -> str:
    if isinstance(finding, Mapping):
        return str(finding.get(key) or "")
    return str(getattr(finding, key, "") or "")


def _is_enforced_core_runtime_path(path: str) -> bool:
    return path == "src/agentic_project_kit/transfer_repo_actions.py"


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
        return MutationLockFindingClassification(
            kind="filesystem_side_effect",
            counts_as_blocking=False,
            rationale="filesystem side-effect remains visible for review; LC3 hard blocking is limited to runtime git/github mutators",
        )

    if category in {"A", "B"} or "git_" in reason or "github_" in reason:
        if _is_enforced_core_runtime_path(path) and symbol in CORE_RUNTIME_MUTATOR_SYMBOLS:
            return MutationLockFindingClassification(
                kind="runtime_mutation",
                counts_as_blocking=True,
                rationale="finding is in a runtime git/github mutation path",
            )
        if any(hint in symbol_l for hint in RUNTIME_MUTATION_SYMBOL_HINTS):
            return MutationLockFindingClassification(
                kind="delegated_runtime_reference",
                counts_as_blocking=False,
                rationale="runtime-like command text is outside the LC3 enforced core mutator body or delegates to locked core mutators",
            )

    return MutationLockFindingClassification(
        kind="review_visible_reference",
        counts_as_blocking=False,
        rationale="finding remains visible for review but does not match an enforced LC3 runtime mutator",
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
    findings: list[MutationLockFinding]

    @property
    def blocking_findings(self) -> list[MutationLockFinding]:
        return [
            finding
            for finding in self.findings
            if classify_mutation_lock_finding(finding).counts_as_blocking
        ]

    @property
    def non_blocking_findings(self) -> list[MutationLockFinding]:
        return [
            finding
            for finding in self.findings
            if not classify_mutation_lock_finding(finding).counts_as_blocking
        ]

    @property
    def result_status(self) -> str:
        return "BLOCK" if self.blocking_findings else "PASS"

    @property
    def returncode(self) -> int:
        return 0 if self.result_status == "PASS" else 1

    def to_dict(self) -> dict[str, Any]:
        findings = [_finding_to_dict(finding) for finding in self.findings]
        blocking_findings = [
            finding
            for finding in findings
            if finding["classification"]["counts_as_blocking"]
        ]
        non_blocking_findings = [
            finding
            for finding in findings
            if not finding["classification"]["counts_as_blocking"]
        ]
        return {
            "kind": self.kind,
            "result_status": self.result_status,
            "finding_count": len(findings),
            "blocking_finding_count": len(blocking_findings),
            "non_blocking_finding_count": len(non_blocking_findings),
            "classification_summary": _classification_summary(self.findings),
            "findings": findings,
            "blocking_findings": blocking_findings,
            "non_blocking_findings": non_blocking_findings,
        }


def _finding_to_dict(finding: MutationLockFinding) -> dict[str, Any]:
    classification = classify_mutation_lock_finding(finding)
    data = asdict(finding)
    data["classification"] = classification.to_dict()
    return data


def _classification_summary(findings: list[MutationLockFinding]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for finding in findings:
        classification = classify_mutation_lock_finding(finding)
        entry = summary.setdefault(
            classification.kind,
            {
                "count": 0,
                "counts_as_blocking": classification.counts_as_blocking,
            },
        )
        entry["count"] = int(entry["count"]) + 1
    return dict(sorted(summary.items()))


_MUTATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("git_branch_mutation", re.compile(r"\bgit\s+(?:switch|checkout|branch)\b|[\"']git[\"']\s*,\s*[\"'](?:switch|checkout|branch)[\"']|branch_create|branch-switch")),
    ("git_history_mutation", re.compile(r"\bgit\s+(?:commit|merge|reset|restore|push)\b|[\"']git[\"']\s*,\s*[\"'](?:commit|merge|reset|restore|push)[\"']|pr-create-complete|pr-complete")),
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


def _function_body(lines: list[str], symbol: str) -> str:
    start: int | None = None
    for line_no, line in enumerate(lines):
        if re.match(rf"def\s+{re.escape(symbol)}\(", line):
            start = line_no
            break
    if start is None:
        return ""
    end = len(lines)
    for line_no in range(start + 1, len(lines)):
        if re.match(r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\(", lines[line_no]):
            end = line_no
            break
    return "\n".join(lines[start:end])


def _symbol_has_lock_marker(lines: list[str], symbol: str) -> bool:
    body = _function_body(lines, symbol)
    if any(marker in body for marker in _LOCK_MARKERS):
        return True
    if symbol.startswith("_") and symbol.endswith("_unlocked"):
        wrapper_symbol = symbol.removeprefix("_").removesuffix("_unlocked")
        wrapper_body = _function_body(lines, wrapper_symbol)
        return any(marker in wrapper_body for marker in _LOCK_MARKERS)
    return False


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
                if _symbol_has_lock_marker(lines, symbol):
                    continue
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

    return MutationLockCoverageAuditResult(
        kind="mutation_lock_coverage_audit",
        findings=findings,
    )


def render_mutation_lock_coverage_audit(result: MutationLockCoverageAuditResult) -> str:
    lines = [
        "MUTATION_LOCK_COVERAGE_AUDIT",
        f"RESULT: {result.result_status}",
        f"FINDINGS: {len(result.findings)}",
        f"BLOCKING_FINDINGS: {len(result.blocking_findings)}",
        f"NON_BLOCKING_FINDINGS: {len(result.non_blocking_findings)}",
    ]
    if result.findings:
        lines.append("CLASSIFICATION_SUMMARY:")
        for kind, summary in _classification_summary(result.findings).items():
            disposition = "BLOCK" if summary["counts_as_blocking"] else "non-blocking"
            lines.append(f"- {kind}: {summary['count']} ({disposition})")

    if result.blocking_findings:
        lines.append("BLOCKING:")
    for finding in result.blocking_findings:
        classification = classify_mutation_lock_finding(finding)
        lines.append(
            f"- [{finding.category}] {finding.symbol} {finding.path}:{finding.line} "
            f"— classification={classification.kind} disposition=BLOCK "
            f"— {finding.reason} — {classification.rationale}"
        )

    if result.non_blocking_findings:
        lines.append("NON_BLOCKING:")
    for finding in result.non_blocking_findings:
        classification = classify_mutation_lock_finding(finding)
        lines.append(
            f"- [{finding.category}] {finding.symbol} {finding.path}:{finding.line} "
            f"— classification={classification.kind} disposition=non-blocking "
            f"— {finding.reason} — {classification.rationale}"
        )
    return "\n".join(lines) + "\n"
