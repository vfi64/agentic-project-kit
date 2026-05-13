from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any


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
        elif document.category == "current-state":
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


def write_doc_mesh_json_report(report: DocMeshReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
