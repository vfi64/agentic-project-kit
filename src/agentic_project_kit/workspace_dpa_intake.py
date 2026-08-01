from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from agentic_project_kit.dpa_repo_adoption_assessment import (
    DpaRepoAdoptionAssessment,
    DpaRepoAdoptionSurface,
    dpa_repo_adoption_evidence_output_root,
    evaluate_dpa_repo_adoption_assessment,
)
from agentic_project_kit.workspace_adopt import (
    WorkspaceAdoptReport,
    analyze_workspace_adoption,
)

DPA_WORKSPACE_INTAKE_KIND = "workspace_dpa_intake_report"
DPA_WORKSPACE_INTAKE_MODEL = "workspace-dpa-intake-v1"
READY_STATUS = "READY_FOR_DPA_INTAKE_ADJUDICATION"
BLOCKED_STATUS = "BLOCKED_FOR_DPA_INTAKE"


@dataclass(frozen=True)
class DpaIntakeDecisionGroup:
    classification: str
    surface_count: int
    maintainer_decision_required_count: int
    generated_or_command_updated_count: int
    default_decision: str
    dpa_600_evidence: str
    dpa_700_evidence: str
    source_authority: str
    writer: str
    reader: str
    representative_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "surface_count": self.surface_count,
            "maintainer_decision_required_count": self.maintainer_decision_required_count,
            "generated_or_command_updated_count": self.generated_or_command_updated_count,
            "default_decision": self.default_decision,
            "dpa_600_evidence": self.dpa_600_evidence,
            "dpa_700_evidence": self.dpa_700_evidence,
            "source_authority": self.source_authority,
            "writer": self.writer,
            "reader": self.reader,
            "representative_paths": list(self.representative_paths),
        }


@dataclass(frozen=True)
class WorkspaceDpaIntakeReport:
    root: Path
    validation_ref: str
    validation_ref_source: str
    workspace_adoption: WorkspaceAdoptReport
    dpa_assessment: DpaRepoAdoptionAssessment
    decision_groups: tuple[DpaIntakeDecisionGroup, ...]
    evidence_output_path: str | None = None
    evidence_execute: bool = False
    evidence_write: dict[str, Any] | None = None

    @property
    def result_status(self) -> str:
        if self.dpa_assessment.blocker_count:
            return BLOCKED_STATUS
        if self.evidence_write is not None and self.evidence_write["result_status"] == "BLOCK":
            return BLOCKED_STATUS
        return READY_STATUS

    @property
    def ok(self) -> bool:
        return self.result_status == READY_STATUS

    @property
    def maintainer_decision_required_count(self) -> int:
        return sum(group.maintainer_decision_required_count for group in self.decision_groups)

    @property
    def generated_or_command_updated_count(self) -> int:
        return sum(group.generated_or_command_updated_count for group in self.decision_groups)

    def as_json_data(self) -> dict[str, Any]:
        payload = {
            "schema_version": 1,
            "kind": DPA_WORKSPACE_INTAKE_KIND,
            "intake_model": DPA_WORKSPACE_INTAKE_MODEL,
            "result_status": self.result_status,
            "root": self.root.as_posix(),
            "validation_ref": self.validation_ref,
            "validation_ref_source": self.validation_ref_source,
            "workspace_adoption": _workspace_adoption_summary(self.workspace_adoption),
            "dpa_repo_adoption_assessment": self.dpa_assessment.as_dict(),
            "adjudication_plan": {
                "decision_group_count": len(self.decision_groups),
                "maintainer_decision_required_count": self.maintainer_decision_required_count,
                "generated_or_command_updated_count": self.generated_or_command_updated_count,
                "groups": [group.as_dict() for group in self.decision_groups],
            },
            "automation": {
                "workspace_adopt_completed": True,
                "dpa_repo_adoption_assessment_completed": True,
                "exact_ref_resolved": self.validation_ref != "UNKNOWN",
                "evidence_write_requested": self.evidence_output_path is not None,
                "evidence_output_path": self.evidence_output_path,
                "evidence_execute_requested": self.evidence_execute,
                "conformance_adjudication_performed": False,
                "migration_performed": False,
                "production_mutation_performed": False,
            },
            "claims": {
                "kit_wide_dpa_conformance_claimed": False,
                "stable_dpa_claimed": False,
                "external_repo_conformance_claimed": False,
                "automatic_migration_performed": False,
                "production_mutation_performed": False,
            },
            "next_actions": _next_actions(self),
            "final_signal": "d" if self.ok else "f",
        }
        if self.evidence_write is not None:
            payload["evidence_write"] = self.evidence_write
        return payload


def build_workspace_dpa_intake_report(
    root: Path | str = Path("."),
    *,
    validation_ref: str | None = None,
    output: Path | str | None = None,
    write_evidence: bool = False,
    execute: bool = False,
) -> WorkspaceDpaIntakeReport:
    root_path = Path(root).resolve()
    resolved_ref, ref_source = _resolve_validation_ref(root_path, validation_ref)
    adoption = analyze_workspace_adoption(root_path)
    assessment = evaluate_dpa_repo_adoption_assessment(
        root_path,
        validation_ref=resolved_ref if resolved_ref != "UNKNOWN" else None,
    )
    evidence_target = _evidence_target(
        root_path,
        assessment.current_validation_ref,
        output=output,
        write_evidence=write_evidence,
    )
    report = WorkspaceDpaIntakeReport(
        root=root_path,
        validation_ref=assessment.current_validation_ref,
        validation_ref_source=ref_source,
        workspace_adoption=adoption,
        dpa_assessment=assessment,
        decision_groups=_decision_groups(assessment.surfaces),
        evidence_output_path=_render_evidence_target(root_path, evidence_target),
        evidence_execute=execute,
    )
    if evidence_target is None:
        return report
    evidence_write = write_workspace_dpa_intake_json(
        report,
        root_path,
        evidence_target,
        execute=execute,
    )
    return WorkspaceDpaIntakeReport(
        root=report.root,
        validation_ref=report.validation_ref,
        validation_ref_source=report.validation_ref_source,
        workspace_adoption=report.workspace_adoption,
        dpa_assessment=report.dpa_assessment,
        decision_groups=report.decision_groups,
        evidence_output_path=report.evidence_output_path,
        evidence_execute=report.evidence_execute,
        evidence_write=evidence_write,
    )


def render_workspace_dpa_intake_report(report: WorkspaceDpaIntakeReport) -> str:
    lines = [
        "WORKSPACE_DPA_INTAKE",
        f"STATUS={report.result_status}",
        f"ROOT={report.root.as_posix()}",
        f"VALIDATION_REF={report.validation_ref}",
        f"VALIDATION_REF_SOURCE={report.validation_ref_source}",
        "WORKSPACE_ADOPT_STATUS=PASS",
        f"AGENTIC_STATUS={report.workspace_adoption.agentic.status}",
        f"DPA_REPO_ADOPTION_STATUS={report.dpa_assessment.result_status}",
        f"SURFACES={len(report.dpa_assessment.surfaces)}",
        f"HIGH_AUTHORITY_SURFACES={report.dpa_assessment.high_authority_surface_count}",
        f"MAINTAINER_DECISIONS_REQUIRED={report.maintainer_decision_required_count}",
        f"GENERATED_OR_COMMAND_UPDATED_SURFACES={report.generated_or_command_updated_count}",
        f"BLOCKERS={report.dpa_assessment.blocker_count}",
        f"WARNINGS={report.dpa_assessment.warning_count}",
        "EXTERNAL_REPO_CONFORMANCE_CLAIMED=false",
        "AUTOMATIC_MIGRATION_PERFORMED=false",
        "PRODUCTION_MUTATION_PERFORMED=false",
    ]
    if report.evidence_write is not None:
        reason = f"|reason={report.evidence_write['reason']}" if "reason" in report.evidence_write else ""
        lines.append(
            "EVIDENCE_WRITE="
            f"{report.evidence_write['result_status']}|"
            f"path={report.evidence_write['output_path']}|"
            f"written={str(report.evidence_write.get('written', False)).lower()}"
            f"{reason}"
        )
    lines.append("NEXT=maintainer-adjudicate listed decision groups before conformance claims")
    for group in report.decision_groups:
        lines.append(
            "DECISION_GROUP="
            f"{group.classification}|surfaces={group.surface_count}|"
            f"maintainer_decisions={group.maintainer_decision_required_count}|"
            f"generated_or_command_updated={group.generated_or_command_updated_count}|"
            f"default={group.default_decision}"
        )
    for finding in report.dpa_assessment.findings:
        lines.append(
            f"FINDING={finding.severity}|{finding.code}|path={finding.path}|{finding.message}"
        )
    return "\n".join(lines) + "\n"


def write_workspace_dpa_intake_json(
    report: WorkspaceDpaIntakeReport,
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
    evidence_root = dpa_repo_adoption_evidence_output_root(base)
    if evidence_root not in (output_path, *output_path.parents):
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_dpa_assessment_evidence_root",
            "output_path": relative.as_posix(),
            "written": False,
        }

    rendered = json.dumps(report.as_json_data(), indent=2, sort_keys=True) + "\n"
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


def _workspace_adoption_summary(report: WorkspaceAdoptReport) -> dict[str, Any]:
    return {
        "kind": "workspace_adopt_report_summary",
        "result_status": "PASS",
        "root": report.root.as_posix(),
        "project": report.project.as_json_data(),
        "proposed_manifest": report.manifest,
        "proposed_manifest_yaml": report.manifest_yaml,
        "docs_preview": [row.as_json_data() for row in report.docs_preview],
        "documentation_age_baseline": [
            row.as_json_data() for row in report.documentation_age_baseline
        ],
        "ci_workflows": list(report.ci_workflows),
        "agentic": report.agentic.as_json_data(),
        "init_tree": list(report.init_tree),
        "privacy_boundary": report.privacy_boundary,
    }


def _decision_groups(
    surfaces: tuple[DpaRepoAdoptionSurface, ...],
) -> tuple[DpaIntakeDecisionGroup, ...]:
    by_classification: dict[str, list[DpaRepoAdoptionSurface]] = {}
    for surface in surfaces:
        by_classification.setdefault(surface.classification, []).append(surface)

    groups: list[DpaIntakeDecisionGroup] = []
    for classification, members in sorted(by_classification.items()):
        first = members[0]
        groups.append(
            DpaIntakeDecisionGroup(
                classification=classification,
                surface_count=len(members),
                maintainer_decision_required_count=sum(
                    1 for surface in members if surface.maintainer_adjudication_required
                ),
                generated_or_command_updated_count=sum(
                    1 for surface in members if surface.generated_or_command_updated
                ),
                default_decision=_default_decision(classification, first),
                dpa_600_evidence=first.dpa_600_evidence,
                dpa_700_evidence=first.dpa_700_evidence,
                source_authority=first.source_authority,
                writer=first.writer,
                reader=first.reader,
                representative_paths=tuple(surface.path for surface in members[:10]),
            )
        )
    return tuple(groups)


def _default_decision(classification: str, surface: DpaRepoAdoptionSurface) -> str:
    if surface.generated_or_command_updated:
        return "no-migration-command-owned-regeneration"
    if classification == "ci_workflow":
        return "bounded-rollout-with-rollback-required"
    if classification in {"status_authority", "handoff_authority"}:
        return "manual-preservation-required"
    if classification == "workspace_manifest":
        return "command-only-migration-or-no-migration-required"
    return "maintainer-adjudication-required"


def _resolve_validation_ref(root: Path, validation_ref: str | None) -> tuple[str, str]:
    explicit = validation_ref.strip() if isinstance(validation_ref, str) else ""
    if explicit:
        return explicit, "explicit"
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return "UNKNOWN", "missing"
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip(), "git_head"
    return "UNKNOWN", "missing"


def _evidence_target(
    root: Path,
    validation_ref: str,
    *,
    output: Path | str | None,
    write_evidence: bool,
) -> Path | str | None:
    if output is not None:
        return output
    if not write_evidence:
        return None
    return dpa_repo_adoption_evidence_output_root(root) / (
        f"workspace-dpa-intake-{_safe_ref_token(validation_ref)}.json"
    )


def _render_evidence_target(root: Path, target: Path | str | None) -> str | None:
    if target is None:
        return None
    output_path = _resolve_under_root(root, target)
    try:
        return output_path.relative_to(root).as_posix()
    except ValueError:
        return output_path.as_posix()


def _safe_ref_token(validation_ref: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", validation_ref.strip()).strip(".-")
    if not token or token == "UNKNOWN":
        return "unknown-ref"
    return token[:40]


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _next_actions(report: WorkspaceDpaIntakeReport) -> list[str]:
    actions: list[str] = []
    if report.validation_ref == "UNKNOWN":
        actions.append("record an exact repository ref before adoption readiness")
    if report.workspace_adoption.agentic.status == "foreign_agentic_directory":
        actions.append("diagnose foreign .agentic/ directory before workspace init")
    if report.evidence_write is None:
        actions.append("write bounded DPA intake evidence if this repo enters managed scope")
    elif report.evidence_write["result_status"] == "BLOCK":
        actions.append("choose an evidence path under docs/architecture/evidence/dpa/assessment/")
    elif not report.evidence_write.get("written", False):
        actions.append("rerun with explicit execute semantics to write bounded intake evidence")
    actions.append("maintainer-adjudicate each decision group before migration or conformance claims")
    return actions
