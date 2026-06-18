from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import tomllib


CURRENT_STATE_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/releases/VERIFIED_RELEASES.md",
)

HANDOFF_PACKAGE_DOCS = (
    "docs/reports/handoff-packages/latest/successor_prompt.md",
    "docs/reports/handoff-packages/latest/validation_report.json",
    "docs/reports/handoff-packages/latest/execution_contract.json",
    "docs/reports/handoff-packages/latest/source_manifest.json",
)


@dataclass(frozen=True)
class DocCurrencyFinding:
    path: str
    check: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DocCurrencyAuditResult:
    root: str
    version: str | None
    package_version: str | None
    version_doi: str | None
    concept_doi: str | None
    findings: tuple[DocCurrencyFinding, ...]
    blockers: tuple[DocCurrencyFinding, ...]

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
            "kind": "doc_currency_audit",
            "root": self.root,
            "status": self.status,
            "version": self.version,
            "package_version": self.package_version,
            "version_doi": self.version_doi,
            "concept_doi": self.concept_doi,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [item.as_dict() for item in self.findings],
            "blockers": [item.as_dict() for item in self.blockers],
        }


def _read_text(root: Path, relative: str) -> str | None:
    path = root / relative
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _project_version(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    value = project.get("version")
    return str(value) if value is not None else None


def _package_version(root: Path) -> str | None:
    init_py = root / "src" / "agentic_project_kit" / "__init__.py"
    if not init_py.exists():
        return None
    for line in init_py.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("__version__"):
            continue
        if "=" not in stripped:
            continue
        value = stripped.split("=", 1)[1].strip()
        if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
            return value[1:-1]
    return None


def _doi_values(root: Path, version: str | None) -> tuple[str | None, str | None]:
    verified = _read_text(root, "docs/releases/VERIFIED_RELEASES.md") or ""
    version_doi = None
    concept_doi = None

    if version:
        version_section = re.search(
            rf"v{re.escape(version)}[\s\S]*?(10\.5281/zenodo\.\d+)",
            verified,
        )
        if version_section:
            version_doi = version_section.group(1)

    dois = re.findall(r"10\.5281/zenodo\.\d+", verified)
    if dois:
        # The concept DOI is usually repeated as the stable archive DOI and differs from the version DOI.
        for doi in reversed(dois):
            if doi != version_doi:
                concept_doi = doi
                break

    return version_doi, concept_doi


def _finding(
    findings: list[DocCurrencyFinding],
    blockers: list[DocCurrencyFinding],
    path: str,
    check: str,
    ok: bool,
    detail: str,
) -> None:
    item = DocCurrencyFinding(
        path=path,
        check=check,
        status="PASS" if ok else "FAIL",
        detail=detail,
    )
    findings.append(item)
    if not ok:
        blockers.append(item)


def audit_doc_currency(root: Path = Path(".")) -> DocCurrencyAuditResult:
    root = root.resolve()
    findings: list[DocCurrencyFinding] = []
    blockers: list[DocCurrencyFinding] = []

    version = _project_version(root)
    package_version = _package_version(root)
    version_doi, concept_doi = _doi_values(root, version)

    _finding(
        findings,
        blockers,
        "pyproject.toml",
        "project_version_exists",
        version is not None,
        f"version={version}",
    )
    _finding(
        findings,
        blockers,
        "src/agentic_project_kit/__init__.py",
        "package_version_matches_project",
        bool(version and package_version == version),
        f"project={version}, package={package_version}",
    )
    _finding(
        findings,
        blockers,
        "docs/releases/VERIFIED_RELEASES.md",
        "current_version_doi_exists",
        version_doi is not None,
        f"version_doi={version_doi}",
    )
    _finding(
        findings,
        blockers,
        "docs/releases/VERIFIED_RELEASES.md",
        "concept_doi_exists",
        concept_doi is not None,
        f"concept_doi={concept_doi}",
    )

    for relative in CURRENT_STATE_DOCS:
        text = _read_text(root, relative)
        _finding(
            findings,
            blockers,
            relative,
            "file_exists",
            text is not None,
            "exists" if text is not None else "missing",
        )
        if text is None:
            continue

        if version:
            _finding(
                findings,
                blockers,
                relative,
                "mentions_current_version",
                f"v{version}" in text or version in text,
                f"version={version}",
            )
        if version_doi:
            _finding(
                findings,
                blockers,
                relative,
                "mentions_current_version_doi",
                version_doi in text,
                f"version_doi={version_doi}",
            )
        if concept_doi and relative in {"README.md", "CITATION.cff", "docs/releases/VERIFIED_RELEASES.md"}:
            _finding(
                findings,
                blockers,
                relative,
                "mentions_concept_doi",
                concept_doi in text,
                f"concept_doi={concept_doi}",
            )

    for relative in HANDOFF_PACKAGE_DOCS:
        text = _read_text(root, relative)
        _finding(
            findings,
            blockers,
            relative,
            "handoff_package_file_exists",
            text is not None,
            "exists" if text is not None else "missing",
        )
        if not text or not version:
            continue
        if relative.endswith("source_manifest.json"):
            _finding(
                findings,
                blockers,
                relative,
                "handoff_package_source_manifest_structural_anchor",
                '"sources"' in text or '"files"' in text or '"manifest"' in text,
                "source_manifest is structural; version/PASS is not required",
            )
            continue
        _finding(
            findings,
            blockers,
            relative,
            "handoff_package_mentions_current_version_or_status",
            version in text or "PASS" in text,
            f"version={version}",
        )

    return DocCurrencyAuditResult(
        root=root.as_posix(),
        version=version,
        package_version=package_version,
        version_doi=version_doi,
        concept_doi=concept_doi,
        findings=tuple(findings),
        blockers=tuple(blockers),
    )


def render_doc_currency_audit(result: DocCurrencyAuditResult) -> str:
    lines = [
        "DOC_CURRENCY_AUDIT",
        f"STATUS={result.status}",
        f"VERSION={result.version}",
        f"PACKAGE_VERSION={result.package_version}",
        f"VERSION_DOI={result.version_doi}",
        f"CONCEPT_DOI={result.concept_doi}",
        f"FINDING_COUNT={len(result.findings)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]

    for item in result.blockers:
        lines.append(
            f"BLOCKER={item.path}|{item.check}|{item.status}|{item.detail}"
        )

    return "\n".join(lines) + "\n"
