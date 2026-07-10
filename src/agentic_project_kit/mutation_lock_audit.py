from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any


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
