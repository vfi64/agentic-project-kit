from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.workspace import load_workspace

DPA_REPO_ADOPTION_MODEL = "dpa-repo-adoption-assessment-v1"
DPA_REPO_ADOPTION_KIND = "dpa_repo_adoption_assessment"
DPA_CAPABLE_STATUS = "DPA_CAPABLE_WITH_FRESH_PER_REPO_ASSESSMENT"
READY_STATUS = "READY_FOR_DPA_REPO_ADOPTION_ADJUDICATION"
BLOCKED_STATUS = "BLOCKED_FOR_DPA_REPO_ADOPTION"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")

HIGH_AUTHORITY_CLASSIFICATIONS = frozenset(
    {
        "agent_instruction",
        "architecture_authority",
        "ci_workflow",
        "command_updated_state",
        "dpa_authority",
        "generated_projection",
        "handoff_authority",
        "planning_authority",
        "release_state",
        "status_authority",
        "workspace_manifest",
    }
)

SCAN_SUFFIXES = frozenset(
    {
        ".cff",
        ".json",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
    }
)

TOP_LEVEL_CANDIDATES = frozenset(
    {
        "AGENTS.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "README.md",
        "codemeta.json",
        "package.json",
        "pyproject.toml",
    }
)

EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    }
)


@dataclass(frozen=True)
class DpaRepoAdoptionFinding:
    code: str
    message: str
    path: str
    severity: str = "blocker"

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class DpaRepoAdoptionSurface:
    path: str
    classification: str
    document_form: str
    source_authority: str
    writer: str
    reader: str
    target_identity: str
    dpa_600_evidence: str
    dpa_700_evidence: str
    recommendation: str
    maintainer_adjudication_required: bool
    generated_or_command_updated: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "classification": self.classification,
            "document_form": self.document_form,
            "source_authority": self.source_authority,
            "writer": self.writer,
            "reader": self.reader,
            "target_identity": self.target_identity,
            "dpa_600_evidence": self.dpa_600_evidence,
            "dpa_700_evidence": self.dpa_700_evidence,
            "recommendation": self.recommendation,
            "maintainer_adjudication_required": self.maintainer_adjudication_required,
            "generated_or_command_updated": self.generated_or_command_updated,
        }


@dataclass(frozen=True)
class DpaRepoAdoptionAssessment:
    root: str
    current_validation_ref: str
    surfaces: tuple[DpaRepoAdoptionSurface, ...]
    findings: tuple[DpaRepoAdoptionFinding, ...]

    @property
    def blocker_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "blocker")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

    @property
    def high_authority_surface_count(self) -> int:
        return sum(
            1 for surface in self.surfaces if surface.classification in HIGH_AUTHORITY_CLASSIFICATIONS
        )

    @property
    def generated_or_command_updated_surface_count(self) -> int:
        return sum(1 for surface in self.surfaces if surface.generated_or_command_updated)

    @property
    def manual_preservation_surface_count(self) -> int:
        return sum(1 for surface in self.surfaces if surface.maintainer_adjudication_required)

    @property
    def result_status(self) -> str:
        return BLOCKED_STATUS if self.blocker_count else READY_STATUS

    @property
    def ok(self) -> bool:
        return self.blocker_count == 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": DPA_REPO_ADOPTION_KIND,
            "assessment_model": DPA_REPO_ADOPTION_MODEL,
            "result_status": self.result_status,
            "root": self.root,
            "current_validation_ref": self.current_validation_ref,
            "surface_count": len(self.surfaces),
            "high_authority_surface_count": self.high_authority_surface_count,
            "manual_preservation_surface_count": self.manual_preservation_surface_count,
            "generated_or_command_updated_surface_count": (
                self.generated_or_command_updated_surface_count
            ),
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "findings": [finding.as_dict() for finding in self.findings],
            "surfaces": [surface.as_dict() for surface in self.surfaces],
            "foreign_repo_management": {
                "status": DPA_CAPABLE_STATUS,
                "fresh_per_repo_inventory_recorded": True,
                "source_authority_inventory_recorded": True,
                "target_identity_inventory_recorded": True,
                "dpa_600_700_assessment_recorded": True,
                "requires_maintainer_authorized_scope": True,
                "automatic_external_repo_conformance_claimed": False,
            },
            "claims": {
                "kit_wide_dpa_conformance_claimed": False,
                "stable_dpa_claimed": False,
                "external_repo_conformance_claimed": False,
                "automatic_migration_performed": False,
                "production_mutation_performed": False,
            },
        }


def evaluate_dpa_repo_adoption_assessment(
    root: Path | str = ".",
    *,
    validation_ref: str | None = None,
) -> DpaRepoAdoptionAssessment:
    base = Path(root).resolve()
    findings: list[DpaRepoAdoptionFinding] = []
    if not base.exists() or not base.is_dir():
        findings.append(
            DpaRepoAdoptionFinding(
                code="root-not-directory",
                message="target repository root must be an existing directory",
                path=base.as_posix(),
            )
        )
        return DpaRepoAdoptionAssessment(
            root=base.as_posix(),
            current_validation_ref="UNKNOWN",
            surfaces=(),
            findings=tuple(findings),
        )

    current_ref = _current_validation_ref(base, validation_ref, findings)
    _agentic_collision_findings(base, findings)
    surfaces = tuple(_classify_surface(path, base) for path in _candidate_paths(base))
    return DpaRepoAdoptionAssessment(
        root=base.as_posix(),
        current_validation_ref=current_ref,
        surfaces=surfaces,
        findings=tuple(findings),
    )


def render_dpa_repo_adoption_assessment(result: DpaRepoAdoptionAssessment) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_REPO_ADOPTION_ASSESSMENT",
        f"STATUS={payload['result_status']}",
        f"ROOT={payload['root']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"SURFACES={payload['surface_count']}",
        f"HIGH_AUTHORITY_SURFACES={payload['high_authority_surface_count']}",
        f"MANUAL_PRESERVATION_SURFACES={payload['manual_preservation_surface_count']}",
        "GENERATED_OR_COMMAND_UPDATED_SURFACES="
        f"{payload['generated_or_command_updated_surface_count']}",
        f"BLOCKERS={payload['blocker_count']}",
        f"WARNINGS={payload['warning_count']}",
        f"FOREIGN_REPO_STATUS={payload['foreign_repo_management']['status']}",
        "EXTERNAL_REPO_CONFORMANCE_CLAIMED="
        f"{str(payload['claims']['external_repo_conformance_claimed']).lower()}",
        "AUTOMATIC_MIGRATION_PERFORMED="
        f"{str(payload['claims']['automatic_migration_performed']).lower()}",
        "NEXT=maintainer-adjudicate bounded scope before migration, strict gates, or conformance claims",
    ]
    for classification, count in _classification_counts(result.surfaces).items():
        lines.append(f"CLASSIFICATION={classification}|count={count}")
    for surface in result.surfaces[:50]:
        lines.append(
            "SURFACE="
            f"{surface.path}|class={surface.classification}|form={surface.document_form}|"
            f"dpa600={surface.dpa_600_evidence}|dpa700={surface.dpa_700_evidence}"
        )
    if len(result.surfaces) > 50:
        lines.append(f"SURFACE_TRUNCATED={len(result.surfaces) - 50}")
    for finding in result.findings:
        lines.append(
            f"FINDING={finding.severity}|{finding.code}|path={finding.path}|{finding.message}"
        )
    return "\n".join(lines) + "\n"


def write_dpa_repo_adoption_assessment_json(
    result: DpaRepoAdoptionAssessment,
    root: Path | str,
    output: Path | str,
    *,
    execute: bool,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output_path = _resolve_under_root(base, output)
    try:
        relative = output_path.relative_to(base)
    except ValueError:
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_repository_root",
            "output_path": output_path.as_posix(),
            "written": False,
        }
    evidence_root = _evidence_output_root(base)
    if evidence_root not in (output_path, *output_path.parents):
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_dpa_assessment_evidence_root",
            "output_path": relative.as_posix(),
            "written": False,
        }
    rendered = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
    changed = True
    if output_path.exists():
        changed = output_path.read_text(encoding="utf-8") != rendered
    if execute:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    return {
        "result_status": "PASS",
        "output_path": relative.as_posix(),
        "changed": changed,
        "written": bool(execute),
    }


def _candidate_paths(root: Path) -> tuple[Path, ...]:
    candidates: set[Path] = set()
    for relative in TOP_LEVEL_CANDIDATES:
        path = root / relative
        if path.is_file() and not path.is_symlink():
            candidates.add(path)
    for directory in ("docs", ".agentic", ".github/workflows"):
        base = root / directory
        if not base.exists():
            continue
        if base.is_file() and _is_candidate_file(base):
            candidates.add(base)
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink() or not _is_candidate_file(path):
                continue
            if _is_excluded(path, root):
                continue
            candidates.add(path)
    return tuple(sorted(candidates, key=lambda path: path.relative_to(root).as_posix()))


def _is_candidate_file(path: Path) -> bool:
    return path.name in TOP_LEVEL_CANDIDATES or path.suffix.lower() in SCAN_SUFFIXES


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in parts) or parts[:2] == (".agentic", "tmp")


def _classify_surface(path: Path, root: Path) -> DpaRepoAdoptionSurface:
    relative = path.relative_to(root).as_posix()
    classification = _classification(relative)
    document_form = _document_form(classification, path)
    generated = classification in {"command_updated_state", "generated_projection"}
    return DpaRepoAdoptionSurface(
        path=relative,
        classification=classification,
        document_form=document_form,
        source_authority=_source_authority(classification),
        writer=_writer(classification),
        reader=_reader(classification),
        target_identity=f"repo:{relative}",
        dpa_600_evidence=_dpa_600_evidence(classification),
        dpa_700_evidence=_dpa_700_evidence(classification),
        recommendation=_recommendation(classification),
        maintainer_adjudication_required=not generated,
        generated_or_command_updated=generated,
    )


def _classification(relative: str) -> str:
    if relative == ".agentic/config.yaml":
        return "workspace_manifest"
    if relative in {"docs/STATUS.md", ".agentic/state/status.md"}:
        return "status_authority"
    if relative in {"docs/handoff/CURRENT_HANDOFF.md", ".agentic/state/handoff/README.md"}:
        return "handoff_authority"
    if relative.startswith(".agentic/state/handoff/packages/"):
        return "generated_projection"
    if relative.startswith(".agentic/state/handoff/") and relative.endswith((".json", ".yaml")):
        return "generated_projection"
    if relative.startswith("docs/reports/handoff-packages/"):
        return "generated_projection"
    if relative.startswith("docs/reports/terminal/") or relative.startswith("docs/reports/transfer_runs/"):
        return "generated_projection"
    if relative.startswith(".agentic/state/") or relative.startswith(".agentic/registries/"):
        return "command_updated_state"
    if relative.startswith(".github/workflows/"):
        return "ci_workflow"
    if relative == "AGENTS.md":
        return "agent_instruction"
    if relative in {"CHANGELOG.md", "CITATION.cff", "codemeta.json"}:
        return "release_state"
    if relative.startswith("docs/architecture/dpa/"):
        return "dpa_authority"
    if relative.startswith("docs/architecture/"):
        return "architecture_authority"
    if relative.startswith("docs/planning/"):
        return "planning_authority"
    if relative == "README.md":
        return "onboarding_document"
    if relative in {"pyproject.toml", "package.json"}:
        return "project_config"
    if relative.startswith("docs/"):
        return "manual_document"
    return "structured_or_manual_document"


def _document_form(classification: str, path: Path) -> str:
    if classification == "generated_projection":
        return "generated_projection"
    if classification == "command_updated_state":
        return "command_updated_state"
    if classification == "status_authority":
        return "status_authority_document"
    if classification == "handoff_authority":
        return "handoff_authority_document"
    if classification == "ci_workflow":
        return "structured_workflow"
    if classification in {"workspace_manifest", "project_config", "release_state"}:
        return "structured_config" if path.suffix.lower() != ".md" else "manual_document"
    if classification.endswith("_authority") or classification == "agent_instruction":
        return "authority_document"
    if path.suffix.lower() == ".md":
        return "manual_document"
    return "structured_config"


def _source_authority(classification: str) -> str:
    if classification == "generated_projection":
        return "owning generator command"
    if classification == "command_updated_state":
        return "agentic-kit command"
    if classification == "workspace_manifest":
        return "workspace manifest owner"
    if classification == "ci_workflow":
        return "repository CI owner"
    return "maintainer"


def _writer(classification: str) -> str:
    if classification == "generated_projection":
        return "owning generator command only"
    if classification == "command_updated_state":
        return "agentic-kit command only"
    if classification == "ci_workflow":
        return "reviewed CI workflow change"
    return "human or coding agent through reviewed change"


def _reader(classification: str) -> str:
    if classification == "ci_workflow":
        return "GitHub Actions"
    if classification == "workspace_manifest":
        return "agentic-kit workspace loader"
    if classification in {"status_authority", "handoff_authority"}:
        return "maintainers and coding agents"
    if classification == "generated_projection":
        return "handoff workflow and coding agents"
    return "maintainers, users, and coding agents"


def _dpa_600_evidence(classification: str) -> str:
    if classification in {"generated_projection", "command_updated_state", "workspace_manifest"}:
        return "serialize with owning command, workspace lock, exact ref, and PR head"
    if classification == "ci_workflow":
        return "serialize branch/PR workflow changes with exact head and rollback plan"
    return "serialize by branch, review, exact ref, and no concurrent authority edit"


def _dpa_700_evidence(classification: str) -> str:
    if classification == "generated_projection":
        return "no manual migration; regenerate from owning source"
    if classification in {"command_updated_state", "workspace_manifest"}:
        return "command-only migration or no-migration adjudication"
    if classification == "ci_workflow":
        return "bounded rollout with rollback or no-migration adjudication"
    return "manual preservation adjudication before migration"


def _recommendation(classification: str) -> str:
    if classification == "generated_projection":
        return "preserve generator/source authority; do not patch generated output manually"
    if classification == "command_updated_state":
        return "use owning agentic-kit command for updates"
    if classification in {"status_authority", "handoff_authority"}:
        return "require maintainer-adjudicated preservation before adoption"
    if classification == "ci_workflow":
        return "adopt only through bounded workflow rollout with rollback"
    return "review as manual source during per-repo DPA scope adjudication"


def _classification_counts(
    surfaces: tuple[DpaRepoAdoptionSurface, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for surface in surfaces:
        counts[surface.classification] = counts.get(surface.classification, 0) + 1
    return dict(sorted(counts.items()))


def _current_validation_ref(
    root: Path,
    validation_ref: str | None,
    findings: list[DpaRepoAdoptionFinding],
) -> str:
    explicit = validation_ref.strip() if isinstance(validation_ref, str) else ""
    if explicit:
        return explicit
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip()
    findings.append(
        DpaRepoAdoptionFinding(
            code="exact-ref-missing",
            message="DPA repo adoption assessment requires an exact current validation ref",
            path=".",
        )
    )
    return "UNKNOWN"


def _agentic_collision_findings(root: Path, findings: list[DpaRepoAdoptionFinding]) -> None:
    agentic = root / ".agentic"
    manifest = agentic / "config.yaml"
    if agentic.exists() and not manifest.exists():
        findings.append(
            DpaRepoAdoptionFinding(
                code="foreign-agentic-directory",
                message="foreign .agentic/ directory requires maintainer diagnosis before init/adoption",
                path=".agentic",
            )
        )


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _evidence_output_root(root: Path) -> Path:
    try:
        workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    except RuntimeError:
        return root.joinpath("docs", "architecture", "evidence", "dpa", "assessment")
    return workspace.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()
