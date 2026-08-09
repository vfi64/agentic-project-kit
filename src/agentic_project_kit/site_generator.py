from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
import json
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
import tomllib
from typing import Any

import yaml

from agentic_project_kit.command_manifest import SAFETY_VALUES, SURFACE_VALUES, load_manifest, manifest_sha
from agentic_project_kit.gui_command_projection import diagnostic_priority_for_command
from agentic_project_kit.site_claims import ClaimEvaluationReport, evaluate_site_claims


PRODUCT_NAME = "Agentic Execution Runtime"
FORMER_PRODUCT_NAME = "Agentic Project Kit"
SITE_KIND = "agentic_project_kit_generated_site"


@dataclass(frozen=True)
class SiteFoundationMetadata:
    product_name: str
    former_product_name: str
    package_name: str
    package_version: str
    requires_python: str
    command_count: int
    manifest_sha: str
    reproduced_manifest_sha: str
    build_commit: str
    release_tag: str
    concept_doi: str
    version_doi: str
    current_verified_main: str
    surface_counts: dict[str, int]
    safety_counts: dict[str, int]
    command_group_count: int

    @property
    def manifest_identity_verified(self) -> bool:
        return self.manifest_sha == self.reproduced_manifest_sha

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["manifest_identity_verified"] = self.manifest_identity_verified
        return data


@dataclass(frozen=True)
class SiteCommandEntry:
    qualified_name: str
    group: str
    surface: str
    safety: str
    dry_run_available: bool
    diagnostic_priority: str
    when_to_use: str
    help: str
    params: tuple[dict[str, object], ...]

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["params"] = [dict(param) for param in self.params]
        return data


@dataclass(frozen=True)
class SiteCommandCatalog:
    entries: tuple[SiteCommandEntry, ...]

    @property
    def guided_entries(self) -> tuple[SiteCommandEntry, ...]:
        return tuple(entry for entry in self.entries if entry.surface == "orchestrator")

    @property
    def diagnostic_entries(self) -> tuple[SiteCommandEntry, ...]:
        return tuple(entry for entry in self.entries if entry.surface == "diagnostic")

    @property
    def common_blocker_entries(self) -> tuple[SiteCommandEntry, ...]:
        return tuple(
            entry for entry in self.diagnostic_entries if entry.diagnostic_priority == "common_blocker"
        )

    def surface_counts(self) -> dict[str, int]:
        return {
            surface: len([entry for entry in self.entries if entry.surface == surface])
            for surface in sorted(SURFACE_VALUES)
        }

    def safety_counts(self) -> dict[str, int]:
        return {
            safety: len([entry for entry in self.entries if entry.safety == safety])
            for safety in sorted(SAFETY_VALUES)
        }

    def group_counts(self) -> dict[str, int]:
        groups = sorted({entry.group for entry in self.entries})
        return {group: len([entry for entry in self.entries if entry.group == group]) for group in groups}

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "site_command_catalog",
            "command_count": len(self.entries),
            "guided_count": len(self.guided_entries),
            "diagnostic_count": len(self.diagnostic_entries),
            "surface_counts": self.surface_counts(),
            "safety_counts": self.safety_counts(),
            "group_counts": self.group_counts(),
            "entries": [entry.as_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class SiteStatusProjection:
    current_version: str
    current_verified_release: str
    current_release_tag: str
    concept_doi: str
    version_doi: str
    current_verified_main: str
    latest_substantive_work: str
    next_safe_step: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SiteRoadmapProjection:
    status: str
    updated_after_pr: str
    updated_after_pr_semantics: str
    updated_after_pr_current_main_claimed: bool | None
    strategy_counts: dict[str, int]
    roadmap_counts: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SiteFoundationReport:
    root: str
    metadata: SiteFoundationMetadata | None
    command_catalog: SiteCommandCatalog | None
    status_projection: SiteStatusProjection
    roadmap_projection: SiteRoadmapProjection
    claim_report: ClaimEvaluationReport
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers and self.metadata is not None

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "site_foundation_report",
            "root": self.root,
            "status": self.status,
            "metadata": self.metadata.as_dict() if self.metadata is not None else None,
            "command_catalog": (
                self.command_catalog.as_dict() if self.command_catalog is not None else None
            ),
            "status_projection": self.status_projection.as_dict(),
            "roadmap_projection": self.roadmap_projection.as_dict(),
            "claim_report": self.claim_report.as_dict(),
            "blockers": list(self.blockers),
            "blocker_count": len(self.blockers),
        }


@dataclass(frozen=True)
class SiteBuildResult:
    root: str
    output_dir: str
    report: SiteFoundationReport
    files: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.report.ok

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return self.report.returncode

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": SITE_KIND,
            "root": self.root,
            "output_dir": self.output_dir,
            "status": self.status,
            "files": list(self.files),
            "file_count": len(self.files),
            "report": self.report.as_dict(),
        }


def collect_site_foundation_metadata(
    root: Path = Path("."),
    *,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> SiteFoundationReport:
    root = root.resolve()
    blockers: list[str] = []
    pyproject = _read_pyproject(root, blockers)
    committed_manifest = manifest if manifest is not None else _read_manifest(root, blockers)

    project = pyproject.get("project") if isinstance(pyproject.get("project"), dict) else {}
    package_name = _string(project.get("name"))
    package_version = _string(project.get("version"))
    requires_python = _string(project.get("requires-python"))
    if not package_name:
        blockers.append("pyproject.toml project.name is missing")
    if not package_version:
        blockers.append("pyproject.toml project.version is missing")
    if not requires_python:
        blockers.append("pyproject.toml project.requires-python is missing")

    commands = committed_manifest.get("commands") if isinstance(committed_manifest, dict) else None
    if not isinstance(commands, list) or not commands:
        blockers.append("command manifest commands must be a non-empty list")
        commands = []
    meta = committed_manifest.get("meta") if isinstance(committed_manifest, dict) else {}
    manifest_identity = _string(meta.get("manifest_sha")) if isinstance(meta, dict) else ""
    reproduced_manifest_identity = manifest_sha(commands)
    if not manifest_identity:
        blockers.append("command manifest meta.manifest_sha is missing")
    elif manifest_identity != reproduced_manifest_identity:
        blockers.append(
            "command manifest meta.manifest_sha does not match the reproduced command manifest hash"
        )

    commit = build_commit or _current_commit(root)
    if not commit:
        blockers.append("build commit is not available")

    command_catalog = _build_command_catalog(commands, blockers)
    status_projection = _read_status_projection(root)
    roadmap_projection = _read_roadmap_projection(root)
    claim_report = evaluate_site_claims(root, command_catalog=command_catalog)
    blockers.extend(claim_report.blockers)
    concept_doi = status_projection.concept_doi or _citation_value(root, "doi")
    version_doi = status_projection.version_doi
    release_tag = status_projection.current_release_tag
    current_verified_main = status_projection.current_verified_main

    metadata = None
    if not blockers and command_catalog is not None:
        metadata = SiteFoundationMetadata(
            product_name=PRODUCT_NAME,
            former_product_name=FORMER_PRODUCT_NAME,
            package_name=package_name,
            package_version=package_version,
            requires_python=requires_python,
            command_count=len(commands),
            manifest_sha=manifest_identity,
            reproduced_manifest_sha=reproduced_manifest_identity,
            build_commit=commit,
            release_tag=release_tag,
            concept_doi=concept_doi,
            version_doi=version_doi,
            current_verified_main=current_verified_main,
            surface_counts=command_catalog.surface_counts(),
            safety_counts=command_catalog.safety_counts(),
            command_group_count=len(command_catalog.group_counts()),
        )

    return SiteFoundationReport(
        root=root.as_posix(),
        metadata=metadata,
        command_catalog=command_catalog,
        status_projection=status_projection,
        roadmap_projection=roadmap_projection,
        claim_report=claim_report,
        blockers=tuple(blockers),
    )


def build_site(
    root: Path = Path("."),
    *,
    output_dir: Path | None = None,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> SiteBuildResult:
    root = root.resolve()
    output = (output_dir or root / "site" / "dist").resolve()
    report = collect_site_foundation_metadata(
        root,
        build_commit=build_commit,
        manifest=manifest,
    )
    if not report.ok:
        return SiteBuildResult(
            root=root.as_posix(),
            output_dir=output.as_posix(),
            report=report,
            files=(),
        )

    metadata = report.metadata
    command_catalog = report.command_catalog
    assert metadata is not None
    assert command_catalog is not None
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "static").mkdir(parents=True, exist_ok=True)
    (output / "commands").mkdir(parents=True, exist_ok=True)
    (output / "claims").mkdir(parents=True, exist_ok=True)

    index_html = render_index_html(root, report)
    site_json = json.dumps(
        {
            "schema_version": 1,
            "kind": SITE_KIND,
            "metadata": metadata.as_dict(),
            "command_catalog": command_catalog.as_dict(),
            "status_projection": report.status_projection.as_dict(),
            "roadmap_projection": report.roadmap_projection.as_dict(),
            "claim_report": report.claim_report.as_dict(),
        },
        indent=2,
        sort_keys=True,
    )
    (output / "index.html").write_text(index_html, encoding="utf-8")
    (output / "site.json").write_text(site_json + "\n", encoding="utf-8")
    (output / "commands" / "commands.json").write_text(
        json.dumps(command_catalog.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "claims" / "claims.json").write_text(
        json.dumps(report.claim_report.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "claims" / "index.html").write_text(
        render_claims_html(root, metadata, report.claim_report),
        encoding="utf-8",
    )
    (output / "commands" / "guided.html").write_text(
        render_command_view_html(
            root,
            metadata,
            title="Guided Commands",
            description="Primary user and lifecycle operations generated from surface=orchestrator.",
            entries=command_catalog.guided_entries,
        ),
        encoding="utf-8",
    )
    (output / "commands" / "diagnostics.html").write_text(
        render_command_view_html(
            root,
            metadata,
            title="Diagnostic Commands",
            description="Inspection and blocker-analysis operations generated from surface=diagnostic.",
            entries=command_catalog.diagnostic_entries,
        ),
        encoding="utf-8",
    )
    (output / "commands" / "index.html").write_text(
        render_command_view_html(
            root,
            metadata,
            title="Complete Command Reference",
            description="All registered commands generated from the current command manifest.",
            entries=command_catalog.entries,
        ),
        encoding="utf-8",
    )
    for source in sorted((root / "site" / "static").iterdir()):
        if source.is_file():
            shutil.copy2(source, output / "static" / source.name)

    files = tuple(
        sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file())
    )
    return SiteBuildResult(
        root=root.as_posix(),
        output_dir=output.as_posix(),
        report=report,
        files=files,
    )


def render_index_html(root: Path, report: SiteFoundationReport) -> str:
    metadata = report.metadata
    command_catalog = report.command_catalog
    assert metadata is not None
    assert command_catalog is not None
    template_path = root / "site" / "templates" / "index.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    values = {
        "product_name": escape(metadata.product_name),
        "former_product_name": escape(metadata.former_product_name),
        "package_name": escape(metadata.package_name),
        "package_version": escape(metadata.package_version),
        "requires_python": escape(metadata.requires_python),
        "command_count": str(metadata.command_count),
        "manifest_sha": escape(metadata.manifest_sha),
        "reproduced_manifest_sha": escape(metadata.reproduced_manifest_sha),
        "manifest_identity_verified": str(metadata.manifest_identity_verified).lower(),
        "build_commit": escape(metadata.build_commit),
        "release_tag": escape(metadata.release_tag or "not recorded"),
        "concept_doi": escape(metadata.concept_doi or "not recorded"),
        "version_doi": escape(metadata.version_doi or "not recorded"),
        "current_verified_main": escape(metadata.current_verified_main or "not recorded"),
        "orchestrator_count": str(metadata.surface_counts.get("orchestrator", 0)),
        "diagnostic_count": str(metadata.surface_counts.get("diagnostic", 0)),
        "primitive_count": str(metadata.surface_counts.get("primitive", 0)),
        "command_group_count": str(metadata.command_group_count),
        "project_direction_status": escape(report.roadmap_projection.status or "not recorded"),
        "claim_verified_count": str(report.claim_report.status_counts().get("verified", 0)),
        "claim_unverified_count": str(report.claim_report.status_counts().get("unverified", 0)),
        "claim_planned_count": str(report.claim_report.status_counts().get("planned", 0)),
        "required_claim_count": str(report.claim_report.required_counts().get("required", 0)),
        "latest_substantive_work": escape(
            report.status_projection.latest_substantive_work or "not recorded"
        ),
        "next_safe_step": escape(report.status_projection.next_safe_step or "not recorded"),
        "guided_command_items": _command_summary_items(command_catalog.guided_entries, limit=8),
        "common_diagnostic_items": _command_summary_items(
            command_catalog.common_blocker_entries,
            limit=6,
            empty="No common blocker diagnostics are currently projected.",
        ),
        "verified_now_items": _claim_summary_items(
            [
                claim
                for claim in report.claim_report.claims
                if claim.required and claim.status == "verified"
            ],
            empty="No required claims are currently verified.",
        ),
        "available_evolving_items": _claim_summary_items(
            [
                claim
                for claim in report.claim_report.claims
                if not claim.required and claim.status == "verified"
            ],
            empty="No optional claims are currently verified.",
        ),
        "planned_items": _claim_summary_items(
            [claim for claim in report.claim_report.claims if claim.status == "planned"],
            empty="No planned public claims are currently declared.",
        ),
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _command_summary_items(
    entries: tuple[SiteCommandEntry, ...],
    *,
    limit: int,
    empty: str = "No commands are currently projected.",
) -> str:
    if not entries:
        return f"          <li>{escape(empty)}</li>"
    rows = []
    for entry in entries[:limit]:
        rows.append(
            "          <li>"
            f"<code>{escape(entry.qualified_name)}</code>"
            f"<span>{escape(entry.when_to_use)}</span>"
            "</li>"
        )
    return "\n".join(rows)


def _claim_summary_items(claims: list[object], *, empty: str) -> str:
    if not claims:
        return f"          <li>{escape(empty)}</li>"
    rows = []
    for claim in sorted(claims, key=lambda item: str(getattr(item, "id", ""))):
        rows.append(
            "          <li>"
            f"<code>{escape(str(getattr(claim, 'id', '')))}</code>"
            f"<span>{escape(str(getattr(claim, 'text', '')))}</span>"
            "</li>"
        )
    return "\n".join(rows)


def render_claims_html(
    root: Path,
    metadata: SiteFoundationMetadata,
    claim_report: ClaimEvaluationReport,
) -> str:
    template_path = root / "site" / "templates" / "claims.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    rows = "\n".join(_claim_table_row(claim) for claim in claim_report.claims)
    values = {
        "product_name": escape(metadata.product_name),
        "manifest_sha": escape(metadata.manifest_sha),
        "package_version": escape(metadata.package_version),
        "claim_count": str(len(claim_report.claims)),
        "verified_count": str(claim_report.status_counts().get("verified", 0)),
        "unverified_count": str(claim_report.status_counts().get("unverified", 0)),
        "planned_count": str(claim_report.status_counts().get("planned", 0)),
        "required_count": str(claim_report.required_counts().get("required", 0)),
        "optional_count": str(claim_report.required_counts().get("optional", 0)),
        "rows": rows,
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _claim_table_row(claim: object) -> str:
    claim_id = escape(str(getattr(claim, "id", "")))
    text = escape(str(getattr(claim, "text", "")))
    status = escape(str(getattr(claim, "status", "")))
    required = "yes" if bool(getattr(claim, "required", False)) else "no"
    evidence = getattr(claim, "evidence", ())
    evidence_text = ", ".join(str(getattr(item, "evidence_type", "")) for item in evidence) or "none"
    return (
        "          <tr>"
        f"<td><code>{claim_id}</code></td>"
        f"<td>{text}</td>"
        f"<td>{status}</td>"
        f"<td>{required}</td>"
        f"<td>{escape(evidence_text)}</td>"
        "</tr>"
    )


def render_command_view_html(
    root: Path,
    metadata: SiteFoundationMetadata,
    *,
    title: str,
    description: str,
    entries: tuple[SiteCommandEntry, ...],
) -> str:
    template_path = root / "site" / "templates" / "commands.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    rows = "\n".join(_command_table_row(entry, metadata) for entry in entries)
    values = {
        "product_name": escape(metadata.product_name),
        "title": escape(title),
        "description": escape(description),
        "manifest_sha": escape(metadata.manifest_sha),
        "package_version": escape(metadata.package_version),
        "command_count": str(len(entries)),
        "rows": rows,
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _command_table_row(entry: SiteCommandEntry, metadata: SiteFoundationMetadata) -> str:
    dry_run = "yes" if entry.dry_run_available else "no"
    params = ", ".join(str(param.get("name") or "") for param in entry.params) or "none"
    return (
        "          <tr>"
        f"<td><code>{escape(entry.qualified_name)}</code></td>"
        f"<td>{escape(entry.group)}</td>"
        f"<td>{escape(entry.surface)}</td>"
        f"<td>{escape(entry.safety)}</td>"
        f"<td>{dry_run}</td>"
        f"<td>{escape(entry.when_to_use)}</td>"
        f"<td>{escape(params)}</td>"
        f"<td>{escape(metadata.package_version)}</td>"
        f"<td><code>{escape(metadata.manifest_sha)}</code></td>"
        "</tr>"
    )


def _read_pyproject(root: Path, blockers: list[str]) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.exists():
        blockers.append("pyproject.toml is missing")
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        blockers.append(f"pyproject.toml is not valid TOML: {exc}")
        return {}


def _read_manifest(root: Path, blockers: list[str]) -> dict[str, Any]:
    try:
        return load_manifest(root)
    except Exception as exc:
        blockers.append(f"command manifest is not readable: {exc}")
        return {}


def _build_command_catalog(
    commands: list[Any],
    blockers: list[str],
) -> SiteCommandCatalog | None:
    entries: list[SiteCommandEntry] = []
    seen: set[str] = set()
    for index, command in enumerate(commands):
        entry_blockers: list[str] = []
        if not isinstance(command, dict):
            blockers.append(f"command manifest entry {index} is not an object")
            continue
        qualified_name = _string(command.get("qualified_name"))
        group = _string(command.get("group"))
        surface = _string(command.get("surface"))
        safety = _string(command.get("safety"))
        when_to_use = _string(command.get("when_to_use"))
        params = command.get("params")
        if not qualified_name:
            entry_blockers.append(f"command manifest entry {index} has no qualified_name")
        elif qualified_name in seen:
            entry_blockers.append(f"duplicate command in manifest: {qualified_name}")
        else:
            seen.add(qualified_name)
        if not group:
            entry_blockers.append(f"{qualified_name or index}: group is missing")
        if surface not in SURFACE_VALUES:
            entry_blockers.append(f"{qualified_name or index}: invalid surface {surface!r}")
        if safety not in SAFETY_VALUES:
            entry_blockers.append(f"{qualified_name or index}: invalid safety {safety!r}")
        if "dry_run_available" not in command or not isinstance(
            command.get("dry_run_available"), bool
        ):
            entry_blockers.append(f"{qualified_name or index}: dry_run_available must be boolean")
        if not when_to_use:
            entry_blockers.append(f"{qualified_name or index}: when_to_use is missing")
        if not isinstance(params, list):
            entry_blockers.append(f"{qualified_name or index}: params must be a list")
            params = []
        blockers.extend(entry_blockers)
        if entry_blockers:
            continue
        entries.append(
            SiteCommandEntry(
                qualified_name=qualified_name,
                group=group,
                surface=surface,
                safety=safety,
                dry_run_available=bool(command.get("dry_run_available")),
                diagnostic_priority=diagnostic_priority_for_command(command),
                when_to_use=when_to_use,
                help=_string(command.get("help")),
                params=tuple(_param_summary(param) for param in params if isinstance(param, dict)),
            )
        )
    if not entries:
        blockers.append("command catalog has no renderable commands")
        return None
    catalog = SiteCommandCatalog(entries=tuple(sorted(entries, key=lambda entry: entry.qualified_name)))
    if not catalog.guided_entries:
        blockers.append("guided command view has no orchestrator commands")
    if not catalog.diagnostic_entries:
        blockers.append("diagnostic command view has no diagnostic commands")
    return catalog


def _param_summary(param: dict[str, Any]) -> dict[str, object]:
    return {
        "name": _string(param.get("name")),
        "required": bool(param.get("required")),
        "opts": [str(item) for item in param.get("opts") or []],
        "help": _string(param.get("help")),
    }


def _read_status_projection(root: Path) -> SiteStatusProjection:
    text = (root / "docs" / "STATUS.md").read_text(encoding="utf-8") if (root / "docs" / "STATUS.md").exists() else ""
    block = _section_block(text, "Current State")
    return SiteStatusProjection(
        current_version=_match_line(block, r"^Current version:\s*([0-9]+(?:\.[0-9]+){2})\.?"),
        current_verified_release=_match_line(
            block, r"^Current verified release:\s*v?([0-9]+\.[0-9]+\.[0-9]+)\.?"
        ),
        current_release_tag=_match_line(block, r"^Current release tag:\s*`?([^`\n]+?)`?\.?$"),
        concept_doi=_match_line(block, r"^Zenodo concept DOI:\s*`?([^`\n]+)`?\.?"),
        version_doi=_match_line(block, r"^Verified Zenodo version DOI:\s*`?([^`\n]+)`?\.?"),
        current_verified_main=_match_line(block, r"^Current verified main:\s*`?([0-9a-f]{7,40})`?"),
        latest_substantive_work=_match_line(block, r"^Latest substantive work:\s*(.+)$"),
        next_safe_step=_match_line(block, r"^Next safe step:\s*(.+)$"),
    )


def _read_roadmap_projection(root: Path) -> SiteRoadmapProjection:
    path = root / "docs" / "planning" / "PROJECT_DIRECTION.yaml"
    data: dict[str, Any] = {}
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        data = loaded if isinstance(loaded, dict) else {}
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    strategies = data.get("strategy") if isinstance(data.get("strategy"), list) else []
    roadmap = data.get("roadmap") if isinstance(data.get("roadmap"), list) else []
    return SiteRoadmapProjection(
        status=_string(meta.get("status")),
        updated_after_pr=str(meta.get("updated_after_pr") or ""),
        updated_after_pr_semantics=_string(meta.get("updated_after_pr_semantics")),
        updated_after_pr_current_main_claimed=(
            meta.get("updated_after_pr_current_main_claimed")
            if isinstance(meta.get("updated_after_pr_current_main_claimed"), bool)
            else None
        ),
        strategy_counts=_status_counts(strategies),
        roadmap_counts=_status_counts(roadmap),
    )


def _status_counts(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        status = _string(item.get("status")) or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _citation_value(root: Path, key: str) -> str:
    path = root / "CITATION.cff"
    if not path.exists():
        return ""
    return _match_line(path.read_text(encoding="utf-8"), rf"^{key}:\s*\"?([^\"\n]+)\"?")


def _section_block(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    return text[start:] if next_heading == -1 else text[start:next_heading]


def _match_line(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _current_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""
