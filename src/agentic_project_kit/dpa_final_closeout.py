from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_dp5_strict_gate import evaluate_dp5_strict_gate
from agentic_project_kit.dpa_post_dp2_scope_assessment import evaluate_post_dp2_scope_assessment
from agentic_project_kit.workspace import load_workspace

DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/DPA_FINAL_CLOSEOUT_RECORD_20260801.json"
)
DPA_FINAL_CLOSEOUT_MODEL = "dpa-final-closeout-v1"
VALID_STATUS = "VALID_DPA_FINAL_CLOSEOUT_RECORD"
ACCEPTED_STATUS = "DPA_DP3_DP5_FINAL_CLOSEOUT_RECORDED"
ACCEPTED_TOKEN = "DPA_DP3_DP5_FINAL_CLOSEOUT_AUTHORIZED"
READY_FOR_CLOSEOUT_STATUS = "READY_FOR_FINAL_CLOSEOUT_RECORD"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")


@dataclass(frozen=True)
class DpaFinalCloseoutFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class DpaFinalCloseoutResult:
    root: str
    record_path: str
    record_present: bool
    record_validation_ref: str
    current_validation_ref: str
    record_status: str
    decision_token: str
    post_dp2_status: str
    strict_gate_status: str
    dp2_implementation_percent: int
    kit_wide_dpa_conformance_claimed: bool
    stable_dpa_claimed: bool
    findings: tuple[DpaFinalCloseoutFinding, ...]

    @property
    def ok(self) -> bool:
        return self.result_status == VALID_STATUS

    @property
    def result_status(self) -> str:
        if not self.record_present:
            return "MISSING_DPA_FINAL_CLOSEOUT_RECORD"
        if self.findings:
            return "INVALID_DPA_FINAL_CLOSEOUT_RECORD"
        return VALID_STATUS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_final_closeout_check",
            "closeout_model": DPA_FINAL_CLOSEOUT_MODEL,
            "result_status": self.result_status,
            "record_path": self.record_path,
            "record_present": self.record_present,
            "record_validation_ref": self.record_validation_ref,
            "current_validation_ref": self.current_validation_ref,
            "record_status": self.record_status,
            "decision_token": self.decision_token,
            "post_dp2_status": self.post_dp2_status,
            "strict_gate_status": self.strict_gate_status,
            "dp2_implementation_percent": self.dp2_implementation_percent,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "claims": {
                "kit_wide_dpa_conformance_claimed": self.kit_wide_dpa_conformance_claimed,
                "stable_dpa_claimed": self.stable_dpa_claimed,
                "production_mutation_performed": False,
                "generated_outputs_manually_patched": False,
            },
        }


def evaluate_dpa_final_closeout_record(
    root: Path | str = ".",
    *,
    record_path: Path | str = DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH,
    validation_ref: str | None = None,
) -> DpaFinalCloseoutResult:
    base = Path(root).resolve()
    path = _resolve_under_root(base, record_path)
    display_path = _display_path(path, base)
    current_ref = validation_ref or _git_head(base)

    if not path.exists():
        return DpaFinalCloseoutResult(
            root=base.as_posix(),
            record_path=display_path,
            record_present=False,
            record_validation_ref="",
            current_validation_ref=current_ref,
            record_status="MISSING",
            decision_token="",
            post_dp2_status="",
            strict_gate_status="",
            dp2_implementation_percent=0,
            kit_wide_dpa_conformance_claimed=False,
            stable_dpa_claimed=False,
            findings=(
                DpaFinalCloseoutFinding(
                    code="final-closeout-record-missing",
                    message="Record exact DP1-DP5 closeout evidence before claiming Kit-wide DPA conformance.",
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

    findings: list[DpaFinalCloseoutFinding] = []
    _validate_header(data, findings, display_path, root=base)
    scope = _mapping(data.get("closeout_scope"))
    criteria = _mapping(data.get("criteria"))
    claims = _mapping(data.get("claims"))
    _validate_scope(scope, findings, display_path, root=base)
    post_payload = _load_json_path(
        scope.get("post_dp2_scope_assessment"),
        base,
        findings,
        display_path,
        "post-dp2-assessment",
    )
    strict_payload = _load_json_path(
        scope.get("dp5_strict_gate"),
        base,
        findings,
        display_path,
        "strict-gate",
    )
    post_status = str(post_payload.get("kit_wide_dpa_status", "")) if post_payload else ""
    strict_status = str(strict_payload.get("result_status", "")) if strict_payload else ""
    dp2_percent = int(post_payload.get("dp2_implementation_percent", 0)) if post_payload else 0
    _validate_post_dp2_payload(post_payload, findings, display_path)
    _validate_strict_gate_payload(strict_payload, findings, display_path)
    _validate_live_state(data, base, findings, display_path)
    _validate_criteria(criteria, findings, display_path)
    _validate_rollback(data, findings, display_path, root=base)
    _validate_claims(claims, findings, display_path)

    return DpaFinalCloseoutResult(
        root=base.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref=str(data.get("validation_ref", "")),
        current_validation_ref=current_ref,
        record_status=str(data.get("status", "")),
        decision_token=str(data.get("decision_token", "")),
        post_dp2_status=post_status,
        strict_gate_status=strict_status,
        dp2_implementation_percent=dp2_percent,
        kit_wide_dpa_conformance_claimed=claims.get("kit_wide_dpa_conformance_claimed") is True,
        stable_dpa_claimed=claims.get("stable_dpa_claimed") is True,
        findings=tuple(findings),
    )


def render_dpa_final_closeout_check(result: DpaFinalCloseoutResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_FINAL_CLOSEOUT_CHECK",
        f"STATUS={payload['result_status']}",
        f"RECORD={payload['record_path']}",
        f"RECORD_VALIDATION_REF={payload['record_validation_ref']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"RECORD_STATUS={payload['record_status']}",
        f"DECISION_TOKEN={payload['decision_token']}",
        f"POST_DP2_STATUS={payload['post_dp2_status']}",
        f"STRICT_GATE_STATUS={payload['strict_gate_status']}",
        f"DP2_IMPLEMENTATION_PERCENT={payload['dp2_implementation_percent']}",
        f"KIT_WIDE_DPA_CONFORMANCE_CLAIMED={str(payload['claims']['kit_wide_dpa_conformance_claimed']).lower()}",
        f"STABLE_DPA_CLAIMED={str(payload['claims']['stable_dpa_claimed']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dpa_final_closeout_check_json(
    result: DpaFinalCloseoutResult,
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


def _validate_header(
    data: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
    *,
    root: Path,
) -> None:
    if data.get("schema_version") != 1:
        _finding(findings, "schema-version-invalid", "schema_version must be 1", path)
    if data.get("kind") != "dpa_final_closeout_record":
        _finding(findings, "kind-invalid", "kind must be dpa_final_closeout_record", path)
    if data.get("status") != ACCEPTED_STATUS:
        _finding(findings, "status-not-recorded", f"status must be {ACCEPTED_STATUS}", path)
    if data.get("decision_token") != ACCEPTED_TOKEN:
        _finding(findings, "decision-token-invalid", f"decision_token must be {ACCEPTED_TOKEN}", path)
    validation_ref = str(data.get("validation_ref", ""))
    if not validation_ref:
        _finding(findings, "validation-ref-missing", "validation_ref must record an exact ref", path)
    elif _git_ref_exists(root, validation_ref) is False:
        _finding(findings, "validation-ref-unresolvable", f"validation_ref is not a known commit: {validation_ref}", path)
    if not str(data.get("maintainer", "")).strip():
        _finding(findings, "maintainer-missing", "maintainer authorization text must be recorded", path)


def _validate_scope(
    scope: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
    *,
    root: Path,
) -> None:
    if scope.get("id") != "DPA_KIT_WIDE_DPA_DP1_DP5_ACCEPTED_SCOPE":
        _finding(findings, "closeout-scope-id-invalid", "closeout_scope.id must name the accepted DP1-DP5 scope", path)
    _require_existing_paths(scope.get("evidence"), root, findings, path, "closeout-scope-evidence-missing")
    for key in (
        "dp1_readiness_record",
        "dp2_maintainer_record",
        "dp3_dp4_adjudication_record",
        "dp5_strict_stage_record",
        "post_dp2_scope_assessment",
        "dp5_strict_gate",
    ):
        value = str(scope.get(key, "")).strip()
        if not value:
            _finding(findings, f"{key.replace('_', '-')}-missing", f"closeout_scope.{key} must be set", path)
        elif not (root / value).exists():
            _finding(findings, f"{key.replace('_', '-')}-missing", f"missing closeout scope path: {value}", path)


def _validate_post_dp2_payload(
    payload: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
) -> None:
    if not payload:
        return
    if payload.get("kind") != "dpa_post_dp2_scope_assessment":
        _finding(findings, "post-dp2-kind-invalid", "post-DP2 evidence must be dpa_post_dp2_scope_assessment", path)
    if payload.get("kit_wide_dpa_status") != READY_FOR_CLOSEOUT_STATUS:
        _finding(findings, "post-dp2-status-invalid", f"post-DP2 status must be {READY_FOR_CLOSEOUT_STATUS}", path)
    if payload.get("final_closeout_ready") is not True:
        _finding(findings, "post-dp2-not-closeout-ready", "post-DP2 evidence must set final_closeout_ready=true", path)
    if payload.get("blocker_count") != 0:
        _finding(findings, "post-dp2-blockers-present", "post-DP2 evidence must have blocker_count=0", path)
    if payload.get("dp2_implementation_percent") != 100:
        _finding(findings, "dp2-percent-invalid", "DP2 selected scope implementation percent must remain 100", path)
    if payload.get("kit_wide_dpa_conformance_claimed") is not False:
        _finding(findings, "post-dp2-overclaims-conformance", "post-DP2 evidence must not itself claim conformance", path)
    dp5 = _mapping(payload.get("dp5"))
    if dp5.get("status") != "STRICT_ACTIVE_READY_FOR_FINAL_CLOSEOUT":
        _finding(findings, "dp5-status-invalid", "DP5 must be strict-active and ready for final closeout", path)
    if dp5.get("warning_count") != 0:
        _finding(findings, "dp5-warnings-present", "DP5 warning_count must be 0", path)


def _validate_strict_gate_payload(
    payload: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
) -> None:
    if not payload:
        return
    if payload.get("kind") != "dpa_dp5_strict_gate":
        _finding(findings, "strict-gate-kind-invalid", "strict gate evidence must be dpa_dp5_strict_gate", path)
    if payload.get("result_status") != "PASS":
        _finding(findings, "strict-gate-not-pass", "strict gate result must be PASS", path)
    if payload.get("active_stage") != "strict":
        _finding(findings, "strict-gate-stage-invalid", "strict gate active_stage must be strict", path)
    if payload.get("blocker_count") != 0:
        _finding(findings, "strict-gate-blockers-present", "strict gate blocker_count must be 0", path)
    if payload.get("warning_count") != 0:
        _finding(findings, "strict-gate-warnings-present", "strict gate warning_count must be 0", path)
    if payload.get("final_closeout_ready") is not True:
        _finding(findings, "strict-gate-not-closeout-ready", "strict gate must set final_closeout_ready=true", path)
    claims = _mapping(payload.get("claims"))
    if claims.get("kit_wide_dpa_conformance_claimed") is not False:
        _finding(findings, "strict-gate-overclaims-conformance", "strict gate must not itself claim conformance", path)


def _validate_live_state(
    data: dict[str, Any],
    root: Path,
    findings: list[DpaFinalCloseoutFinding],
    path: str,
) -> None:
    validation_ref = str(data.get("validation_ref", ""))
    post = evaluate_post_dp2_scope_assessment(root, validation_ref=validation_ref)
    if post.findings or not post.final_closeout_ready or post.blocker_count != 0:
        _finding(findings, "live-post-dp2-not-ready", "current post-DP2 evaluation must remain closeout-ready", path)
    strict = evaluate_dp5_strict_gate(root, validation_ref=validation_ref)
    if not strict.ok:
        _finding(findings, "live-strict-gate-not-pass", "current strict gate evaluation must pass", path)


def _validate_criteria(
    criteria: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
) -> None:
    expected = {
        "dp2_selected_scope_implementation_percent": 100,
        "post_dp2_kit_wide_dpa_status": READY_FOR_CLOSEOUT_STATUS,
        "post_dp2_final_closeout_ready": True,
        "blocker_count": 0,
        "warning_count": 0,
        "dp3_bounded_rollout_adjudicated": True,
        "dp4_status_authority_adjudicated": True,
        "dp5_strict_lifecycle_adopted": True,
        "strict_gate_result_status": "PASS",
        "strict_gate_active_stage": "strict",
        "strict_gate_blocker_count": 0,
    }
    for key, value in expected.items():
        if criteria.get(key) != value:
            _finding(findings, f"criteria-{key.replace('_', '-')}-invalid", f"criteria.{key} must be {value!r}", path)


def _validate_rollback(
    data: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
    *,
    root: Path,
) -> None:
    rollback = _mapping(data.get("rollback"))
    if rollback.get("tested_or_adjudicated") is not True:
        _finding(findings, "rollback-not-proven", "rollback must be tested or explicitly adjudicated", path)
    _require_existing_paths(rollback.get("evidence"), root, findings, path, "rollback-evidence-missing")


def _validate_claims(
    claims: dict[str, Any],
    findings: list[DpaFinalCloseoutFinding],
    path: str,
) -> None:
    required_true = (
        "dp3_bounded_rollout_complete",
        "dp4_status_authority_discovery_complete",
        "dp5_strict_lifecycle_complete",
        "strict_enforcement_claimed",
        "kit_wide_dpa_conformance_claimed",
    )
    for field in required_true:
        if claims.get(field) is not True:
            _finding(findings, "claim-invalid", f"claims.{field} must be true", path)
    required_false = (
        "stable_dpa_claimed",
        "production_mutation_performed",
        "generated_outputs_manually_patched",
    )
    for field in required_false:
        if claims.get(field) is not False:
            _finding(findings, "false-claim-invalid", f"claims.{field} must be false", path)
    if claims.get("claim_scope") != "accepted-kit-dpa-dp1-dp5-implementation-scope":
        _finding(findings, "claim-scope-invalid", "claims.claim_scope must be exact and bounded", path)


def _load_json_path(
    value: Any,
    root: Path,
    findings: list[DpaFinalCloseoutFinding],
    path: str,
    label: str,
) -> dict[str, Any]:
    candidate = str(value or "").strip()
    if not candidate:
        _finding(findings, f"{label}-path-missing", f"{label} path must be set", path)
        return {}
    resolved = root / candidate
    if not resolved.exists():
        _finding(findings, f"{label}-path-missing", f"missing {label} path: {candidate}", path)
        return {}
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _finding(findings, f"{label}-invalid-json", f"{label} JSON is invalid: {exc}", candidate)
        return {}
    if not isinstance(payload, dict):
        _finding(findings, f"{label}-invalid", f"{label} JSON must be an object", candidate)
        return {}
    return payload


def _invalid_result(
    root: Path,
    display_path: str,
    current_ref: str,
    message: str,
) -> DpaFinalCloseoutResult:
    return DpaFinalCloseoutResult(
        root=root.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref="",
        current_validation_ref=current_ref,
        record_status="INVALID",
        decision_token="",
        post_dp2_status="",
        strict_gate_status="",
        dp2_implementation_percent=0,
        kit_wide_dpa_conformance_claimed=False,
        stable_dpa_claimed=False,
        findings=(
            DpaFinalCloseoutFinding(
                code="final-closeout-record-invalid-json",
                message=message,
                path=display_path,
            ),
        ),
    )


def _require_existing_paths(
    value: Any,
    root: Path,
    findings: list[DpaFinalCloseoutFinding],
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


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _finding(
    findings: list[DpaFinalCloseoutFinding],
    code: str,
    message: str,
    path: str,
) -> None:
    findings.append(DpaFinalCloseoutFinding(code=code, message=message, path=path))


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "UNKNOWN"
    return completed.stdout.strip()


def _git_ref_exists(root: Path, ref: str) -> bool | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


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
