from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_dp3_dp4_adjudication import (
    DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
    Dp3Dp4AdjudicationResult,
    evaluate_dp3_dp4_adjudication_record,
)
from agentic_project_kit.dpa_readiness import (
    DEFAULT_READINESS_PATH,
    evaluate_dpa_readiness,
)
from agentic_project_kit.dpa_successor_projection import (
    DPA_SUCCESSOR_PROJECTION_CONTRACT_ID,
    DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS,
    DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
    DPA_SUCCESSOR_PROJECTION_WRITER_ID,
)
from agentic_project_kit.dpa_workspace_init_projection import (
    DPA_WORKSPACE_INIT_CONTRACT_ID,
    DPA_WORKSPACE_INIT_MANIFEST_PATH,
    DPA_WORKSPACE_INIT_SOURCE_PATHS,
    DPA_WORKSPACE_INIT_TARGET_SCOPE,
    DPA_WORKSPACE_INIT_WRITER_ID,
)
from agentic_project_kit.workspace import load_workspace

ASSESSMENT_MODEL = "dpa-post-dp2-scope-assessment-v1"
RESULT_STATUS = "POST_DP2_SCOPE_ASSESSMENT_RECORDED"
KIT_WIDE_DPA_STATUS = "DP3_DP5_NOT_COMPLETE"
KIT_WIDE_DPA_STATUS_DP5_ONLY = "DP5_NOT_COMPLETE"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")


@dataclass(frozen=True)
class ScopeAssessmentFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class RolloutCandidate:
    writer_id: str
    target_identity: str
    target_path: str
    source_authority: str
    source_paths: tuple[str, ...]
    document_form: str
    readiness_record_status: str
    implementation_result_ref: str
    implementation_ref_verified: bool | None
    dpa_600_evidence: dict[str, Any]
    dpa_700_evidence: dict[str, Any]
    rollback: str
    adjudication_record: str
    adjudication_status: str
    entry_blockers: tuple[str, ...]
    completion_blockers: tuple[str, ...]

    @property
    def entry_ready(self) -> bool:
        return not self.entry_blockers

    @property
    def status(self) -> str:
        if self.entry_blockers:
            return "BLOCKED_FOR_DP3_ENTRY"
        if not self.completion_blockers:
            return "ADJUDICATED_FOR_BOUNDED_DP3_ROLLOUT"
        return "READY_FOR_BOUNDED_DP3_ADJUDICATION"

    def as_dict(self) -> dict[str, Any]:
        return {
            "writer_id": self.writer_id,
            "target_identity": self.target_identity,
            "target_path": self.target_path,
            "source_authority": self.source_authority,
            "source_paths": list(self.source_paths),
            "document_form": self.document_form,
            "readiness_record_status": self.readiness_record_status,
            "implementation_result_ref": self.implementation_result_ref,
            "implementation_ref_verified": self.implementation_ref_verified,
            "dpa_600_evidence": self.dpa_600_evidence,
            "dpa_700_evidence": self.dpa_700_evidence,
            "rollback": self.rollback,
            "adjudication_record": self.adjudication_record,
            "adjudication_status": self.adjudication_status,
            "status": self.status,
            "entry_ready": self.entry_ready,
            "entry_blockers": list(self.entry_blockers),
            "completion_blockers": list(self.completion_blockers),
            "claims": _false_claims(),
        }


@dataclass(frozen=True)
class StatusAuthorityCandidate:
    id: str
    path: str
    document_form: str
    source_authority: str
    target_identity: str
    generated_or_command_updated: bool
    decision: str
    adjudication_record: str
    adjudication_status: str
    blockers: tuple[str, ...]
    evidence: tuple[str, ...]

    @property
    def status(self) -> str:
        if self.blockers:
            return "BLOCKED_FOR_DP4_EXIT"
        return "ADJUDICATED_FOR_BOUNDED_DP4_EXIT"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "document_form": self.document_form,
            "source_authority": self.source_authority,
            "target_identity": self.target_identity,
            "generated_or_command_updated": self.generated_or_command_updated,
            "decision": self.decision,
            "adjudication_record": self.adjudication_record,
            "adjudication_status": self.adjudication_status,
            "status": self.status,
            "blockers": list(self.blockers),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class StrictLifecycleStage:
    stage: str
    status: str
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "status": self.status, "blockers": list(self.blockers)}


@dataclass(frozen=True)
class PostDp2ScopeAssessmentResult:
    root: str
    validation_ref: str
    readiness_record: str
    dp2_status: str
    dp2_implementation_percent: int
    dp2_scope: str
    adjudication_record: Dp3Dp4AdjudicationResult
    rollout_candidates: tuple[RolloutCandidate, ...]
    status_authority_candidates: tuple[StatusAuthorityCandidate, ...]
    strict_lifecycle_stages: tuple[StrictLifecycleStage, ...]
    findings: tuple[ScopeAssessmentFinding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def dp3_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for candidate in self.rollout_candidates:
            blockers.extend(f"{candidate.writer_id}:{blocker}" for blocker in candidate.entry_blockers)
            blockers.extend(f"{candidate.writer_id}:{blocker}" for blocker in candidate.completion_blockers)
        return tuple(blockers)

    @property
    def dp4_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for candidate in self.status_authority_candidates:
            blockers.extend(f"{candidate.id}:{blocker}" for blocker in candidate.blockers)
        return tuple(blockers)

    @property
    def dp5_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for stage in self.strict_lifecycle_stages:
            blockers.extend(f"{stage.stage}:{blocker}" for blocker in stage.blockers)
        return tuple(dict.fromkeys(blockers))

    @property
    def blocker_count(self) -> int:
        return len(self.dp3_blockers) + len(self.dp4_blockers) + len(self.dp5_blockers)

    @property
    def final_closeout_ready(self) -> bool:
        return self.structural_ok and self.blocker_count == 0

    @property
    def kit_wide_dpa_status(self) -> str:
        if self.final_closeout_ready:
            return "READY_FOR_FINAL_CLOSEOUT_RECORD"
        if not self.dp3_blockers and not self.dp4_blockers and self.dp5_blockers:
            return KIT_WIDE_DPA_STATUS_DP5_ONLY
        return KIT_WIDE_DPA_STATUS

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if self.dp2_status != "DP2_AUTHORIZED":
            return "DP2_NOT_AUTHORIZED"
        return RESULT_STATUS

    def as_dict(self) -> dict[str, Any]:
        dp3_bounded_slice_adjudicated = not self.dp3_blockers
        dp4_bounded_slice_adjudicated = not self.dp4_blockers
        return {
            "schema_version": 1,
            "kind": "dpa_post_dp2_scope_assessment",
            "assessment_model": ASSESSMENT_MODEL,
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "readiness_record": self.readiness_record,
            "dp2_status": self.dp2_status,
            "dp2_implementation_percent": self.dp2_implementation_percent,
            "dp2_scope": self.dp2_scope,
            "kit_wide_dpa_status": self.kit_wide_dpa_status,
            "kit_wide_dpa_conformance_claimed": False,
            "final_closeout_ready": self.final_closeout_ready,
            "dp3_dp4_adjudication": self.adjudication_record.as_dict(),
            "finding_count": len(self.findings),
            "blocker_count": self.blocker_count,
            "findings": [finding.as_dict() for finding in self.findings],
            "dp3": {
                "status": (
                    "ADJUDICATED_FOR_BOUNDED_SLICE"
                    if dp3_bounded_slice_adjudicated
                    else "NOT_COMPLETE"
                ),
                "bounded_slice_adjudicated": dp3_bounded_slice_adjudicated,
                "blockers": list(self.dp3_blockers),
                "rollout_candidates": [candidate.as_dict() for candidate in self.rollout_candidates],
            },
            "dp4": {
                "status": (
                    "ADJUDICATED_FOR_BOUNDED_STATUS_AUTHORITY_SLICE"
                    if dp4_bounded_slice_adjudicated
                    else "NOT_COMPLETE"
                ),
                "bounded_slice_adjudicated": dp4_bounded_slice_adjudicated,
                "blockers": list(self.dp4_blockers),
                "status_authority_candidates": [
                    candidate.as_dict() for candidate in self.status_authority_candidates
                ],
            },
            "dp5": {
                "status": "BLOCKED_BEFORE_STAGE_TRANSITION",
                "blockers": list(self.dp5_blockers),
                "strict_lifecycle_stages": [stage.as_dict() for stage in self.strict_lifecycle_stages],
            },
            "claims": _false_claims(),
        }


def evaluate_post_dp2_scope_assessment(
    root: Path | str = ".",
    *,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
    adjudication_record_path: Path | str = DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
    validation_ref: str | None = None,
) -> PostDp2ScopeAssessmentResult:
    base = Path(root).resolve()
    readiness = evaluate_dpa_readiness(base, readiness_path=readiness_path)
    record_path = _resolve_under_root(base, readiness_path)
    findings = [
        ScopeAssessmentFinding(
            code=f"dp2-readiness-{finding.code}",
            message=finding.message,
            path=finding.path,
        )
        for finding in readiness.findings
    ]
    selected_writer_status = _mapping(readiness.data.get("selected_writer_status"))
    resolved_validation_ref = validation_ref or _git_head(base)
    adjudication = evaluate_dp3_dp4_adjudication_record(
        base,
        record_path=adjudication_record_path,
        validation_ref=resolved_validation_ref,
    )

    rollout_candidates = _rollout_candidates(base, selected_writer_status, adjudication)
    status_authority_candidates = _status_authority_candidates(base, adjudication)
    strict_lifecycle_stages = _strict_lifecycle_stages(adjudication)
    dp2_scope = str(
        _mapping(readiness.data.get("dp2_entry_status")).get(
            "first_dp2_target_scope",
            "UNKNOWN",
        )
    )
    return PostDp2ScopeAssessmentResult(
        root=base.as_posix(),
        validation_ref=resolved_validation_ref,
        readiness_record=_display_path(record_path, base),
        dp2_status=readiness.status,
        dp2_implementation_percent=readiness.implementation_percent,
        dp2_scope=dp2_scope,
        adjudication_record=adjudication,
        rollout_candidates=rollout_candidates,
        status_authority_candidates=status_authority_candidates,
        strict_lifecycle_stages=strict_lifecycle_stages,
        findings=tuple(findings),
    )


def render_post_dp2_scope_assessment(result: PostDp2ScopeAssessmentResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_POST_DP2_SCOPE_ASSESSMENT",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"DP2_STATUS={payload['dp2_status']}",
        f"DP2_IMPLEMENTATION_PERCENT={payload['dp2_implementation_percent']}",
        f"DP2_SCOPE={payload['dp2_scope']}",
        f"KIT_WIDE_DPA_STATUS={payload['kit_wide_dpa_status']}",
        "KIT_WIDE_DPA_CONFORMANCE_CLAIMED=false",
        f"FINAL_CLOSEOUT_READY={str(payload['final_closeout_ready']).lower()}",
        f"FINDINGS={payload['finding_count']}",
        f"BLOCKERS={payload['blocker_count']}",
    ]
    for candidate in payload["dp3"]["rollout_candidates"]:
        lines.append(
            "DP3_TARGET="
            f"{candidate['writer_id']}|status={candidate['status']}|target={candidate['target_identity']}"
        )
    for candidate in payload["dp4"]["status_authority_candidates"]:
        lines.append(
            "DP4_CANDIDATE="
            f"{candidate['id']}|status={candidate['status']}|decision={candidate['decision']}"
        )
    for stage in payload["dp5"]["strict_lifecycle_stages"]:
        lines.append(f"DP5_STAGE={stage['stage']}|status={stage['status']}")
    for blocker in (*payload["dp3"]["blockers"], *payload["dp4"]["blockers"], *payload["dp5"]["blockers"]):
        lines.append(f"BLOCKER={blocker}")
    for finding in payload["findings"]:
        lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_post_dp2_scope_assessment_json(
    result: PostDp2ScopeAssessmentResult,
    root: Path | str,
    output: Path | str,
    *,
    execute: bool,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output_path = _resolve_under_root(base, output)
    relative = output_path.relative_to(base)
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


def _rollout_candidates(
    root: Path,
    selected_writer_status: dict[str, Any],
    adjudication: Dp3Dp4AdjudicationResult,
) -> tuple[RolloutCandidate, ...]:
    return (
        _candidate(
            root,
            writer_id=DPA_WORKSPACE_INIT_WRITER_ID,
            target_identity=DPA_WORKSPACE_INIT_TARGET_SCOPE,
            target_path=DPA_WORKSPACE_INIT_MANIFEST_PATH,
            source_authority=DPA_WORKSPACE_INIT_CONTRACT_ID,
            source_paths=DPA_WORKSPACE_INIT_SOURCE_PATHS,
            document_form="external-generated-initialization-manifest",
            readiness_record_status=str(selected_writer_status.get(DPA_WORKSPACE_INIT_WRITER_ID, "MISSING")),
            expected_readiness_status="EXTERNAL_HABITABILITY_ONLY",
            implementation_result_ref="f653bbbb",
            evidence_path="docs/architecture/evidence/dpa/probes/fixture-evidence-0b985a22-wrt-ch005-20260729/results.json",
            rollback="no production migration; fixture cleanup covers disposable generated target roots",
            adjudication=adjudication,
            completion_blocker="dp3-adjudicated-rollout-result-missing",
        ),
        _candidate(
            root,
            writer_id=DPA_SUCCESSOR_PROJECTION_WRITER_ID,
            target_identity=DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
            target_path="docs/reports/handoff-packages/latest/",
            source_authority=DPA_SUCCESSOR_PROJECTION_CONTRACT_ID,
            source_paths=DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS,
            document_form="command-generated-successor-handoff-projection",
            readiness_record_status=str(selected_writer_status.get(DPA_SUCCESSOR_PROJECTION_WRITER_ID, "MISSING")),
            expected_readiness_status="GENERATED_OUTPUT_CONTRACT_ONLY",
            implementation_result_ref="644f470a",
            evidence_path="docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json",
            rollback="source command contract and exact-byte rollback classification; no durable manual patches",
            adjudication=adjudication,
            completion_blocker="dp3-or-dp4-generated-output-adjudication-record-missing",
        ),
    )


def _candidate(
    root: Path,
    *,
    writer_id: str,
    target_identity: str,
    target_path: str,
    source_authority: str,
    source_paths: tuple[str, ...],
    document_form: str,
    readiness_record_status: str,
    expected_readiness_status: str,
    implementation_result_ref: str,
    evidence_path: str,
    rollback: str,
    adjudication: Dp3Dp4AdjudicationResult,
    completion_blocker: str,
) -> RolloutCandidate:
    entry_blockers: list[str] = []
    for source_path in source_paths:
        if not (root / source_path).exists():
            entry_blockers.append(f"source-missing:{source_path}")
    if readiness_record_status != expected_readiness_status:
        entry_blockers.append(
            f"readiness-record-status-mismatch:{readiness_record_status}:expected:{expected_readiness_status}"
        )
    evidence = _evidence_summary(root, evidence_path)
    if not evidence["present"]:
        entry_blockers.append(f"evidence-missing:{evidence_path}")
    elif evidence.get("result_status") != "FULL_FIXTURE_EVIDENCE_RECORDED":
        entry_blockers.append(f"fixture-evidence-not-full:{evidence.get('result_status')}")
    if _mapping(evidence.get("full_evidence_by_family")).get("PROBE-003") is not True:
        entry_blockers.append("dpa-600-probe-003-evidence-missing")
    if _mapping(evidence.get("full_evidence_by_family")).get("PROBE-004") is not True:
        entry_blockers.append("dpa-700-probe-004-evidence-missing")
    if evidence.get("rollback_cleanup_proven") is not True:
        entry_blockers.append("rollback-cleanup-not-proven")
    completion_blockers: tuple[str, ...]
    if adjudication.dp3_target_accepted(writer_id):
        completion_blockers = ()
    else:
        completion_blockers = (completion_blocker,)
    return RolloutCandidate(
        writer_id=writer_id,
        target_identity=target_identity,
        target_path=target_path,
        source_authority=source_authority,
        source_paths=source_paths,
        document_form=document_form,
        readiness_record_status=readiness_record_status,
        implementation_result_ref=implementation_result_ref,
        implementation_ref_verified=_git_ref_exists(root, implementation_result_ref),
        dpa_600_evidence={
            "probe_family": "PROBE-003",
            "evidence_path": evidence_path,
            "satisfied": _mapping(evidence.get("full_evidence_by_family")).get("PROBE-003") is True,
        },
        dpa_700_evidence={
            "probe_family": "PROBE-004",
            "evidence_path": evidence_path,
            "satisfied": _mapping(evidence.get("full_evidence_by_family")).get("PROBE-004") is True,
            "rollback_cleanup_proven": evidence.get("rollback_cleanup_proven") is True,
        },
        rollback=rollback,
        adjudication_record=adjudication.record_path,
        adjudication_status=adjudication.dp3_target_status.get(writer_id, adjudication.result_status),
        entry_blockers=tuple(entry_blockers),
        completion_blockers=completion_blockers,
    )


def _status_authority_candidates(
    root: Path,
    adjudication: Dp3Dp4AdjudicationResult,
) -> tuple[StatusAuthorityCandidate, ...]:
    successor_evidence = "docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json"
    candidates = [
        StatusAuthorityCandidate(
            id="DP4-CURRENT-HANDOFF",
            path="docs/handoff/CURRENT_HANDOFF.md",
            document_form="hybrid-current-state-document",
            source_authority=".agentic/operational_handoff_state.yaml plus curated manual regions",
            target_identity="CURRENT_HANDOFF_SELF_HOSTING_TARGET",
            generated_or_command_updated=True,
            decision="manual-preservation-required-for-non-lifecycle-owned-bytes",
            adjudication_record=adjudication.record_path,
            adjudication_status=adjudication.dp4_candidate_status.get("DP4-CURRENT-HANDOFF", adjudication.result_status),
            blockers=_dp4_blockers(adjudication, "DP4-CURRENT-HANDOFF", "dp4-adjudication-record-missing"),
            evidence=("docs/architecture/evidence/dpa/assessment/DP2_MAINTAINER_ASSESSMENT_RECORD_20260728.json",),
        ),
        StatusAuthorityCandidate(
            id="DP4-STATUS",
            path="docs/STATUS.md",
            document_form="manual-current-state-dashboard",
            source_authority="manual-maintainer-current-state-update",
            target_identity="PROJECT_STATUS_CURRENT_STATE",
            generated_or_command_updated=False,
            decision="no-migration-until-reader-writer-inventory-is-recorded",
            adjudication_record=adjudication.record_path,
            adjudication_status=adjudication.dp4_candidate_status.get("DP4-STATUS", adjudication.result_status),
            blockers=_dp4_blockers(adjudication, "DP4-STATUS", "reader-writer-generator-command-update-inventory-missing"),
            evidence=(),
        ),
        StatusAuthorityCandidate(
            id="DP4-SUCCESSOR-PROJECTIONS",
            path="docs/reports/handoff-packages/latest/ and docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
            document_form="command-generated-successor-handoff-projection-family",
            source_authority=DPA_SUCCESSOR_PROJECTION_CONTRACT_ID,
            target_identity=DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
            generated_or_command_updated=True,
            decision="no-migration-generated-output-command-contract-boundary",
            adjudication_record=adjudication.record_path,
            adjudication_status=adjudication.dp4_candidate_status.get(
                "DP4-SUCCESSOR-PROJECTIONS",
                adjudication.result_status,
            ),
            blockers=_dp4_blockers(adjudication, "DP4-SUCCESSOR-PROJECTIONS", "dp4-no-migration-adjudication-record-missing"),
            evidence=(successor_evidence,),
        ),
    ]
    return tuple(_with_missing_path_blockers(root, candidate) for candidate in candidates)


def _with_missing_path_blockers(root: Path, candidate: StatusAuthorityCandidate) -> StatusAuthorityCandidate:
    path = candidate.path.split(" and ", 1)[0].rstrip("/")
    if path.endswith("latest"):
        path = "docs/reports/handoff-packages/latest"
    blockers = list(candidate.blockers)
    if not (root / path).exists():
        blockers.append(f"candidate-path-missing:{candidate.path}")
    for evidence in candidate.evidence:
        if not (root / evidence).exists():
            blockers.append(f"evidence-missing:{evidence}")
    return StatusAuthorityCandidate(
        id=candidate.id,
        path=candidate.path,
        document_form=candidate.document_form,
        source_authority=candidate.source_authority,
        target_identity=candidate.target_identity,
        generated_or_command_updated=candidate.generated_or_command_updated,
        decision=candidate.decision,
        adjudication_record=candidate.adjudication_record,
        adjudication_status=candidate.adjudication_status,
        blockers=tuple(blockers),
        evidence=candidate.evidence,
    )


def _dp4_blockers(adjudication: Dp3Dp4AdjudicationResult, candidate_id: str, fallback: str) -> tuple[str, ...]:
    if adjudication.dp4_candidate_accepted(candidate_id):
        return ()
    return (fallback,)


def _strict_lifecycle_stages(adjudication: Dp3Dp4AdjudicationResult) -> tuple[StrictLifecycleStage, ...]:
    blockers = []
    if not adjudication.ok:
        blockers.append("accepted-dp3-and-dp4-results-missing")
    blockers.extend(
        (
            "exact-stage-authorization-record-missing",
            "rollback-to-less-strict-stage-evidence-missing",
        )
    )
    blocker_tuple = tuple(blockers)
    return (
        StrictLifecycleStage("observe", "BLOCKED_BEFORE_STAGE_TRANSITION", blocker_tuple),
        StrictLifecycleStage("warn", "BLOCKED_BEFORE_STAGE_TRANSITION", blocker_tuple),
        StrictLifecycleStage("block-new", "BLOCKED_BEFORE_STAGE_TRANSITION", blocker_tuple),
        StrictLifecycleStage("strict", "BLOCKED_BEFORE_STAGE_TRANSITION", blocker_tuple),
    )


def _evidence_summary(root: Path, evidence_path: str) -> dict[str, Any]:
    path = root / evidence_path
    if not path.exists():
        return {"path": evidence_path, "present": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"path": evidence_path, "present": True, "json_error": str(exc)}
    if not isinstance(data, dict):
        return {"path": evidence_path, "present": True, "json_error": "evidence root must be object"}
    return {
        "path": evidence_path,
        "present": True,
        "kind": data.get("kind"),
        "validation_ref": data.get("validation_ref"),
        "result_status": data.get("result_status"),
        "full_evidence_by_family": data.get("full_evidence_by_family", {}),
        "rollback_cleanup_proven": data.get("rollback_cleanup_proven"),
    }


def _false_claims() -> dict[str, bool]:
    return {
        "dp3_complete": False,
        "dp4_complete": False,
        "dp5_strict_enforced": False,
        "kit_wide_dpa_conformance_claimed": False,
        "production_mutation_performed": False,
        "generated_outputs_manually_patched": False,
    }


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()


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


def _git_ref_exists(root: Path, ref: str) -> bool | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.returncode == 0
