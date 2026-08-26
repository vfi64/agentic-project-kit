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
DOCS_PAGES_FALLBACK_KIND = "agentic_project_kit_docs_pages_fallback"
DOCS_PAGES_FALLBACK_BUILD_COMMIT = "docs-pages-fallback"
B1_EVIDENCE_SOURCE = "docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json"


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
    repository_url: str
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
    lifecycle_rank: int | None = None

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["params"] = [dict(param) for param in self.params]
        return data


@dataclass(frozen=True)
class SiteCommandCatalog:
    entries: tuple[SiteCommandEntry, ...]

    @property
    def guided_entries(self) -> tuple[SiteCommandEntry, ...]:
        return _guided_lifecycle_entries(
            tuple(entry for entry in self.entries if entry.surface == "orchestrator")
        )

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
    workflow_projection: dict[str, object]
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
            "workflow_projection": self.workflow_projection,
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


@dataclass(frozen=True)
class DocsPagesFallbackResult:
    root: str
    docs_root: str
    site_subdir: str
    site_build: SiteBuildResult | None
    files: tuple[str, ...]
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers and self.site_build is not None and self.site_build.ok

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": DOCS_PAGES_FALLBACK_KIND,
            "root": self.root,
            "docs_root": self.docs_root,
            "site_subdir": self.site_subdir,
            "status": self.status,
            "files": list(self.files),
            "file_count": len(self.files),
            "blockers": list(self.blockers),
            "blocker_count": len(self.blockers),
            "site_build": self.site_build.as_dict() if self.site_build is not None else None,
        }


def collect_site_foundation_metadata(
    root: Path = Path("."),
    *,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
    status_projection: SiteStatusProjection | None = None,
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
    status_projection = status_projection or _read_status_projection(root)
    roadmap_projection = _read_roadmap_projection(root)
    workflow_projection = _build_workflow_projection(root, command_catalog)
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
            repository_url=_project_repository_url(project),
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
        workflow_projection=workflow_projection,
        claim_report=claim_report,
        blockers=tuple(blockers),
    )


def build_site(
    root: Path = Path("."),
    *,
    output_dir: Path | None = None,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
    status_projection: SiteStatusProjection | None = None,
) -> SiteBuildResult:
    root = root.resolve()
    output = (output_dir or root / "site" / "dist").resolve()
    report = collect_site_foundation_metadata(
        root,
        build_commit=build_commit,
        manifest=manifest,
        status_projection=status_projection,
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
    (output / "quickstart").mkdir(parents=True, exist_ok=True)
    (output / "workflows").mkdir(parents=True, exist_ok=True)

    index_html = render_index_html(root, report)
    quickstart_projection = _build_quickstart_projection(metadata, command_catalog)
    workflow_projection = report.workflow_projection
    site_json = json.dumps(
        {
            "schema_version": 1,
            "kind": SITE_KIND,
            "metadata": metadata.as_dict(),
            "command_catalog": command_catalog.as_dict(),
            "status_projection": report.status_projection.as_dict(),
            "roadmap_projection": report.roadmap_projection.as_dict(),
            "workflow_projection": workflow_projection,
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
    (output / "quickstart" / "quickstart.json").write_text(
        json.dumps(quickstart_projection, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "quickstart" / "index.html").write_text(
        render_quickstart_html(root, metadata, quickstart_projection),
        encoding="utf-8",
    )
    (output / "workflows" / "workflows.json").write_text(
        json.dumps(workflow_projection, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "workflows" / "index.html").write_text(
        render_workflows_html(root, metadata, workflow_projection),
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


def build_docs_pages_fallback(
    root: Path = Path("."),
    *,
    site_subdir: str = "site",
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> DocsPagesFallbackResult:
    root = root.resolve()
    docs_root = root / "docs"
    blockers = _docs_pages_fallback_blockers(site_subdir)
    site_build: SiteBuildResult | None = None
    files: tuple[str, ...] = ()
    if not blockers:
        docs_root.mkdir(parents=True, exist_ok=True)
        site_build = build_site(
            root,
            output_dir=docs_root / site_subdir,
            build_commit=build_commit or DOCS_PAGES_FALLBACK_BUILD_COMMIT,
            manifest=manifest,
            status_projection=_docs_pages_fallback_status_projection(root),
        )
        if site_build.ok:
            (docs_root / "index.html").write_text(
                _render_docs_pages_index(site_subdir),
                encoding="utf-8",
            )
            (docs_root / ".nojekyll").write_text(
                "Generated marker: serve docs/ as static GitHub Pages content.\n",
                encoding="utf-8",
            )
            files = tuple(
                sorted((".nojekyll", "index.html", *(f"{site_subdir}/{path}" for path in site_build.files)))
            )
        else:
            blockers.extend(site_build.report.blockers)

    return DocsPagesFallbackResult(
        root=root.as_posix(),
        docs_root=docs_root.as_posix(),
        site_subdir=site_subdir,
        site_build=site_build,
        files=files,
        blockers=tuple(blockers),
    )


def _docs_pages_fallback_blockers(site_subdir: str) -> list[str]:
    if not site_subdir or site_subdir in {".", ".."}:
        return ["docs Pages site subdir must be a named child directory"]
    if "/" in site_subdir or "\\" in site_subdir:
        return ["docs Pages site subdir must not contain path separators"]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", site_subdir):
        return ["docs Pages site subdir contains unsupported characters"]
    return []


def _render_docs_pages_index(site_subdir: str) -> str:
    target = f"{site_subdir}/index.html"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="0; url={target}">
    <link rel="canonical" href="{target}">
    <title>{PRODUCT_NAME}</title>
  </head>
  <body>
    <main>
      <p><a href="{target}">Open the generated website</a>.</p>
    </main>
  </body>
</html>
"""


def _docs_pages_fallback_status_projection(root: Path) -> SiteStatusProjection:
    current = _read_status_projection(root)
    return SiteStatusProjection(
        current_version=current.current_version,
        current_verified_release=current.current_verified_release,
        current_release_tag=current.current_release_tag,
        concept_doi=current.concept_doi,
        version_doi=current.version_doi,
        current_verified_main="See docs/STATUS.md",
        latest_substantive_work="See docs/STATUS.md for current repository state.",
        next_safe_step="See docs/handoff/CURRENT_HANDOFF.md for current handoff guidance.",
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
        "repository_url": escape(metadata.repository_url or "#"),
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
        "guided_command_items": _command_summary_items(
            _guided_lifecycle_entries(command_catalog.guided_entries),
            limit=8,
        ),
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
        "workflow_mode_count": str(len(report.workflow_projection.get("modes", []))),
        "brownfield_cycle_count": escape(
            _projection_value(report.workflow_projection, "brownfield.real_cycles", "not recorded")
        ),
        "brownfield_status": escape(
            _projection_value(report.workflow_projection, "brownfield.status", "not recorded")
        ),
    }
    return template.safe_substitute(values).rstrip() + "\n"


def render_workflows_html(
    root: Path,
    metadata: SiteFoundationMetadata,
    projection: dict[str, object],
) -> str:
    template_path = root / "site" / "templates" / "workflows.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    values = {
        "product_name": escape(metadata.product_name),
        "package_version": escape(metadata.package_version),
        "manifest_sha": escape(metadata.manifest_sha),
        "mode_cards": _workflow_mode_cards(projection),
        "core_workflow_items": _workflow_step_items(projection),
        "boundary_items": _workflow_boundary_items(projection),
        "brownfield_items": _brownfield_fact_items(projection),
        "brownfield_status": escape(_projection_value(projection, "brownfield.status", "not recorded")),
        "brownfield_source": escape(_projection_value(projection, "brownfield.source", "")),
        "brownfield_evidence_type": escape(
            _projection_value(projection, "brownfield.rule_ack_evidence_type", "not recorded")
        ),
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _guided_lifecycle_entries(
    entries: tuple[SiteCommandEntry, ...],
) -> tuple[SiteCommandEntry, ...]:
    return tuple(sorted(entries, key=_guided_lifecycle_sort_key))


def _guided_lifecycle_sort_key(entry: SiteCommandEntry) -> tuple[int, int, str]:
    if entry.lifecycle_rank is not None:
        return (entry.lifecycle_rank, 0, entry.qualified_name)
    qualified = entry.qualified_name
    path = qualified.removeprefix("agentic-kit ").split()
    group = path[0] if path else ""
    leaf = path[-1] if path else ""
    group_rank = {
        "workspace": 100,
        "work": 200,
        "workflow": 300,
        "transfer": 400,
        "release": 500,
        "docs": 600,
        "dpa": 700,
    }.get(group, 800)
    leaf_rank = {
        "adopt": 0,
        "init": 1,
        "upgrade": 2,
        "dpa-intake": 3,
        "remove": 90,
        "start": 0,
        "finish": 1,
        "recover": 2,
        "remote-work-start": 0,
        "remote-next": 1,
        "pr-create-complete": 2,
        "pr-complete": 3,
        "pr-closeout-complete": 4,
        "post-merge-settle": 5,
        "post-merge-complete": 6,
        "chat-switch-complete": 7,
        "admin-refresh-pr": 8,
        "prepare": 0,
        "ready": 1,
        "release-prep": 2,
        "release-publish": 3,
        "post-release-doi-closeout": 4,
        "sweep": 0,
        "final-closeout-check": 0,
        "artifact-gc": 0,
    }.get(leaf, 50)
    return (group_rank, leaf_rank, qualified)


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


def _build_quickstart_projection(
    metadata: SiteFoundationMetadata,
    command_catalog: SiteCommandCatalog,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "site_quickstart_projection",
        "package": {
            "name": metadata.package_name,
            "version": metadata.package_version,
            "requires_python": metadata.requires_python,
            "repository_url": metadata.repository_url,
        },
        "docs": [
            {
                "label": "First-chat onboarding",
                "path": "docs/ONBOARDING.md",
            },
            {
                "label": "Brownfield external repository guide",
                "path": "docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md",
            },
            {
                "label": "Command reference",
                "path": "docs/reference/AGENTIC_KIT_COMMANDS.md",
            },
            {
                "label": "Test gates",
                "path": "docs/TEST_GATES.md",
            },
        ],
        "flows": [
            {
                "id": "new-repository",
                "title": "New repository",
                "commands": _quickstart_commands(
                    command_catalog,
                    ("agentic-kit init", "agentic-kit check", "agentic-kit doctor"),
                ),
            },
            {
                "id": "existing-repository",
                "title": "Existing repository",
                "commands": _quickstart_commands(
                    command_catalog,
                    (
                        "agentic-kit workspace dpa-intake",
                        "agentic-kit workspace adopt",
                        "agentic-kit workspace init",
                        "agentic-kit check-docs",
                        "agentic-kit check",
                        "agentic-kit doctor",
                        "agentic-kit transfer chat-switch-complete",
                        "agentic-kit workspace remove",
                    ),
                ),
            },
        ],
    }


def _quickstart_commands(
    command_catalog: SiteCommandCatalog,
    names: tuple[str, ...],
) -> list[dict[str, object]]:
    entries = {entry.qualified_name: entry for entry in command_catalog.entries}
    rows: list[dict[str, object]] = []
    for name in names:
        entry = entries.get(name)
        rows.append(
            {
                "qualified_name": name,
                "manifest_present": entry is not None,
                "surface": entry.surface if entry is not None else "",
                "safety": entry.safety if entry is not None else "",
                "dry_run_available": entry.dry_run_available if entry is not None else False,
                "when_to_use": entry.when_to_use if entry is not None else "",
            }
        )
    return rows


def _build_workflow_projection(
    root: Path,
    command_catalog: SiteCommandCatalog | None,
) -> dict[str, object]:
    command_catalog = command_catalog or SiteCommandCatalog(entries=())
    brownfield = _read_b1_evidence(root)
    return {
        "schema_version": 1,
        "kind": "site_workflow_projection",
        "source": "site_generator.py",
        "modes": [
            {
                "id": "file-transfer",
                "title": "File Transfer",
                "maturity": "primary web-LLM path",
                "best_for": "Web or hosted LLMs without direct terminal or repository access.",
                "summary": (
                    "The human and the LLM exchange bounded Kit transfer files while the "
                    "repository remains the source of truth."
                ),
                "commands": _quickstart_commands(
                    command_catalog,
                    (
                        "agentic-kit transfer read-user-task",
                        "agentic-kit transfer submit-user-task",
                        "agentic-kit transfer remote-next",
                        "agentic-kit transfer chat-switch-complete",
                    ),
                ),
            },
            {
                "id": "copy-paste",
                "title": "Copy and Paste",
                "maturity": "manual fallback",
                "best_for": "Small manual web-LLM sessions where a file-transfer carrier is not needed.",
                "summary": (
                    "The LLM proposes a bounded terminal block, the human runs it, and the "
                    "important output is returned to the conversation."
                ),
                "commands": _quickstart_commands(
                    command_catalog,
                    (
                        "agentic-kit workflow request",
                        "agentic-kit workflow run",
                        "agentic-kit transfer log-header",
                        "agentic-kit transfer chat-switch-complete",
                    ),
                ),
            },
            {
                "id": "agent-direct",
                "title": "Agent Direct",
                "maturity": "executor-controlled workspace path",
                "best_for": "Executors with controlled repository and terminal access.",
                "summary": (
                    "The executor can run Kit commands directly, but repository governance, "
                    "evidence, safety classes and handoff state remain separate from the agent."
                ),
                "commands": _quickstart_commands(
                    command_catalog,
                    (
                        "agentic-kit command-for",
                        "agentic-kit transfer remote-work-start",
                        "agentic-kit transfer pr-create-complete",
                        "agentic-kit transfer protected-diff-plan",
                        "agentic-kit transfer chat-switch-complete",
                    ),
                ),
            },
            {
                "id": "gui",
                "title": "GUI",
                "maturity": "experimental early surface",
                "best_for": "Local operator visibility over manifest-backed actions and readiness checks.",
                "summary": (
                    "The GUI entry point is available, but full parity with every CLI command "
                    "is not claimed. The manifest remains the command authority."
                ),
                "commands": _quickstart_commands(
                    command_catalog,
                    (
                        "agentic-kit gui-readiness-gate",
                        "agentic-kit cockpit run",
                        "agentic-kit cockpit select",
                    ),
                ),
            },
        ],
        "core_workflow": [
            {
                "title": "Select the interaction mode",
                "detail": "Choose File Transfer, Copy and Paste, Agent Direct, or the experimental GUI surface.",
            },
            {
                "title": "Inspect before mutation",
                "detail": "Use read-only or dry-run commands where available and keep target-owned decisions explicit.",
            },
            {
                "title": "Run a bounded slice",
                "detail": "Make one coherent change on a branch, record gates and evidence, and keep PR review visible.",
            },
            {
                "title": "Close the handoff",
                "detail": "Generate the successor package so another session or executor can continue from repository state.",
            },
        ],
        "boundaries": [
            "Git records history and diffs; the Kit adds machine-readable operational state and handoff contracts.",
            "GitHub PRs coordinate review; the Kit wraps PR lifecycle checks when evidence is available.",
            "CI validates configured checks; the Kit records when remote target-CI is absent or not claimed.",
            "AGENTS.md guides an executor; the Kit keeps durable governance, evidence and command metadata in the repository.",
            "The executor is replaceable; repository governance persists.",
            "The Kit itself makes no LLM API calls and does not require an LLM API; executor services may have their own costs.",
            "YAML and JSON state are versioned, diffable and reviewable, but they create file volume and projection-refresh work.",
        ],
        "brownfield": brownfield,
    }


def _read_b1_evidence(root: Path) -> dict[str, object]:
    path = root / B1_EVIDENCE_SOURCE
    if not path.exists():
        return {
            "source": B1_EVIDENCE_SOURCE,
            "status": "not_recorded",
            "real_cycles": "not recorded",
            "merge_boundary_cycles": "not recorded",
            "summary": "No consolidated B1 evidence report is currently available.",
        }
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "source": B1_EVIDENCE_SOURCE,
            "status": "invalid",
            "real_cycles": "not recorded",
            "merge_boundary_cycles": "not recorded",
            "summary": f"B1 evidence JSON is not parseable: {exc}",
        }
    data = loaded if isinstance(loaded, dict) else {}
    cycles = data.get("cycle_totals") if isinstance(data.get("cycle_totals"), dict) else {}
    seams = data.get("seam_metric") if isinstance(data.get("seam_metric"), dict) else {}
    tests = data.get("tests") if isinstance(data.get("tests"), dict) else {}
    defects = data.get("defects") if isinstance(data.get("defects"), list) else []
    return {
        "source": B1_EVIDENCE_SOURCE,
        "status": _string(data.get("status")),
        "real_cycles": cycles.get("real_cycles", ""),
        "merge_boundary_cycles": cycles.get("merge_boundary_cycles", ""),
        "administrative_refresh_prs": cycles.get("administrative_refresh_prs", ""),
        "admin_refresh_rate": cycles.get("admin_refresh_rate", ""),
        "observable_admin_refresh_share": _string(cycles.get("observable_admin_refresh_share")),
        "seam_metric_name": _string(seams.get("definition")),
        "legacy_seams_start": seams.get("start", ""),
        "legacy_seams_end": seams.get("end", ""),
        "full_suite_min": tests.get("full_suite_min", ""),
        "full_suite_max": tests.get("full_suite_max", ""),
        "cycle_005_test_boundary": _string(tests.get("cycle_005_test_boundary")),
        "defect_count": len(defects),
        "rule_ack_evidence_type": _string(data.get("rule_ack_evidence_type")),
        "summary": _string(data.get("public_summary")),
        "generalization_boundary": _string(data.get("generalization_boundary")),
    }


def _workflow_mode_cards(projection: dict[str, object]) -> str:
    modes = projection.get("modes")
    if not isinstance(modes, list) or not modes:
        return "        <article class=\"panel\"><p>No workflow modes are currently projected.</p></article>"
    cards = []
    for mode in modes:
        if not isinstance(mode, dict):
            continue
        cards.append(
            "        <article class=\"panel workflow-card\" id=\"mode-"
            f"{escape(_string(mode.get('id')))}\">"
            f"<p class=\"eyebrow\">{escape(_string(mode.get('maturity')))}</p>"
            f"<h2>{escape(_string(mode.get('title')))}</h2>"
            f"<p>{escape(_string(mode.get('summary')))}</p>"
            f"<p><strong>Best for:</strong> {escape(_string(mode.get('best_for')))}</p>"
            "<ul class=\"summary-list command-flow\">"
            f"\n{_mode_command_items(mode)}\n"
            "</ul>"
            "</article>"
        )
    return "\n".join(cards)


def _mode_command_items(mode: dict[str, object]) -> str:
    commands = mode.get("commands")
    if not isinstance(commands, list) or not commands:
        return "          <li>No manifest-backed commands are projected for this mode.</li>"
    rows = []
    for command in commands:
        if not isinstance(command, dict):
            continue
        name = _string(command.get("qualified_name"))
        metadata = " · ".join(
            part
            for part in (
                _string(command.get("surface")),
                _string(command.get("safety")),
                "dry-run" if command.get("dry_run_available") is True else "",
            )
            if part
        )
        rows.append(
            "          <li>"
            f"<a href=\"../commands/index.html\"><code>{escape(name)}</code></a>"
            f"<span>{escape(_string(command.get('when_to_use')) or 'Manifest metadata unavailable.')}</span>"
            f"<small>{escape(metadata or 'not in manifest')}</small>"
            "</li>"
        )
    return "\n".join(rows)


def _workflow_step_items(projection: dict[str, object]) -> str:
    steps = projection.get("core_workflow")
    if not isinstance(steps, list) or not steps:
        return "          <li>No core workflow is currently projected.</li>"
    rows = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        rows.append(
            "          <li>"
            f"<strong>{escape(_string(step.get('title')))}</strong>"
            f"<span>{escape(_string(step.get('detail')))}</span>"
            "</li>"
        )
    return "\n".join(rows)


def _workflow_boundary_items(projection: dict[str, object]) -> str:
    boundaries = projection.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        return "          <li>No boundaries are currently projected.</li>"
    return "\n".join(f"          <li><span>{escape(str(item))}</span></li>" for item in boundaries)


def _brownfield_fact_items(projection: dict[str, object]) -> str:
    brownfield = projection.get("brownfield")
    if not isinstance(brownfield, dict):
        return "          <li>No Brownfield evidence is currently projected.</li>"
    facts = (
        ("Status", brownfield.get("status")),
        ("Real cycles", brownfield.get("real_cycles")),
        ("Merge-boundary cycles", brownfield.get("merge_boundary_cycles")),
        ("Administrative refresh PRs", brownfield.get("administrative_refresh_prs")),
        ("Legacy seams", f"{brownfield.get('legacy_seams_start')} to {brownfield.get('legacy_seams_end')}"),
        ("Full-suite runs", f"{brownfield.get('full_suite_min')} to {brownfield.get('full_suite_max')} tests"),
        ("Cycle 005", brownfield.get("cycle_005_test_boundary")),
        ("Core defects found", brownfield.get("defect_count")),
    )
    rows = []
    for label, value in facts:
        rows.append(
            "          <li>"
            f"<strong>{escape(str(label))}</strong>"
            f"<span>{escape(_display_value(value))}</span>"
            "</li>"
        )
    return "\n".join(rows)


def _display_value(value: object) -> str:
    text = "" if value is None else str(value)
    if not text or text == "None to None" or text == "None to None tests":
        return "not recorded"
    return text


def _projection_value(projection: dict[str, object], dotted_path: str, default: str) -> str:
    current: object = projection
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return str(current) if current not in (None, "") else default


def render_quickstart_html(
    root: Path,
    metadata: SiteFoundationMetadata,
    projection: dict[str, object],
) -> str:
    template_path = root / "site" / "templates" / "quickstart.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    values = {
        "product_name": escape(metadata.product_name),
        "package_name": escape(metadata.package_name),
        "package_version": escape(metadata.package_version),
        "requires_python": escape(metadata.requires_python),
        "repository_url": escape(metadata.repository_url or "#"),
        "new_repo_command_items": _quickstart_flow_command_items(projection, "new-repository"),
        "existing_repo_command_items": _quickstart_flow_command_items(projection, "existing-repository"),
        "docs_link_items": _quickstart_docs_link_items(metadata, projection),
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _quickstart_flow_command_items(projection: dict[str, object], flow_id: str) -> str:
    flows = projection.get("flows")
    if not isinstance(flows, list):
        return "          <li>No command flow is currently projected.</li>"
    flow = next((item for item in flows if isinstance(item, dict) and item.get("id") == flow_id), None)
    if not isinstance(flow, dict):
        return "          <li>No command flow is currently projected.</li>"
    commands = flow.get("commands")
    if not isinstance(commands, list) or not commands:
        return "          <li>No commands are currently projected.</li>"
    rows = []
    for command in commands:
        if not isinstance(command, dict):
            continue
        name = _string(command.get("qualified_name"))
        when_to_use = _string(command.get("when_to_use")) or "Command metadata is not projected."
        metadata = " · ".join(
            part
            for part in (
                _string(command.get("surface")),
                _string(command.get("safety")),
                "dry-run" if command.get("dry_run_available") is True else "",
            )
            if part
        )
        rows.append(
            "          <li>"
            f"<code>{escape(name)}</code>"
            f"<span>{escape(when_to_use)}</span>"
            f"<small>{escape(metadata or 'manifest metadata unavailable')}</small>"
            "</li>"
        )
    return "\n".join(rows) if rows else "          <li>No commands are currently projected.</li>"


def _quickstart_docs_link_items(
    metadata: SiteFoundationMetadata,
    projection: dict[str, object],
) -> str:
    docs = projection.get("docs")
    if not isinstance(docs, list):
        return "          <li>No documentation links are currently projected.</li>"
    rows = []
    repository = metadata.repository_url.rstrip("/")
    for item in docs:
        if not isinstance(item, dict):
            continue
        label = _string(item.get("label"))
        path = _string(item.get("path"))
        href = f"{repository}/blob/main/{path}" if repository and path else "#"
        rows.append(f'          <li><a href="{escape(href)}">{escape(label or path)}</a></li>')
    return "\n".join(rows) if rows else "          <li>No documentation links are currently projected.</li>"


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
    params = "; ".join(_format_param(param) for param in entry.params) or "none"
    command_text = " ".join(
        (
            entry.qualified_name,
            entry.group,
            entry.surface,
            entry.safety,
            entry.when_to_use,
            entry.help,
            params,
        )
    ).lower()
    return (
        "          <tr"
        f" data-command-text=\"{escape(command_text, quote=True)}\""
        f" data-safety=\"{escape(entry.safety, quote=True)}\""
        f" data-surface=\"{escape(entry.surface, quote=True)}\">"
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


def _format_param(param: dict[str, object]) -> str:
    name = _string(param.get("name")) or "<unnamed>"
    opts = param.get("opts")
    opts_text = "/".join(str(item) for item in opts) if isinstance(opts, list) else ""
    default = param.get("default")
    default_text = "" if default in (None, "") else f" default={default}"
    required = " required" if param.get("required") is True else ""
    return " ".join(part for part in (name, opts_text, required, default_text) if part).strip()


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
                lifecycle_rank=(
                    command.get("lifecycle_rank")
                    if isinstance(command.get("lifecycle_rank"), int)
                    else None
                ),
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
        "default": param.get("default"),
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


def _project_repository_url(project: dict[str, Any]) -> str:
    urls = project.get("urls")
    if not isinstance(urls, dict):
        return ""
    for key in ("Repository", "Source", "Source Code", "Homepage"):
        value = urls.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


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
