from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Literal


@dataclass(frozen=True)
class DocMeshDocument:
    path: str
    category: str
    required: bool = True
    historical: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "category": self.category,
            "required": self.required,
            "historical": self.historical,
        }


@dataclass(frozen=True)
class DocMeshFinding:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True)
class DocMeshReport:
    documents: tuple[DocMeshDocument, ...]
    findings: tuple[DocMeshFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "documents": [document.to_dict() for document in self.documents],
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class DocMeshRepair:
    code: str
    path: str
    action: str
    safe: bool
    mode: Literal["automatic", "manual"]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "action": self.action,
            "safe": self.safe,
            "mode": self.mode,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DocMeshRepairPlan:
    ok: bool
    repairs: tuple[DocMeshRepair, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "repairs": [repair.to_dict() for repair in self.repairs],
        }


@dataclass(frozen=True)
class DocMeshRepairAction:
    path: str
    action: str
    changed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "action": self.action,
            "changed": self.changed,
            "message": self.message,
        }


@dataclass(frozen=True)
class DocMeshRepairResult:
    changed: bool
    actions: tuple[DocMeshRepairAction, ...]
    skipped: tuple[DocMeshRepair, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": self.changed,
            "actions": [action.to_dict() for action in self.actions],
            "skipped": [repair.to_dict() for repair in self.skipped],
        }


DOC_MESH_DOCUMENTS: tuple[DocMeshDocument, ...] = (
    DocMeshDocument("README.md", "current-state"),
    DocMeshDocument("CHANGELOG.md", "current-state"),
    DocMeshDocument("CITATION.cff", "current-state"),
    DocMeshDocument("pyproject.toml", "current-state"),
    DocMeshDocument("src/agentic_project_kit/__init__.py", "current-state"),
    DocMeshDocument("docs/STATUS.md", "current-state"),
    DocMeshDocument("docs/handoff/CURRENT_HANDOFF.md", "current-state"),
    DocMeshDocument("AGENTS.md", "governance"),
    DocMeshDocument("docs/TEST_GATES.md", "governance"),
    DocMeshDocument("docs/DOCUMENTATION_COVERAGE.yaml", "governance"),
    DocMeshDocument("sentinel.yaml", "governance"),
    DocMeshDocument(".agentic/project.yaml", "governance"),
    DocMeshDocument("docs/architecture/ARCHITECTURE_CONTRACT.md", "architecture"),
    DocMeshDocument("docs/WORKFLOW_OUTPUT_CYCLE.md", "architecture"),
    DocMeshDocument("DESIGN.md", "architecture", required=False),
    DocMeshDocument(
        "docs/reports/status_roadmap_summary_after_pr105_20260512.md",
        "historical-plan",
        historical=True,
    ),
    DocMeshDocument("docs/V0.3.0_OUTPUT_REPAIR_PLAN.md", "historical-plan", required=False, historical=True),
)

HISTORICAL_BANNER = "This file is historical audit evidence, not the current source of truth."


_VERSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "pyproject.toml": re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE),
    "src/agentic_project_kit/__init__.py": re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE),
    "docs/STATUS.md": re.compile(r"^Current version:\s*([0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE),
    "docs/handoff/CURRENT_HANDOFF.md": re.compile(r"^Current version:\s*([0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE),
    "CITATION.cff": re.compile(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE),
    "README.md": re.compile(r"Version `([0-9]+\.[0-9]+\.[0-9]+)`"),
}

_VERIFIED_DOI_PATTERN = re.compile(
    r"(?:archived|Verified) v(?P<version>[0-9]+\.[0-9]+\.[0-9]+).*?(?P<doi>10\.5281/zenodo\.[0-9]+)",
    re.IGNORECASE,
)

_STALE_CURRENT_STATE_MARKERS = (
    "release candidate",
    "release-preparation branch",
    "must wait for post-release verification",
)

_STALE_MARKER_DOCUMENTS = frozenset(
    {
        "README.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    }
)

_REPAIR_POLICY: dict[str, tuple[str, bool, Literal["automatic", "manual"], str]] = {
    "historical-banner-missing": (
        "insert_historical_banner",
        True,
        "automatic",
        "Historical banner insertion is mechanical and does not alter semantic content.",
    ),
    "version-mismatch": (
        "align_version_marker",
        False,
        "manual",
        "Version alignment can be mechanical later, but the authoritative source must be reviewed first.",
    ),
    "release-doi-list-mismatch": (
        "sync_release_doi_list",
        False,
        "manual",
        "DOI list synchronization must preserve release evidence and should be reviewed before file edits.",
    ),
    "stale-current-state-marker": (
        "manual_review_required",
        False,
        "manual",
        "Stale wording may require contextual rewriting rather than mechanical deletion.",
    ),
    "missing-document": (
        "manual_review_required",
        False,
        "manual",
        "Missing documents require a maintainer decision before creation.",
    ),
    "missing-version": (
        "manual_review_required",
        False,
        "manual",
        "Missing version markers require a maintainer decision about the correct source of truth.",
    ),
}


def build_doc_mesh_report(project_root: Path) -> DocMeshReport:
    findings: list[DocMeshFinding] = []
    versions: dict[str, str] = {}
    contents: dict[str, str] = {}

    for document in DOC_MESH_DOCUMENTS:
        path = project_root / document.path
        if not path.exists():
            if document.required:
                findings.append(DocMeshFinding("missing-document", document.path, "required mesh document is missing"))
            continue

        content = path.read_text(encoding="utf-8")
        contents[document.path] = content
        if document.historical:
            findings.extend(_check_historical_document(document.path, content))
        elif document.path in _STALE_MARKER_DOCUMENTS:
            findings.extend(_check_current_state_document(document.path, content))

        pattern = _VERSION_PATTERNS.get(document.path)
        if pattern is not None:
            match = pattern.search(content)
            if match is None:
                findings.append(DocMeshFinding("missing-version", document.path, "current-state document has no machine-readable version marker"))
            else:
                versions[document.path] = match.group(1)

    findings.extend(_check_version_consistency(versions))
    findings.extend(_check_release_doi_consistency(contents))
    return DocMeshReport(documents=DOC_MESH_DOCUMENTS, findings=tuple(findings))


def build_doc_mesh_repair_plan(report: DocMeshReport) -> DocMeshRepairPlan:
    repairs = tuple(_repair_for_finding(finding) for finding in report.findings)
    return DocMeshRepairPlan(ok=not repairs, repairs=repairs)


def apply_doc_mesh_repair_plan(project_root: Path, plan: DocMeshRepairPlan) -> DocMeshRepairResult:
    actions: list[DocMeshRepairAction] = []
    skipped: list[DocMeshRepair] = []

    for repair in plan.repairs:
        if not (repair.safe and repair.mode == "automatic" and repair.action == "insert_historical_banner"):
            skipped.append(repair)
            continue
        actions.append(_insert_historical_banner(project_root, repair.path))

    return DocMeshRepairResult(
        changed=any(action.changed for action in actions),
        actions=tuple(actions),
        skipped=tuple(skipped),
    )


def render_doc_mesh_report(report: DocMeshReport) -> str:
    lines = ["Documentation mesh audit", ""]
    lines.append("Documents:")
    for document in report.documents:
        required = "required" if document.required else "optional"
        lines.append(f"- {document.path}: {document.category}, {required}")
    lines.append("")
    if report.ok:
        lines.append("Overall: PASS")
        return "\n".join(lines)

    lines.append("Findings:")
    for finding in report.findings:
        lines.append(f"- [{finding.code}] {finding.path}: {finding.message}")
    lines.append("")
    lines.append("Overall: FAIL")
    return "\n".join(lines)


def render_doc_mesh_repair_plan(plan: DocMeshRepairPlan) -> str:
    lines = ["Documentation mesh repair plan", ""]
    if plan.ok:
        lines.append("No repairs planned.")
        lines.append("")
        lines.append("Overall: PASS")
        return "\n".join(lines)

    lines.append("Repairs:")
    for repair in plan.repairs:
        safety = "safe" if repair.safe else "manual"
        lines.append(f"- [{repair.code}] {repair.path}: {repair.action} ({safety})")
    lines.append("")
    lines.append("Overall: REVIEW")
    return "\n".join(lines)


def render_doc_mesh_repair_result(result: DocMeshRepairResult) -> str:
    lines = ["Documentation mesh repair result", ""]
    if not result.actions and not result.skipped:
        lines.append("No repairs were needed.")
        lines.append("")
        lines.append("Overall: PASS")
        return "\n".join(lines)

    if result.actions:
        lines.append("Actions:")
        for action in result.actions:
            changed = "changed" if action.changed else "unchanged"
            lines.append(f"- {action.path}: {action.action} ({changed})")
        lines.append("")

    if result.skipped:
        lines.append("Skipped manual repairs:")
        for repair in result.skipped:
            lines.append(f"- [{repair.code}] {repair.path}: {repair.action}")
        lines.append("")

    lines.append("Overall: PASS")
    return "\n".join(lines)


def write_doc_mesh_json_report(report: DocMeshReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_doc_mesh_repair_plan(plan: DocMeshRepairPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_doc_mesh_repair_result(result: DocMeshRepairResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _repair_for_finding(finding: DocMeshFinding) -> DocMeshRepair:
    action, safe, mode, reason = _REPAIR_POLICY.get(
        finding.code,
        (
            "manual_review_required",
            False,
            "manual",
            "Unknown finding code requires manual review before any repair is attempted.",
        ),
    )
    return DocMeshRepair(
        code=finding.code,
        path=finding.path,
        action=action,
        safe=safe,
        mode=mode,
        reason=reason,
    )


def _insert_historical_banner(project_root: Path, relative_path: str) -> DocMeshRepairAction:
    path = project_root / relative_path
    if not path.exists():
        return DocMeshRepairAction(relative_path, "insert_historical_banner", False, "file does not exist")

    content = path.read_text(encoding="utf-8")
    if HISTORICAL_BANNER in content:
        return DocMeshRepairAction(relative_path, "insert_historical_banner", False, "historical banner already present")

    path.write_text(f"{HISTORICAL_BANNER}\n\n{content}", encoding="utf-8")
    return DocMeshRepairAction(relative_path, "insert_historical_banner", True, "historical banner inserted")


def _check_historical_document(path: str, content: str) -> list[DocMeshFinding]:
    findings: list[DocMeshFinding] = []
    if HISTORICAL_BANNER not in content:
        findings.append(
            DocMeshFinding(
                "historical-banner-missing",
                path,
                "historical or roadmap document must be marked as non-current source of truth",
            )
        )
    return findings


def _check_current_state_document(path: str, content: str) -> list[DocMeshFinding]:
    findings: list[DocMeshFinding] = []
    lower = content.lower()
    for marker in _STALE_CURRENT_STATE_MARKERS:
        if marker in lower:
            findings.append(DocMeshFinding("stale-current-state-marker", path, f"stale wording present: {marker!r}"))
    return findings


def _check_version_consistency(versions: dict[str, str]) -> list[DocMeshFinding]:
    if not versions:
        return []

    expected = versions.get("pyproject.toml") or next(iter(versions.values()))
    findings: list[DocMeshFinding] = []
    for path, version in sorted(versions.items()):
        if version != expected:
            findings.append(
                DocMeshFinding(
                    "version-mismatch",
                    path,
                    f"version {version!r} does not match expected version {expected!r}",
                )
            )
    return findings


def _extract_verified_dois(content: str) -> dict[str, str]:
    return {match.group("version"): match.group("doi") for match in _VERIFIED_DOI_PATTERN.finditer(content)}


def _check_release_doi_consistency(contents: dict[str, str]) -> list[DocMeshFinding]:
    findings: list[DocMeshFinding] = []
    readme = contents.get("README.md", "")
    sources = {
        "CHANGELOG.md": contents.get("CHANGELOG.md", ""),
        "CITATION.cff": contents.get("CITATION.cff", ""),
        "docs/STATUS.md": contents.get("docs/STATUS.md", ""),
        "docs/handoff/CURRENT_HANDOFF.md": contents.get("docs/handoff/CURRENT_HANDOFF.md", ""),
    }
    expected: dict[str, str] = {}
    for content in sources.values():
        expected.update(_extract_verified_dois(content))

    readme_dois = _extract_verified_dois(readme)
    for version, doi in sorted(expected.items()):
        if readme_dois.get(version) != doi:
            findings.append(
                DocMeshFinding(
                    "release-doi-list-mismatch",
                    "README.md",
                    f"README DOI list missing or mismatching v{version} -> {doi}",
                )
            )
    return findings
