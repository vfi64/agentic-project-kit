from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

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

DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/DP3_DP4_ADJUDICATION_RECORD_20260801.json"
)
ADJUDICATION_MODEL = "dpa-dp3-dp4-adjudication-record-v1"
VALID_STATUS = "VALID_DP3_DP4_ADJUDICATION_RECORD"
ACCEPTED_RECORD_STATUS = "DP3_DP4_BOUNDED_ADJUDICATION_ACCEPTED"
ACCEPTED_DECISION_TOKEN = "DPA_DP3_DP4_BOUNDED_ADJUDICATION_ACCEPTED"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")

REQUIRED_DP3_TARGETS: dict[str, dict[str, object]] = {
    DPA_WORKSPACE_INIT_WRITER_ID: {
        "target_identity": DPA_WORKSPACE_INIT_TARGET_SCOPE,
        "target_path": DPA_WORKSPACE_INIT_MANIFEST_PATH,
        "source_authority": DPA_WORKSPACE_INIT_CONTRACT_ID,
        "source_paths": DPA_WORKSPACE_INIT_SOURCE_PATHS,
        "document_form": "external-generated-initialization-manifest",
        "implementation_result_ref": "f653bbbb",
        "evidence": (
            "docs/architecture/evidence/dpa/probes/fixture-evidence-0b985a22-wrt-ch005-20260729/results.json",
        ),
    },
    DPA_SUCCESSOR_PROJECTION_WRITER_ID: {
        "target_identity": DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
        "target_path": "docs/reports/handoff-packages/latest/",
        "source_authority": DPA_SUCCESSOR_PROJECTION_CONTRACT_ID,
        "source_paths": DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS,
        "document_form": "command-generated-successor-handoff-projection",
        "implementation_result_ref": "644f470a",
        "evidence": (
            "docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json",
        ),
    },
}

REQUIRED_DP4_CANDIDATES: dict[str, dict[str, object]] = {
    "DP4-CURRENT-HANDOFF": {
        "path": "docs/handoff/CURRENT_HANDOFF.md",
        "decision": "MANUAL_PRESERVATION_WITH_LIFECYCLE_OWNED_GENERATED_BLOCK",
        "document_form": "hybrid-current-state-document",
        "target_identity": "CURRENT_HANDOFF_SELF_HOSTING_TARGET",
    },
    "DP4-STATUS": {
        "path": "docs/STATUS.md",
        "decision": "NO_MIGRATION_MANUAL_STATUS_DASHBOARD",
        "document_form": "manual-current-state-dashboard",
        "target_identity": "PROJECT_STATUS_CURRENT_STATE",
    },
    "DP4-SUCCESSOR-PROJECTIONS": {
        "path": "docs/reports/handoff-packages/latest/ and docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "decision": "NO_MIGRATION_COMMAND_GENERATED_OUTPUT_BOUNDARY",
        "document_form": "command-generated-successor-handoff-projection-family",
        "target_identity": DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
    },
}

FALSE_CLAIM_FIELDS = (
    "kit_wide_dpa_conformance_claimed",
    "dp5_strict_enforced",
    "production_mutation_performed",
    "generated_outputs_manually_patched",
    "stable_dpa_claimed",
)


@dataclass(frozen=True)
class Dp3Dp4AdjudicationFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Dp3Dp4AdjudicationResult:
    root: str
    record_path: str
    record_present: bool
    record_validation_ref: str
    current_validation_ref: str
    record_status: str
    decision_token: str
    dp3_target_status: dict[str, str]
    dp4_candidate_status: dict[str, str]
    dp5_next_stage_authorized: bool
    findings: tuple[Dp3Dp4AdjudicationFinding, ...]

    @property
    def ok(self) -> bool:
        return self.result_status == VALID_STATUS

    @property
    def result_status(self) -> str:
        if not self.record_present:
            return "MISSING_DP3_DP4_ADJUDICATION_RECORD"
        if self.findings:
            return "INVALID_DP3_DP4_ADJUDICATION_RECORD"
        return VALID_STATUS

    def dp3_target_accepted(self, writer_id: str) -> bool:
        return self.ok and self.dp3_target_status.get(writer_id) == "ACCEPTED_FOR_BOUNDED_DP3_ROLLOUT"

    def dp4_candidate_accepted(self, candidate_id: str) -> bool:
        return (
            self.ok
            and self.dp4_candidate_status.get(candidate_id)
            == "ACCEPTED_FOR_BOUNDED_DP4_NO_MIGRATION_OR_MANUAL_PRESERVATION"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_dp3_dp4_adjudication_check",
            "adjudication_model": ADJUDICATION_MODEL,
            "result_status": self.result_status,
            "record_path": self.record_path,
            "record_present": self.record_present,
            "record_validation_ref": self.record_validation_ref,
            "current_validation_ref": self.current_validation_ref,
            "record_status": self.record_status,
            "decision_token": self.decision_token,
            "dp3_target_status": self.dp3_target_status,
            "dp4_candidate_status": self.dp4_candidate_status,
            "dp5_next_stage_authorized": self.dp5_next_stage_authorized,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "claims": _false_claims(),
        }


def evaluate_dp3_dp4_adjudication_record(
    root: Path | str = ".",
    *,
    record_path: Path | str = DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
    validation_ref: str | None = None,
) -> Dp3Dp4AdjudicationResult:
    base = Path(root).resolve()
    path = _resolve_under_root(base, record_path)
    display_path = _display_path(path, base)
    current_ref = validation_ref or _git_head(base)
    findings: list[Dp3Dp4AdjudicationFinding] = []

    if not path.exists():
        return Dp3Dp4AdjudicationResult(
            root=base.as_posix(),
            record_path=display_path,
            record_present=False,
            record_validation_ref="",
            current_validation_ref=current_ref,
            record_status="MISSING",
            decision_token="",
            dp3_target_status={},
            dp4_candidate_status={},
            dp5_next_stage_authorized=False,
            findings=(
                Dp3Dp4AdjudicationFinding(
                    code="adjudication-record-missing",
                    message="Record DP3/DP4 bounded adjudication before clearing post-DP2 blockers.",
                    path=display_path,
                ),
            ),
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _invalid_result(base, display_path, current_ref, f"record JSON is invalid: {exc}")
    if not isinstance(data, dict):
        return _invalid_result(base, display_path, current_ref, "record root must be a JSON object")

    _validate_header(data, findings, display_path, root=base)
    dp3_status = _validate_dp3_scope(data, findings, display_path, root=base)
    dp4_status = _validate_dp4_scope(data, findings, display_path, root=base)
    _validate_dp5_boundary(data, findings, display_path)
    _validate_claims(data, findings, display_path)

    return Dp3Dp4AdjudicationResult(
        root=base.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref=str(data.get("validation_ref", "")),
        current_validation_ref=current_ref,
        record_status=str(data.get("status", "")),
        decision_token=str(data.get("decision_token", "")),
        dp3_target_status=dp3_status,
        dp4_candidate_status=dp4_status,
        dp5_next_stage_authorized=_mapping(data.get("dp5")).get("next_stage_authorized") is True,
        findings=tuple(findings),
    )


def render_dp3_dp4_adjudication_check(result: Dp3Dp4AdjudicationResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP3_DP4_ADJUDICATION_CHECK",
        f"STATUS={payload['result_status']}",
        f"RECORD={payload['record_path']}",
        f"RECORD_VALIDATION_REF={payload['record_validation_ref']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"RECORD_STATUS={payload['record_status']}",
        f"DECISION_TOKEN={payload['decision_token']}",
        f"DP5_NEXT_STAGE_AUTHORIZED={str(payload['dp5_next_stage_authorized']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for writer_id, status in sorted(result.dp3_target_status.items()):
        lines.append(f"DP3_TARGET={writer_id}|status={status}")
    for candidate_id, status in sorted(result.dp4_candidate_status.items()):
        lines.append(f"DP4_CANDIDATE={candidate_id}|status={status}")
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dp3_dp4_adjudication_check_json(
    result: Dp3Dp4AdjudicationResult,
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


def _invalid_result(
    root: Path,
    display_path: str,
    current_ref: str,
    message: str,
) -> Dp3Dp4AdjudicationResult:
    return Dp3Dp4AdjudicationResult(
        root=root.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref="",
        current_validation_ref=current_ref,
        record_status="INVALID",
        decision_token="",
        dp3_target_status={},
        dp4_candidate_status={},
        dp5_next_stage_authorized=False,
        findings=(
            Dp3Dp4AdjudicationFinding(
                code="adjudication-record-invalid-json",
                message=message,
                path=display_path,
            ),
        ),
    )


def _validate_header(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
    *,
    root: Path,
) -> None:
    if data.get("schema_version") != 1:
        _finding(findings, "schema-version-invalid", "schema_version must be 1", path)
    if data.get("kind") != "dpa_dp3_dp4_adjudication_record":
        _finding(findings, "kind-invalid", "kind must be dpa_dp3_dp4_adjudication_record", path)
    if data.get("status") != ACCEPTED_RECORD_STATUS:
        _finding(findings, "status-not-accepted", f"status must be {ACCEPTED_RECORD_STATUS}", path)
    if data.get("decision_token") != ACCEPTED_DECISION_TOKEN:
        _finding(findings, "decision-token-invalid", f"decision_token must be {ACCEPTED_DECISION_TOKEN}", path)
    validation_ref = str(data.get("validation_ref", ""))
    if not validation_ref:
        _finding(findings, "validation-ref-missing", "validation_ref must record an exact ref", path)
    elif _git_ref_exists(root, validation_ref) is False:
        _finding(findings, "validation-ref-unresolvable", f"validation_ref is not a known commit: {validation_ref}", path)
    if not str(data.get("maintainer", "")).strip():
        _finding(findings, "maintainer-missing", "maintainer instruction/adjudication text must be recorded", path)
    assessment = str(data.get("post_dp2_scope_assessment", ""))
    if not assessment:
        _finding(findings, "post-dp2-assessment-missing", "post_dp2_scope_assessment must be recorded", path)
    elif not (root / assessment).exists():
        _finding(findings, "post-dp2-assessment-path-missing", f"missing evidence path: {assessment}", path)


def _validate_dp3_scope(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
    *,
    root: Path,
) -> dict[str, str]:
    scope = _mapping(data.get("dp3_scope"))
    targets = _indexed_mappings(scope.get("rollout_targets"), "writer_id")
    statuses: dict[str, str] = {}
    for writer_id, expected in REQUIRED_DP3_TARGETS.items():
        target = targets.get(writer_id)
        target_path = f"{path}#dp3:{writer_id}"
        if target is None:
            _finding(findings, "dp3-target-missing", f"missing DP3 target {writer_id}", target_path)
            continue
        status = str(_mapping(target.get("adjudication")).get("status", ""))
        statuses[writer_id] = status
        if status != "ACCEPTED_FOR_BOUNDED_DP3_ROLLOUT":
            _finding(findings, "dp3-target-not-accepted", f"{writer_id} is not accepted for bounded DP3 rollout", target_path)
        _require_equal(target, "target_identity", expected["target_identity"], findings, target_path)
        _require_equal(target, "target_path", expected["target_path"], findings, target_path)
        _require_equal(target, "source_authority", expected["source_authority"], findings, target_path)
        _require_equal(target, "document_form", expected["document_form"], findings, target_path)
        _require_equal(target, "implementation_result_ref", expected["implementation_result_ref"], findings, target_path)
        for source_path in expected["source_paths"]:  # type: ignore[index]
            if source_path not in _string_list(target.get("source_paths")):
                _finding(findings, "dp3-source-path-missing", f"{writer_id} missing source path {source_path}", target_path)
        _require_inventory(target, "reader_inventory", findings, target_path)
        _require_inventory(target, "writer_inventory", findings, target_path)
        _require_existing_paths(target.get("rollout_evidence"), root, findings, target_path, "dp3-rollout-evidence-missing")
        _require_status_with_evidence(target, "dpa_600", "SATISFIED_FOR_CURRENT_KIT_REF", root, findings, target_path)
        _require_status_with_evidence(target, "dpa_700", "SATISFIED_FOR_CURRENT_KIT_REF", root, findings, target_path)
        tests = _mapping(target.get("tests"))
        if not _string_list(tests.get("positive")) or not _string_list(tests.get("negative")):
            _finding(findings, "dp3-tests-missing", f"{writer_id} requires positive and negative tests", target_path)
        rollback = _mapping(target.get("rollback"))
        if rollback.get("independently_revertible") is not True and rollback.get("cleanup_proven") is not True:
            _finding(findings, "dp3-rollback-not-proven", f"{writer_id} requires revertible cleanup or proven rollback", target_path)
        if _mapping(target.get("adjudication")).get("maintainer_accepted") is not True:
            _finding(findings, "dp3-maintainer-acceptance-missing", f"{writer_id} requires maintainer acceptance", target_path)
        _validate_false_claims(target, findings, target_path)
    return statuses


def _validate_dp4_scope(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
    *,
    root: Path,
) -> dict[str, str]:
    scope = _mapping(data.get("dp4_scope"))
    candidates = _indexed_mappings(scope.get("status_authority_candidates"), "id")
    statuses: dict[str, str] = {}
    for candidate_id, expected in REQUIRED_DP4_CANDIDATES.items():
        candidate = candidates.get(candidate_id)
        candidate_path = f"{path}#dp4:{candidate_id}"
        if candidate is None:
            _finding(findings, "dp4-candidate-missing", f"missing DP4 candidate {candidate_id}", candidate_path)
            continue
        status = str(_mapping(candidate.get("adjudication")).get("status", ""))
        statuses[candidate_id] = status
        if status != "ACCEPTED_FOR_BOUNDED_DP4_NO_MIGRATION_OR_MANUAL_PRESERVATION":
            _finding(findings, "dp4-candidate-not-accepted", f"{candidate_id} is not accepted for DP4 exit", candidate_path)
        for field in ("path", "decision", "document_form", "target_identity"):
            _require_equal(candidate, field, expected[field], findings, candidate_path)
        for inventory_field in (
            "reader_inventory",
            "writer_inventory",
            "generator_inventory",
            "command_update_inventory",
        ):
            _require_inventory(candidate, inventory_field, findings, candidate_path)
        _require_status_with_evidence(candidate, "dpa_600", "SATISFIED_FOR_CURRENT_KIT_REF", root, findings, candidate_path)
        _require_status_with_evidence(candidate, "dpa_700", "NO_MIGRATION_OR_MANUAL_PRESERVATION", root, findings, candidate_path)
        preservation = _mapping(candidate.get("rollback_or_preservation"))
        if preservation.get("status") not in {
            "MANUAL_PRESERVATION_RECORDED",
            "NO_MIGRATION_RECORDED",
            "COMMAND_CONTRACT_BOUNDARY_RECORDED",
        }:
            _finding(findings, "dp4-preservation-status-invalid", f"{candidate_id} preservation/no-migration status is invalid", candidate_path)
        _require_existing_paths(preservation.get("evidence"), root, findings, candidate_path, "dp4-preservation-evidence-missing")
        if not str(candidate.get("status_authority_consequences", "")).strip():
            _finding(findings, "dp4-status-authority-consequences-missing", f"{candidate_id} must record status-authority consequences", candidate_path)
        if _mapping(candidate.get("adjudication")).get("maintainer_accepted") is not True:
            _finding(findings, "dp4-maintainer-acceptance-missing", f"{candidate_id} requires maintainer acceptance", candidate_path)
        _validate_false_claims(candidate, findings, candidate_path)
    return statuses


def _validate_dp5_boundary(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    dp5 = _mapping(data.get("dp5"))
    if dp5.get("next_stage_authorized") is not False:
        _finding(findings, "dp5-stage-overclaim", "this DP3/DP4 record must not authorize a DP5 stage transition", path)
    if dp5.get("stage_transition") != "NOT_AUTHORIZED_IN_THIS_RECORD":
        _finding(findings, "dp5-stage-boundary-missing", "dp5.stage_transition must remain NOT_AUTHORIZED_IN_THIS_RECORD", path)


def _validate_claims(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    claims = _mapping(data.get("claims"))
    if claims.get("dp3_complete_for_bounded_slice") is not True:
        _finding(findings, "dp3-bounded-claim-missing", "claims.dp3_complete_for_bounded_slice must be true", path)
    if claims.get("dp4_complete_for_bounded_slice") is not True:
        _finding(findings, "dp4-bounded-claim-missing", "claims.dp4_complete_for_bounded_slice must be true", path)
    for field in FALSE_CLAIM_FIELDS:
        if claims.get(field) is not False:
            _finding(findings, "false-claim-invalid", f"claims.{field} must be false", path)


def _validate_false_claims(
    data: dict[str, Any],
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    claims = _mapping(data.get("claims"))
    for field in FALSE_CLAIM_FIELDS:
        if claims.get(field) is not False:
            _finding(findings, "false-claim-invalid", f"claims.{field} must be false", path)


def _require_equal(
    data: dict[str, Any],
    field: str,
    expected: object,
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    if data.get(field) != expected:
        _finding(findings, f"{field.replace('_', '-')}-mismatch", f"{field} must be {expected}", path)


def _require_inventory(
    data: dict[str, Any],
    field: str,
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    entries = _list_of_mappings(data.get(field))
    if not entries:
        _finding(findings, f"{field.replace('_', '-')}-missing", f"{field} must contain at least one entry", path)
        return
    for index, entry in enumerate(entries):
        if not str(entry.get("id") or entry.get("command") or entry.get("path") or "").strip():
            _finding(findings, f"{field.replace('_', '-')}-entry-id-missing", f"{field}[{index}] needs id, command or path", path)


def _require_status_with_evidence(
    data: dict[str, Any],
    field: str,
    expected_status: str,
    root: Path,
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
) -> None:
    payload = _mapping(data.get(field))
    if payload.get("status") != expected_status:
        _finding(findings, f"{field.replace('_', '-')}-status-invalid", f"{field}.status must be {expected_status}", path)
    _require_existing_paths(payload.get("evidence"), root, findings, path, f"{field.replace('_', '-')}-evidence-missing")


def _require_existing_paths(
    value: Any,
    root: Path,
    findings: list[Dp3Dp4AdjudicationFinding],
    path: str,
    code: str,
) -> None:
    paths = _string_list(value)
    if not paths:
        _finding(findings, code, "evidence paths must be a non-empty string list", path)
        return
    for evidence_path in paths:
        if not (root / evidence_path).exists():
            _finding(findings, code, f"missing evidence path: {evidence_path}", path)


def _indexed_mappings(value: Any, key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in _list_of_mappings(value):
        item_key = item.get(key)
        if isinstance(item_key, str) and item_key:
            result[item_key] = item
    return result


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _finding(
    findings: list[Dp3Dp4AdjudicationFinding],
    code: str,
    message: str,
    path: str,
) -> None:
    findings.append(Dp3Dp4AdjudicationFinding(code=code, message=message, path=path))


def _false_claims() -> dict[str, bool]:
    return {
        "dp3_complete": False,
        "dp4_complete": False,
        "dp5_strict_enforced": False,
        "kit_wide_dpa_conformance_claimed": False,
        "production_mutation_performed": False,
        "generated_outputs_manually_patched": False,
        "stable_dpa_claimed": False,
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
