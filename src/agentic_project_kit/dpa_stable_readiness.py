from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_dp5_strict_gate import evaluate_dp5_strict_gate
from agentic_project_kit.dpa_final_closeout import (
    DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH,
    VALID_STATUS as VALID_FINAL_CLOSEOUT_STATUS,
    evaluate_dpa_final_closeout_record,
)
from agentic_project_kit.dpa_post_dp2_scope_assessment import (
    evaluate_post_dp2_scope_assessment,
)
from agentic_project_kit.dpa_probe_002_readiness import (
    evaluate_probe_002_lifecycle_readiness,
)
from agentic_project_kit.dpa_probe_003_readiness import (
    evaluate_probe_003_workflow_readiness,
)
from agentic_project_kit.dpa_probe_004_readiness import (
    evaluate_probe_004_migration_readiness,
)
from agentic_project_kit.dpa_readiness import evaluate_dpa_readiness
from agentic_project_kit.dpa_renderer_readiness import evaluate_renderer_probe_readiness
from agentic_project_kit.workspace import load_workspace

DEFAULT_DPA_STABLE_PROMOTION_RECORD_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/DPA_STABLE_PROMOTION_RECORD_20260801.json"
)
DPA_STABLE_PROMOTION_MODEL = "dpa-stable-promotion-v1"
READY_FOR_STABLE_PROMOTION_STATUS = "READY_FOR_STABLE_DPA_PROMOTION"
VALID_STABLE_PROMOTION_STATUS = "VALID_DPA_STABLE_PROMOTION_RECORD"
BLOCKED_STATUS = "BLOCKED_FOR_STABLE_DPA_PROMOTION"
INVALID_STATUS = "INVALID_DPA_STABLE_PROMOTION_RECORD"
PROMOTION_RECORD_STATUS = "DPA_STABLE_PROMOTION_RECORDED"
PROMOTION_DECISION_TOKEN = "DPA_STABLE_PROMOTION_AUTHORIZED"
STABLE_SCOPE_ID = "DPA_STABLE_ACCEPTED_KIT_SCOPE"
STABLE_CLAIM_SCOPE = "accepted-kit-dpa-dp1-dp5-stable-implementation-scope"
EXTERNAL_REPO_STATUS = "DPA_CAPABLE_WITH_FRESH_PER_REPO_ASSESSMENT"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")

SPEC_FILES: tuple[tuple[str, str], ...] = (
    ("DPA-000", "docs/architecture/dpa/specs/DPA-000-VISION.md"),
    ("DPA-100", "docs/architecture/dpa/specs/DPA-100-FOUNDATIONS.md"),
    ("DPA-200", "docs/architecture/dpa/specs/DPA-200-DOCUMENT-MODEL.md"),
    ("DPA-200-FORM-MATRIX", "docs/architecture/dpa/specs/DPA-200-DOCUMENT-FORM-MATRIX.md"),
    ("DPA-300", "docs/architecture/dpa/specs/DPA-300-REGISTRY-LIFECYCLE-INTEGRATION.md"),
    ("DPA-400", "docs/architecture/dpa/specs/DPA-400-RENDERER-CONTRACT.md"),
    ("DPA-500", "docs/architecture/dpa/specs/DPA-500-FRESHNESS-AND-GATES.md"),
    ("DPA-600", "docs/architecture/dpa/specs/DPA-600-CONCURRENCY.md"),
    ("DPA-700", "docs/architecture/dpa/specs/DPA-700-MIGRATION.md"),
    ("DPA-800", "docs/architecture/dpa/specs/DPA-800-DP1-DP5.md"),
    ("DPA-900", "docs/architecture/dpa/specs/DPA-900-FUTURE.md"),
)
BASELINE_STABLE_SPEC_IDS = frozenset({"DPA-000", "DPA-100"})
PROMOTED_SPEC_IDS = tuple(spec_id for spec_id, _path in SPEC_FILES)


@dataclass(frozen=True)
class DpaStableReadinessFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class DpaSpecStatus:
    spec_id: str
    path: str
    status: str
    present: bool

    @property
    def stable(self) -> bool:
        return self.present and self.status == "stable"

    @property
    def promotable(self) -> bool:
        return self.present and self.status in {"review-ready", "stable"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.spec_id,
            "path": self.path,
            "status": self.status,
            "present": self.present,
            "stable": self.stable,
            "promotable": self.promotable,
        }


@dataclass(frozen=True)
class DpaStableReadinessResult:
    root: str
    current_validation_ref: str
    promotion_record_path: str
    promotion_record_present: bool
    record_validation_ref: str
    record_status: str
    decision_token: str
    dp2_status: str
    dp2_implementation_percent: int
    post_dp2_status: str
    strict_gate_status: str
    final_closeout_status: str
    kit_wide_dpa_conformance_claimed: bool
    stable_dpa_claimed: bool
    external_repo_conformance_claimed: bool
    probe_statuses: dict[str, str]
    spec_statuses: tuple[DpaSpecStatus, ...]
    findings: tuple[DpaStableReadinessFinding, ...]

    @property
    def ready_for_promotion(self) -> bool:
        return not self.promotion_record_present and not self.findings

    @property
    def stable_promoted(self) -> bool:
        return self.promotion_record_present and not self.findings

    @property
    def ok(self) -> bool:
        return self.ready_for_promotion or self.stable_promoted

    @property
    def result_status(self) -> str:
        if self.promotion_record_present:
            return VALID_STABLE_PROMOTION_STATUS if not self.findings else INVALID_STATUS
        return READY_FOR_STABLE_PROMOTION_STATUS if not self.findings else BLOCKED_STATUS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_stable_readiness_check",
            "promotion_model": DPA_STABLE_PROMOTION_MODEL,
            "result_status": self.result_status,
            "current_validation_ref": self.current_validation_ref,
            "promotion_record_path": self.promotion_record_path,
            "promotion_record_present": self.promotion_record_present,
            "record_validation_ref": self.record_validation_ref,
            "record_status": self.record_status,
            "decision_token": self.decision_token,
            "dp2_status": self.dp2_status,
            "dp2_implementation_percent": self.dp2_implementation_percent,
            "post_dp2_status": self.post_dp2_status,
            "strict_gate_status": self.strict_gate_status,
            "final_closeout_status": self.final_closeout_status,
            "probe_statuses": self.probe_statuses,
            "spec_statuses": [item.as_dict() for item in self.spec_statuses],
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "foreign_repo_management": {
                "status": EXTERNAL_REPO_STATUS,
                "automatic_external_repo_conformance_claimed": (
                    self.external_repo_conformance_claimed
                ),
                "requires_fresh_per_repo_inventory": True,
                "requires_fresh_per_repo_dpa_600_700_evidence": True,
                "requires_maintainer_authorized_scope": True,
            },
            "claims": {
                "kit_wide_dpa_conformance_claimed": self.kit_wide_dpa_conformance_claimed,
                "stable_dpa_claimed": self.stable_dpa_claimed,
                "production_mutation_performed": False,
                "generated_outputs_manually_patched": False,
                "external_repo_conformance_claimed": self.external_repo_conformance_claimed,
            },
        }


def evaluate_dpa_stable_readiness(
    root: Path | str = ".",
    *,
    record_path: Path | str = DEFAULT_DPA_STABLE_PROMOTION_RECORD_PATH,
    validation_ref: str | None = None,
) -> DpaStableReadinessResult:
    base = Path(root).resolve()
    current_ref = validation_ref or _git_head(base)
    promotion_path = _resolve_under_root(base, record_path)
    display_path = _display_path(promotion_path, base)
    spec_statuses = tuple(_spec_status(base, spec_id, path) for spec_id, path in SPEC_FILES)
    findings: list[DpaStableReadinessFinding] = []

    _validate_spec_prerequisites(spec_statuses, findings)

    dp2 = evaluate_dpa_readiness(base)
    if not dp2.dp2_ready:
        _finding(findings, "dp2-not-authorized", "DP2 readiness must remain authorized", dp2.path)
    if dp2.implementation_percent != 100:
        _finding(
            findings,
            "dp2-percent-not-100",
            "DP2 selected-scope implementation percent must remain 100",
            dp2.path,
        )

    post_dp2 = evaluate_post_dp2_scope_assessment(base, validation_ref=current_ref)
    if not post_dp2.final_closeout_ready or post_dp2.blocker_count != 0:
        _finding(
            findings,
            "post-dp2-not-closeout-ready",
            "Post-DP2 DP3-DP5 assessment must remain ready for final closeout",
            post_dp2.readiness_record,
        )

    strict_gate = evaluate_dp5_strict_gate(base, validation_ref=current_ref)
    if not strict_gate.ok:
        _finding(
            findings,
            "dp5-strict-gate-not-pass",
            "DP5 strict gate must pass with zero configured blockers",
            display_path,
        )

    final_closeout = evaluate_dpa_final_closeout_record(base, validation_ref=current_ref)
    if not final_closeout.ok:
        _finding(
            findings,
            "final-closeout-invalid",
            "Final DP1-DP5 closeout record must be structurally valid",
            final_closeout.record_path,
        )
    if final_closeout.kit_wide_dpa_conformance_claimed is not True:
        _finding(
            findings,
            "kit-wide-conformance-not-claimed-by-closeout",
            "Final closeout must own the bounded Kit-wide DPA conformance claim",
            final_closeout.record_path,
        )
    if final_closeout.stable_dpa_claimed is not False:
        _finding(
            findings,
            "final-closeout-overclaims-stable",
            "Final closeout must leave stable DPA to the Stable Promotion record",
            final_closeout.record_path,
        )

    probe_statuses = _probe_statuses(base, current_ref, findings)

    record_data: dict[str, Any] = {}
    if promotion_path.exists():
        record_data = _load_promotion_record(promotion_path, base, findings)
        if record_data:
            _validate_promotion_record(record_data, base, display_path, spec_statuses, findings)

    claims = _mapping(record_data.get("claims"))
    external_scope = _mapping(record_data.get("external_repo_management"))

    return DpaStableReadinessResult(
        root=base.as_posix(),
        current_validation_ref=current_ref,
        promotion_record_path=display_path,
        promotion_record_present=promotion_path.exists(),
        record_validation_ref=str(record_data.get("validation_ref", "")),
        record_status=str(record_data.get("status", "")),
        decision_token=str(record_data.get("decision_token", "")),
        dp2_status=dp2.status,
        dp2_implementation_percent=dp2.implementation_percent,
        post_dp2_status=post_dp2.kit_wide_dpa_status,
        strict_gate_status=strict_gate.result_status,
        final_closeout_status=final_closeout.result_status,
        kit_wide_dpa_conformance_claimed=claims.get("kit_wide_dpa_conformance_claimed") is True,
        stable_dpa_claimed=claims.get("stable_dpa_claimed") is True,
        external_repo_conformance_claimed=(
            claims.get("external_repo_conformance_claimed") is True
            or external_scope.get("automatic_external_repo_conformance_claimed") is True
        ),
        probe_statuses=probe_statuses,
        spec_statuses=spec_statuses,
        findings=tuple(findings),
    )


def render_dpa_stable_readiness(result: DpaStableReadinessResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_STABLE_READINESS_CHECK",
        f"STATUS={payload['result_status']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"PROMOTION_RECORD={payload['promotion_record_path']}",
        f"PROMOTION_RECORD_PRESENT={str(payload['promotion_record_present']).lower()}",
        f"RECORD_VALIDATION_REF={payload['record_validation_ref']}",
        f"RECORD_STATUS={payload['record_status']}",
        f"DECISION_TOKEN={payload['decision_token']}",
        f"DP2_STATUS={payload['dp2_status']}",
        f"DP2_IMPLEMENTATION_PERCENT={payload['dp2_implementation_percent']}",
        f"POST_DP2_STATUS={payload['post_dp2_status']}",
        f"STRICT_GATE_STATUS={payload['strict_gate_status']}",
        f"FINAL_CLOSEOUT_STATUS={payload['final_closeout_status']}",
        f"KIT_WIDE_DPA_CONFORMANCE_CLAIMED={str(payload['claims']['kit_wide_dpa_conformance_claimed']).lower()}",
        f"STABLE_DPA_CLAIMED={str(payload['claims']['stable_dpa_claimed']).lower()}",
        f"EXTERNAL_REPO_CONFORMANCE_CLAIMED={str(payload['claims']['external_repo_conformance_claimed']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for spec in payload["spec_statuses"]:
        lines.append(f"SPEC={spec['id']}|status={spec['status']}|stable={str(spec['stable']).lower()}")
    for probe_id, status in payload["probe_statuses"].items():
        lines.append(f"PROBE={probe_id}|status={status}")
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dpa_stable_readiness_json(
    result: DpaStableReadinessResult,
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


def _validate_spec_prerequisites(
    specs: tuple[DpaSpecStatus, ...],
    findings: list[DpaStableReadinessFinding],
) -> None:
    for spec in specs:
        if not spec.present:
            _finding(findings, "spec-missing", f"{spec.spec_id} spec file is missing", spec.path)
            continue
        if spec.spec_id in BASELINE_STABLE_SPEC_IDS and not spec.stable:
            _finding(
                findings,
                "baseline-spec-not-stable",
                f"{spec.spec_id} must already be stable before DPA stable promotion",
                spec.path,
            )
        elif not spec.promotable:
            _finding(
                findings,
                "spec-not-promotable",
                f"{spec.spec_id} must be review-ready or stable before DPA stable promotion",
                spec.path,
            )


def _validate_promotion_record(
    data: dict[str, Any],
    root: Path,
    path: str,
    specs: tuple[DpaSpecStatus, ...],
    findings: list[DpaStableReadinessFinding],
) -> None:
    if data.get("schema_version") != 1:
        _finding(findings, "schema-version-invalid", "schema_version must be 1", path)
    if data.get("kind") != "dpa_stable_promotion_record":
        _finding(findings, "kind-invalid", "kind must be dpa_stable_promotion_record", path)
    if data.get("status") != PROMOTION_RECORD_STATUS:
        _finding(findings, "status-invalid", f"status must be {PROMOTION_RECORD_STATUS}", path)
    if data.get("decision_token") != PROMOTION_DECISION_TOKEN:
        _finding(
            findings,
            "decision-token-invalid",
            f"decision_token must be {PROMOTION_DECISION_TOKEN}",
            path,
        )
    validation_ref = str(data.get("validation_ref", "")).strip()
    if not validation_ref:
        _finding(findings, "validation-ref-missing", "validation_ref must record an exact ref", path)
    elif _git_ref_exists(root, validation_ref) is False:
        _finding(
            findings,
            "validation-ref-unresolvable",
            f"validation_ref is not a known commit: {validation_ref}",
            path,
        )
    if not str(data.get("maintainer", "")).strip():
        _finding(findings, "maintainer-missing", "maintainer authorization text must be recorded", path)

    scope = _mapping(data.get("stable_scope"))
    criteria = _mapping(data.get("criteria"))
    rollback = _mapping(data.get("rollback"))
    claims = _mapping(data.get("claims"))
    external_scope = _mapping(data.get("external_repo_management"))

    _validate_scope(scope, root, path, specs, findings)
    _validate_criteria(criteria, path, findings)
    _validate_rollback(rollback, root, path, findings)
    _validate_claims(claims, path, findings)
    _validate_external_repo_scope(external_scope, path, findings)


def _validate_scope(
    scope: dict[str, Any],
    root: Path,
    path: str,
    specs: tuple[DpaSpecStatus, ...],
    findings: list[DpaStableReadinessFinding],
) -> None:
    if scope.get("id") != STABLE_SCOPE_ID:
        _finding(findings, "stable-scope-id-invalid", f"stable_scope.id must be {STABLE_SCOPE_ID}", path)
    _require_existing_paths(scope.get("evidence"), root, findings, path, "stable-scope-evidence-missing")
    final_closeout_record = str(scope.get("final_closeout_record", "")).strip()
    if final_closeout_record != DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH.as_posix():
        _finding(
            findings,
            "final-closeout-record-path-invalid",
            "stable_scope.final_closeout_record must point at the final closeout record",
            path,
        )
    _load_stable_readiness_evidence(scope.get("stable_readiness_evidence"), root, path, findings)

    spec_map = {spec.spec_id: spec for spec in specs}
    promoted_specs = _promoted_spec_map(scope.get("promoted_specs"), path, findings)
    for spec_id in PROMOTED_SPEC_IDS:
        promoted = promoted_specs.get(spec_id)
        actual = spec_map.get(spec_id)
        if promoted is None:
            _finding(findings, "promoted-spec-missing", f"stable_scope.promoted_specs missing {spec_id}", path)
            continue
        if promoted.get("path") != actual.path:
            _finding(
                findings,
                "promoted-spec-path-invalid",
                f"stable_scope.promoted_specs path mismatch for {spec_id}",
                f"{path}:stable_scope.promoted_specs.{spec_id}",
            )
        if promoted.get("to_status") != "stable":
            _finding(
                findings,
                "promoted-spec-to-status-invalid",
                f"{spec_id} to_status must be stable",
                f"{path}:stable_scope.promoted_specs.{spec_id}",
            )
        if not _string_list(promoted.get("evidence")):
            _finding(
                findings,
                "promoted-spec-evidence-missing",
                f"{spec_id} promotion evidence must be listed",
                f"{path}:stable_scope.promoted_specs.{spec_id}",
            )
        if actual and not actual.stable:
            _finding(
                findings,
                "spec-not-stable-after-promotion",
                f"{spec_id} header status must be stable after promotion",
                actual.path,
            )


def _validate_criteria(
    criteria: dict[str, Any],
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> None:
    expected = {
        "dpa_000_to_dpa_900_stable": True,
        "dp2_selected_scope_implementation_percent": 100,
        "final_closeout_result_status": VALID_FINAL_CLOSEOUT_STATUS,
        "post_dp2_kit_wide_dpa_status": "READY_FOR_FINAL_CLOSEOUT_RECORD",
        "strict_gate_result_status": "PASS",
        "stable_readiness_result_status": READY_FOR_STABLE_PROMOTION_STATUS,
        "blocker_count": 0,
        "warning_count": 0,
    }
    for key, value in expected.items():
        if criteria.get(key) != value:
            _finding(findings, f"criteria-{key.replace('_', '-')}-invalid", f"criteria.{key} must be {value!r}", path)


def _validate_rollback(
    rollback: dict[str, Any],
    root: Path,
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> None:
    if rollback.get("tested_or_adjudicated") is not True:
        _finding(findings, "rollback-not-adjudicated", "rollback must be tested or adjudicated", path)
    if rollback.get("production_mutation_required") is not False:
        _finding(findings, "rollback-production-mutation-invalid", "rollback must not require production mutation", path)
    _require_existing_paths(rollback.get("evidence"), root, findings, path, "rollback-evidence-missing")


def _validate_claims(
    claims: dict[str, Any],
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> None:
    required_true = ("kit_wide_dpa_conformance_claimed", "stable_dpa_claimed")
    for field in required_true:
        if claims.get(field) is not True:
            _finding(findings, "claim-invalid", f"claims.{field} must be true", path)
    required_false = (
        "production_mutation_performed",
        "generated_outputs_manually_patched",
        "external_repo_conformance_claimed",
    )
    for field in required_false:
        if claims.get(field) is not False:
            _finding(findings, "false-claim-invalid", f"claims.{field} must be false", path)
    if claims.get("claim_scope") != STABLE_CLAIM_SCOPE:
        _finding(findings, "claim-scope-invalid", f"claims.claim_scope must be {STABLE_CLAIM_SCOPE}", path)


def _validate_external_repo_scope(
    external_scope: dict[str, Any],
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> None:
    if external_scope.get("status") != EXTERNAL_REPO_STATUS:
        _finding(
            findings,
            "external-repo-status-invalid",
            f"external_repo_management.status must be {EXTERNAL_REPO_STATUS}",
            path,
        )
    if external_scope.get("automatic_external_repo_conformance_claimed") is not False:
        _finding(
            findings,
            "external-repo-overclaim",
            "external repo conformance must not be claimed without per-repo evidence",
            path,
        )
    for key in (
        "requires_fresh_per_repo_inventory",
        "requires_fresh_per_repo_dpa_600_700_evidence",
        "requires_maintainer_authorized_scope",
    ):
        if external_scope.get(key) is not True:
            _finding(findings, "external-repo-guardrail-missing", f"{key} must be true", path)


def _probe_statuses(
    root: Path,
    validation_ref: str,
    findings: list[DpaStableReadinessFinding],
) -> dict[str, str]:
    probes = {
        "PROBE-002": evaluate_probe_002_lifecycle_readiness(root, validation_ref=validation_ref),
        "RENDERER": evaluate_renderer_probe_readiness(root, validation_ref=validation_ref),
        "PROBE-003": evaluate_probe_003_workflow_readiness(root, validation_ref=validation_ref),
        "PROBE-004": evaluate_probe_004_migration_readiness(root, validation_ref=validation_ref),
    }
    statuses: dict[str, str] = {}
    for probe_id, result in probes.items():
        statuses[probe_id] = str(result.result_status)
        if not result.full_evidence_satisfied:
            _finding(
                findings,
                "probe-full-evidence-not-satisfied",
                f"{probe_id} full evidence must remain satisfied for stable promotion",
                result.readiness_record,
            )
    return statuses


def _load_promotion_record(
    path: Path,
    root: Path,
    findings: list[DpaStableReadinessFinding],
) -> dict[str, Any]:
    display_path = _display_path(path, root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _finding(findings, "promotion-record-invalid-json", f"record JSON is invalid: {exc}", display_path)
        return {}
    if not isinstance(data, dict):
        _finding(findings, "promotion-record-not-object", "record root must be a JSON object", display_path)
        return {}
    return data


def _load_stable_readiness_evidence(
    value: Any,
    root: Path,
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> None:
    candidate = str(value or "").strip()
    if not candidate:
        _finding(findings, "stable-readiness-evidence-missing", "stable readiness evidence path is missing", path)
        return
    evidence_path = root / candidate
    if not evidence_path.exists():
        _finding(findings, "stable-readiness-evidence-missing", f"missing evidence path: {candidate}", path)
        return
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _finding(findings, "stable-readiness-evidence-invalid-json", f"evidence JSON is invalid: {exc}", candidate)
        return
    if not isinstance(payload, dict):
        _finding(findings, "stable-readiness-evidence-invalid", "evidence JSON must be an object", candidate)
        return
    if payload.get("kind") != "dpa_stable_readiness_check":
        _finding(findings, "stable-readiness-evidence-kind-invalid", "evidence kind is invalid", candidate)
    if payload.get("result_status") != READY_FOR_STABLE_PROMOTION_STATUS:
        _finding(
            findings,
            "stable-readiness-evidence-status-invalid",
            f"evidence result_status must be {READY_FOR_STABLE_PROMOTION_STATUS}",
            candidate,
        )
    if payload.get("finding_count") != 0:
        _finding(findings, "stable-readiness-evidence-findings-present", "evidence must have zero findings", candidate)


def _promoted_spec_map(
    value: Any,
    path: str,
    findings: list[DpaStableReadinessFinding],
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        _finding(findings, "promoted-specs-missing", "stable_scope.promoted_specs must be a non-empty list", path)
        return {}
    promoted: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        entry = _mapping(item)
        spec_id = str(entry.get("id", "")).strip()
        if not spec_id:
            _finding(findings, "promoted-spec-id-missing", "promoted spec id is missing", f"{path}:promoted_specs[{index}]")
            continue
        if spec_id in promoted:
            _finding(findings, "promoted-spec-duplicate", f"promoted spec is duplicated: {spec_id}", path)
        promoted[spec_id] = entry
    return promoted


def _spec_status(root: Path, spec_id: str, path: str) -> DpaSpecStatus:
    candidate = root / path
    if not candidate.exists():
        return DpaSpecStatus(spec_id=spec_id, path=path, status="MISSING", present=False)
    for line in candidate.read_text(encoding="utf-8").splitlines()[:40]:
        if line.startswith("Status:"):
            return DpaSpecStatus(
                spec_id=spec_id,
                path=path,
                status=line.removeprefix("Status:").strip(),
                present=True,
            )
    return DpaSpecStatus(spec_id=spec_id, path=path, status="MISSING_STATUS", present=True)


def _require_existing_paths(
    value: Any,
    root: Path,
    findings: list[DpaStableReadinessFinding],
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
    findings: list[DpaStableReadinessFinding],
    code: str,
    message: str,
    path: str,
) -> None:
    findings.append(DpaStableReadinessFinding(code=code, message=message, path=path))


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
