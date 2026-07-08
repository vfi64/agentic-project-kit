from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


LEGACY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\./ns\b"),
    re.compile(r"\bns-menu\b"),
    re.compile(r"\bns_release_[A-Za-z0-9_]*"),
    re.compile(r"\btools/ns_[A-Za-z0-9_./-]*"),
    re.compile(r"\bNS RELEASE\b"),
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
}

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "tmp",
}

SKIP_PATH_PREFIXES = (
    "docs/reports/",
    ".agentic/transfer/outbox/",
)

CURRENT_INSTRUCTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(run|execute|use|start|call|invoke|rerun|copy|paste|command|befehl|ausführen|starte)\b", re.I),
    re.compile(r"^\s*(?:[-*]\s*)?(?:cd\s+\S+\s*&&\s*)?\./ns\b", re.I),
    re.compile(r"^\s*(?:[-*]\s*)?tools/ns_", re.I),
)

HISTORICAL_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(historical|legacy|obsolete|removed|deprecated|archiv|archived|historisch|veraltet|entfernt)\b", re.I),
    re.compile(r"\b(before|formerly|previously|früher|ehemalig)\b", re.I),
)

SAFE_CONTEXT_PATH_PARTS = (
    "tests",
    "docs/reports",
    "docs/releases",
    "docs/archive",
    "CHANGELOG.md",
)


@dataclass(frozen=True)
class LegacyReference:
    path: str
    line: int
    text: str
    classification: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line": self.line,
            "text": self.text,
            "classification": self.classification,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class NsLegacyReferenceAuditResult:
    status: str
    returncode: int
    references: tuple[LegacyReference, ...]
    blockers: tuple[LegacyReference, ...]

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "returncode": self.returncode,
            "references": [reference.as_dict() for reference in self.references],
            "blockers": [reference.as_dict() for reference in self.blockers],
            "ok": self.ok,
        }


def _is_text_file(path: Path) -> bool:
    if path.suffix in TEXT_SUFFIXES:
        return True
    if path.name in {"CHANGELOG", "README", "LICENSE"}:
        return True
    return False


def iter_candidate_files(project_root: Path) -> Iterable[Path]:
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(project_root).as_posix()
        relative_parts = path.relative_to(project_root).parts
        if any(part in SKIP_DIR_PARTS for part in relative_parts):
            continue
        if any(relative.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            continue
        if not _is_text_file(path):
            continue
        yield path


def _has_legacy_reference(line: str) -> bool:
    return any(pattern.search(line) for pattern in LEGACY_PATTERNS)


def _safe_context_by_path(relative: str) -> bool:
    return relative.startswith(SAFE_CONTEXT_PATH_PARTS) or any(
        part and relative.startswith(part + "/") for part in SAFE_CONTEXT_PATH_PARTS
    )


def _legacy_documentation_context(relative_path: str) -> bool:
    return (
        relative_path.startswith("docs/workflow/")
        or relative_path.startswith("docs/governance/")
        or relative_path.startswith("docs/strategy/")
        or relative_path.startswith("docs/architecture/")
        or relative_path.startswith("docs/planning/")
        or relative_path == "docs/DOCUMENTATION_COVERAGE.yaml"
        or relative_path == "docs/TEST_GATES.md"
        or relative_path == "docs/WORKFLOW_OUTPUT_CYCLE.md"
    )


def _compatibility_implementation_context(relative_path: str) -> bool:
    return relative_path in {
        "src/agentic_project_kit/ns_legacy_reference_audit.py",
        "src/agentic_project_kit/planning_docs_consolidation_audit.py",
        "src/agentic_project_kit/release_gate_core.py",
        "src/agentic_project_kit/release_verify_core.py",
        "src/agentic_project_kit/removed_ns_commands.py",
        "src/agentic_project_kit/work_order_validator.py",
        "src/agentic_project_kit/gui_dry_run.py",
        "src/agentic_project_kit/chat_bootloader.py",
        "src/agentic_project_kit/doc_currency_audit.py",
        "src/agentic_project_kit/entrypoint_slice_runner.py",
        "src/agentic_project_kit/handoff_prompt.py",
        "src/agentic_project_kit/release_prepare.py",
        "src/agentic_project_kit/run_summary_renderer.py",
        "src/agentic_project_kit/terminal_block_guard.py",
        "tools/NEXT_TRANSFER_TASK.py",
    }


def classify_legacy_reference(relative_path: str, line: str) -> tuple[str, str]:
    stripped = line.strip()
    if _compatibility_implementation_context(relative_path):
        return "compatibility_implementation", "legacy tokens are implementation/classifier compatibility patterns"
    if relative_path.startswith("tests/"):
        return "test_fixture", "test fixture/reference"
    if _legacy_documentation_context(relative_path):
        return "legacy_documentation_context", (
            "planning/workflow/governance documentation; use follow-up documentation cleanup "
            "rather than treating as current supported command surface"
        )
    if any(pattern.search(stripped) for pattern in HISTORICAL_MARKERS):
        return "historical", "line contains explicit historical/legacy marker"
    if relative_path.startswith("docs/reports/"):
        return "generated_report_or_evidence", "report/evidence context"
    if relative_path.startswith("docs/releases/") or relative_path == "CHANGELOG.md":
        return "release_history", "release history context"
    if _safe_context_by_path(relative_path) and not any(
        pattern.search(stripped) for pattern in CURRENT_INSTRUCTION_PATTERNS
    ):
        return "historical", "safe documentation context without imperative wording"
    if any(pattern.search(stripped) for pattern in CURRENT_INSTRUCTION_PATTERNS):
        return "current_instruction_blocker", "looks like a current instruction or executable route"
    return "needs_review", "legacy reference is not explicitly historical or a test fixture"


def audit_ns_legacy_references(project_root: Path | str = ".") -> NsLegacyReferenceAuditResult:
    root = Path(project_root).resolve()
    references: list[LegacyReference] = []

    for path in iter_candidate_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if not _has_legacy_reference(line):
                continue
            classification, reason = classify_legacy_reference(relative, line)
            references.append(
                LegacyReference(
                    path=relative,
                    line=index,
                    text=line.strip(),
                    classification=classification,
                    reason=reason,
                )
            )

    blockers = tuple(
        reference
        for reference in references
        if reference.classification in {"current_instruction_blocker", "needs_review"}
    )
    return NsLegacyReferenceAuditResult(
        status="PASS" if not blockers else "BLOCK",
        returncode=0 if not blockers else 1,
        references=tuple(references),
        blockers=blockers,
    )


def render_ns_legacy_reference_audit(result: NsLegacyReferenceAuditResult) -> str:
    lines = [
        "NS_LEGACY_REFERENCE_AUDIT",
        f"STATUS={result.status}",
        f"RETURNCODE={result.returncode}",
        f"REFERENCE_COUNT={len(result.references)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for reference in result.references:
        lines.append(
            "REFERENCE="
            f"{reference.classification}|{reference.path}:{reference.line}|{reference.text}"
        )
    for blocker in result.blockers:
        lines.append(f"BLOCKER={blocker.path}:{blocker.line}|{blocker.reason}|{blocker.text}")
    lines.append("FINAL_SIGNAL=d" if result.ok else "FINAL_SIGNAL=f")
    return "\n".join(lines) + "\n"


def main() -> int:
    result = audit_ns_legacy_references(Path("."))
    print(render_ns_legacy_reference_audit(result), end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
