from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH, evaluate_dpa_readiness
from agentic_project_kit.workspace import load_workspace

DECISION_CONTROL_SURFACES = (
    "docs/architecture/evidence/dpa/assessment/DP1_ASSESSMENT_READINESS_20260728.md",
    "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json",
    "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md",
    "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md",
    "docs/architecture/dpa/probes/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md",
    "docs/architecture/dpa/probes/fixtures/DP1_PROBE_CLEANUP_AND_ASSESSMENT_PLAN_20260727.md",
)
EXPECTED_DECISION_REQUIREMENTS = (
    "probe_002_full_evidence",
    "renderer_full_evidence",
    "probe_003_full_evidence",
    "probe_004_full_evidence",
    "maintainer_assessment",
    "first_dp2_target_scope",
    "rollback_cleanup_proven",
    "maintainer_authorization",
)
EXPECTED_EVIDENCE_IDS = (
    "current-kit-readonly-refresh",
    "current-kit-probe-001-registry-compatibility",
    "current-kit-probe-002-lifecycle-readiness-preflight",
    "current-kit-wrt-ch001-admin-refresh-observation",
    "current-kit-probe-003-workflow-readiness-preflight",
    "current-kit-renderer-probe-readiness-preflight",
    "current-kit-probe-004-migration-readiness-preflight",
)
ASSESSMENT_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")


@dataclass(frozen=True)
class Dp2DecisionFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Dp2DecisionReadinessResult:
    root: str
    validation_ref: str
    readiness_record: str
    readiness_status: str
    implementation_percent: int
    blockers: tuple[str, ...]
    data: dict[str, Any]
    findings: tuple[Dp2DecisionFinding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if self.readiness_status == "DP2_AUTHORIZED" and not self.blockers:
            return "DP2_AUTHORIZED_ALREADY"
        return "READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_dp2_decision_readiness",
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "readiness_record": self.readiness_record,
            "readiness_status": self.readiness_status,
            "implementation_percent": self.implementation_percent,
            "structural_ok": self.structural_ok,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
            "readiness_blockers": list(self.blockers),
            **self.data,
        }


def evaluate_dp2_decision_readiness(
    root: Path | str = ".",
    *,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
) -> Dp2DecisionReadinessResult:
    base = Path(root).resolve()
    record_path = _resolve_under_root(base, readiness_path)
    findings: list[Dp2DecisionFinding] = []

    readiness = evaluate_dpa_readiness(base, readiness_path=record_path)
    for finding in readiness.findings:
        findings.append(
            Dp2DecisionFinding(
                code=f"readiness-{finding.code}",
                message=finding.message,
                path=finding.path,
            )
        )

    readiness_data = readiness.data if isinstance(readiness.data, dict) else {}
    control_surfaces = _path_records(base, DECISION_CONTROL_SURFACES)
    for item in control_surfaces:
        if not item["present"]:
            findings.append(
                Dp2DecisionFinding(
                    code="decision-control-surface-missing",
                    message=f"Required DP2 decision control surface is missing: {item['path']}",
                    path=item["path"],
                )
            )

    dp2_entry_status = readiness_data.get("dp2_entry_status")
    if not isinstance(dp2_entry_status, dict):
        dp2_entry_status = {}
        findings.append(
            Dp2DecisionFinding(
                code="dp2-entry-status-missing",
                message="readiness record must contain dp2_entry_status mapping",
                path=_display_path(record_path, base),
            )
        )
    for requirement in EXPECTED_DECISION_REQUIREMENTS:
        if requirement not in dp2_entry_status:
            findings.append(
                Dp2DecisionFinding(
                    code="decision-requirement-missing",
                    message=f"Required DP2 decision requirement is missing: {requirement}",
                    path=_display_path(record_path, base),
                )
            )

    evidence_inputs = _evidence_input_records(readiness_data)
    evidence_ids = {item["id"] for item in evidence_inputs}
    for evidence_id in EXPECTED_EVIDENCE_IDS:
        if evidence_id not in evidence_ids:
            findings.append(
                Dp2DecisionFinding(
                    code="decision-evidence-input-missing",
                    message=f"Required current evidence input is missing: {evidence_id}",
                    path=_display_path(record_path, base),
                )
            )

    validation = validation_ref or _git_head(base)
    blockers = tuple(readiness.blockers)
    data = {
        "control_surfaces": control_surfaces,
        "evidence_inputs": evidence_inputs,
        "decision_requirements": _decision_requirement_records(dp2_entry_status),
        "candidate_first_dp2_target_scope": _candidate_first_target_scope(),
        "required_maintainer_actions": _required_maintainer_actions(dp2_entry_status),
        "claims": {
            "maintainer_assessment_recorded": False,
            "maintainer_authorization_recorded": False,
            "first_dp2_target_selected": False,
            "rollback_cleanup_proven": False,
            "dp2_authorized": False,
            "probe_execution_claimed": False,
            "production_mutation_performed": False,
            "kit_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
        },
    }
    return Dp2DecisionReadinessResult(
        root=base.as_posix(),
        validation_ref=validation,
        readiness_record=_display_path(record_path, base),
        readiness_status=readiness.status,
        implementation_percent=readiness.implementation_percent,
        blockers=blockers,
        data=data,
        findings=tuple(findings),
    )


def render_dp2_decision_readiness(result: Dp2DecisionReadinessResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP2_DECISION_READINESS",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"READINESS_STATUS={payload['readiness_status']}",
        f"IMPLEMENTATION_PERCENT={payload['implementation_percent']}",
        f"FINDINGS={payload['finding_count']}",
        f"BLOCKERS={payload['blocker_count']}",
    ]
    for blocker in payload["readiness_blockers"]:
        lines.append(f"READINESS_BLOCKER={blocker}")
    if payload["finding_count"]:
        for finding in payload["findings"]:
            lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_dp2_decision_readiness_json(
    result: Dp2DecisionReadinessResult,
    root: Path | str,
    output: Path | str,
    *,
    execute: bool,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output_path = _resolve_under_root(base, output)
    relative = output_path.relative_to(base)
    evidence_root = _assessment_output_root(base)
    if evidence_root not in (output_path, *output_path.parents):
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_dpa_assessment_evidence_root",
            "output_path": relative.as_posix(),
            "written": False,
        }
    changed = True
    rendered = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
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


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _path_records(root: Path, paths: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"path": item, "present": (root / item).exists()} for item in paths]


def _assessment_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*ASSESSMENT_OUTPUT_ROOT_PARTS)).resolve()


def _evidence_input_records(readiness_data: dict[str, Any]) -> list[dict[str, str]]:
    raw = readiness_data.get("evidence_inputs")
    if not isinstance(raw, list):
        return []
    records: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        records.append(
            {
                "id": str(item.get("id", "")),
                "path": str(item.get("path", "")),
                "result": str(item.get("result", "")),
            }
        )
    return records


def _decision_requirement_records(dp2_entry_status: dict[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for requirement in EXPECTED_DECISION_REQUIREMENTS:
        status = dp2_entry_status.get(requirement)
        records.append(
            {
                "id": requirement,
                "status": str(status or "MISSING"),
                "required_before_dp2": "true",
            }
        )
    return records


def _candidate_first_target_scope() -> dict[str, Any]:
    return {
        "status": "CANDIDATE_REQUIRES_MAINTAINER_RATIFICATION",
        "target_path": "docs/handoff/CURRENT_HANDOFF.md",
        "target_kind": "current self-hosting administrative handoff surface",
        "selected_writers_for_candidate": ["WRT-CH-001"],
        "requires_select_or_defer_decision": ["WRT-CH-002", "WRT-CH-003", "WRT-CH-004"],
        "excluded_from_candidate": {
            "WRT-CH-005": "external-habitability/template writer, not current self-hosting target",
            "WRT-CH-006": "generated successor-package outputs; covered through source command and rollback boundaries",
        },
        "not_authorization": True,
    }


def _required_maintainer_actions(dp2_entry_status: dict[str, Any]) -> list[dict[str, str]]:
    actions = (
        (
            "assess_partial_probe_evidence",
            "maintainer_assessment",
            "Adjudicate every partial or blocked Probe family before DP2.",
        ),
        (
            "ratify_first_dp2_target_scope",
            "first_dp2_target_scope",
            "Select or revise the first DP2 target and writer scope.",
        ),
        (
            "require_rollback_cleanup_proof",
            "rollback_cleanup_proven",
            "Preserve rollback and cleanup evidence for the selected target.",
        ),
        (
            "record_dp2_authorization_token",
            "maintainer_authorization",
            "Record explicit Maintainer authorization only after prerequisites close.",
        ),
    )
    records: list[dict[str, str]] = []
    for action_id, requirement, action in actions:
        status = str(dp2_entry_status.get(requirement, "MISSING"))
        if status != "BLOCKED" and status != "MISSING":
            continue
        records.append(
            {
                "id": action_id,
                "dp2_entry_requirement": requirement,
                "current_status": status,
                "action": action,
            }
        )
    return records


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"
    return completed.stdout.strip() or "UNKNOWN"
