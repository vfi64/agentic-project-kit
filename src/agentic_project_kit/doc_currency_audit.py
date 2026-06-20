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
    warnings: tuple[DocCurrencyFinding, ...] = ()

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
            "warning_count": len(self.warnings),
            "findings": [item.as_dict() for item in self.findings],
            "blockers": [item.as_dict() for item in self.blockers],
            "warnings": [item.as_dict() for item in self.warnings],
            "current_state_currency": {
                "status": "PASS"
                if not any(item.check.startswith("current_state_currency_") for item in self.blockers)
                else "FAIL",
                "blockers": [
                    item.as_dict()
                    for item in self.blockers
                    if item.check.startswith("current_state_currency_")
                ],
                "warnings": [
                    item.as_dict()
                    for item in self.warnings
                    if item.check.startswith("current_state_currency_")
                ],
            },
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


def _warning(findings: list[DocCurrencyFinding], warnings: list[DocCurrencyFinding], path: str, check: str, detail: str) -> None:
    item = DocCurrencyFinding(path=path, check=check, status="WARN", detail=detail)
    findings.append(item)
    warnings.append(item)


def audit_doc_currency(root: Path = Path(".")) -> DocCurrencyAuditResult:
    root = root.resolve()
    findings: list[DocCurrencyFinding] = []
    blockers: list[DocCurrencyFinding] = []
    warnings: list[DocCurrencyFinding] = []

    version = _project_version(root)
    package_version = _package_version(root)
    version_doi, concept_doi = _doi_values(root, version)
    changelog = _read_text(root, "CHANGELOG.md") or ""
    prepared_release_pending_doi = bool(
        version
        and re.search(rf"(?ms)^##\s+v{re.escape(version)}\b.*?Zenodo DOI verification pending", changelog)
    )

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
        version_doi is not None or prepared_release_pending_doi,
        f"version_doi={version_doi}, prepared_release_pending_doi={prepared_release_pending_doi}",
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
            mentions_current_version = f"v{version}" in text or version in text
            if relative == "docs/releases/VERIFIED_RELEASES.md" and prepared_release_pending_doi:
                mentions_current_version = True
            _finding(
                findings,
                blockers,
                relative,
                "mentions_current_version",
                mentions_current_version,
                f"version={version}, prepared_release_pending_doi={prepared_release_pending_doi}",
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

    _audit_current_state_currency(
        root=root,
        version=version,
        findings=findings,
        blockers=blockers,
        warnings=warnings,
    )

    return DocCurrencyAuditResult(
        root=root.as_posix(),
        version=version,
        package_version=package_version,
        version_doi=version_doi,
        concept_doi=concept_doi,
        findings=tuple(findings),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def _audit_current_state_currency(
    *,
    root: Path,
    version: str | None,
    findings: list[DocCurrencyFinding],
    blockers: list[DocCurrencyFinding],
    warnings: list[DocCurrencyFinding],
) -> None:
    readme = _read_text(root, "README.md") or ""
    citation = _read_text(root, "CITATION.cff") or ""
    status = _read_text(root, "docs/STATUS.md") or ""
    changelog = _read_text(root, "CHANGELOG.md") or ""

    current_version_markers = re.findall(r"^Current version:\s*(\d+\.\d+\.\d+)\s*$", readme, re.MULTILINE)
    _finding(
        findings,
        blockers,
        "README.md",
        "current_state_currency_readme_single_current_version_marker",
        len(current_version_markers) == 1,
        f"marker_count={len(current_version_markers)}",
    )
    if version and current_version_markers:
        _finding(
            findings,
            blockers,
            "README.md",
            "current_state_currency_readme_current_version_matches_package",
            current_version_markers == [version],
            f"markers={current_version_markers}, package={version}",
        )

    citation_version = _match_text(r"^version:\s*['\"]?([^'\"\n]+)['\"]?$", citation)
    citation_date = _match_text(r"^date-released:\s*['\"]?(\d{4}-\d{2}-\d{2})['\"]?$", citation)
    changelog_date = _current_changelog_date(changelog, version)
    _finding(
        findings,
        blockers,
        "CITATION.cff",
        "current_state_currency_citation_version_matches_package",
        bool(version and citation_version == version),
        f"citation={citation_version}, package={version}",
    )
    _finding(
        findings,
        blockers,
        "CITATION.cff",
        "current_state_currency_citation_date_matches_current_changelog",
        bool(citation_date and changelog_date and citation_date == changelog_date),
        f"citation_date={citation_date}, changelog_date={changelog_date}",
    )

    status_lines = status.splitlines()
    status_current_block = _markdown_heading_section(status, "## Current State")
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "current_state_currency_status_single_current_state_block",
        status.count("## Current State") == 1,
        f"current_state_heading_count={status.count('## Current State')}",
    )
    status_current_version_marker_count = len(re.findall(r"^Current version:\s*", status, re.MULTILINE))
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "current_state_currency_status_single_current_version_marker",
        status_current_version_marker_count == 1,
        f"current_version_marker_count={status_current_version_marker_count}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "current_state_currency_status_current_state_at_top",
        len(status_lines) > 2 and status_lines[2] == "## Current State",
        f"line3={status_lines[2] if len(status_lines) > 2 else '<missing>'}",
    )
    _finding(
        findings,
        blockers,
        "docs/STATUS.md",
        "current_state_currency_status_top_not_historical_pr",
        "#1436" not in status_current_block
        and "Current planning-slice branch" not in status_current_block,
        "current_state_block_checked",
    )

    current_section = _changelog_section(changelog, version)
    previous_section = _previous_changelog_section(changelog, version)
    _finding(
        findings,
        blockers,
        "CHANGELOG.md",
        "current_state_currency_changelog_current_section_exists",
        bool(current_section),
        f"version={version}",
    )
    if current_section and previous_section:
        _finding(
            findings,
            blockers,
            "CHANGELOG.md",
            "current_state_currency_changelog_not_duplicate_previous_release",
            current_section.strip() != previous_section.strip(),
            "current release section compared with previous release section",
        )
    if current_section and ("./ns" in current_section or "ns release-prep" in current_section):
        if version == "0.4.10":
            _warning(
                findings,
                warnings,
                "CHANGELOG.md",
                "current_state_currency_changelog_legacy_ns_route_in_pinned_release",
                "v0.4.10 is DOI-pinned; legacy text is warned but not rewritten in this slice",
            )
        else:
            _finding(
                findings,
                blockers,
                "CHANGELOG.md",
                "current_state_currency_changelog_no_removed_ns_route_in_current_release",
                False,
                "current release section references removed ./ns route",
            )

    _finding(
        findings,
        blockers,
        "tools/ns_release_metadata_prep.py",
        "current_state_currency_legacy_release_metadata_prep_tool_removed",
        not (root / "tools" / "ns_release_metadata_prep.py").exists(),
        "legacy tool wrapper must not exist",
    )

    for path in sorted((root / "docs" / "releases").glob("*.release-notes.json")):
        text = path.read_text(encoding="utf-8")
        _finding(
            findings,
            blockers,
            path.relative_to(root).as_posix(),
            "current_state_currency_release_notes_json_projection_shape",
            '"kind": "release_notes"' in text and '"schema_version": 1' in text,
            "committed release-note JSON must be generator-shaped",
        )


def _match_text(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _current_changelog_date(changelog: str, version: str | None) -> str | None:
    if not version:
        return None
    return _match_text(rf"^##\s+v{re.escape(version)}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})", changelog)


def _markdown_heading_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ""
    section: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        section.append(line)
    return "\n".join(section).strip()


def _changelog_section(changelog: str, version: str | None) -> str:
    if not version:
        return ""
    match = re.search(
        rf"(?ms)^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        changelog,
    )
    return match.group(0) if match else ""


def _previous_changelog_section(changelog: str, version: str | None) -> str:
    if not version:
        return ""
    current = re.search(
        rf"(?ms)^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        changelog,
    )
    if not current:
        return ""
    previous = re.search(r"(?ms)^##\s+v\d+\.\d+\.\d+\s+-\s+\d{4}-\d{2}-\d{2}.*?(?=^##\s+v|\Z)", changelog[current.end() :])
    return previous.group(0) if previous else ""


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
        f"WARNING_COUNT={len(result.warnings)}",
    ]

    for item in result.blockers:
        lines.append(
            f"BLOCKER={item.path}|{item.check}|{item.status}|{item.detail}"
        )
    for item in result.warnings:
        lines.append(f"WARNING={item.path}|{item.check}|{item.status}|{item.detail}")

    return "\n".join(lines) + "\n"
