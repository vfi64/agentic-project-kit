from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.workspace import load_workspace

DEFAULT_DP5_STAGE_RECORD_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/DP5_OBSERVE_STAGE_RECORD_20260801.json"
)
DP5_STAGE_MODEL = "dpa-dp5-stage-adoption-v1"
VALID_STATUS = "VALID_DP5_STAGE_RECORD"
ACCEPTED_OBSERVE_STATUS = "DP5_OBSERVE_STAGE_ADOPTED"
ACCEPTED_OBSERVE_TOKEN = "DPA_DP5_OBSERVE_STAGE_AUTHORIZED"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")
SUPPORTED_STAGE = "observe"
STRICTER_STAGES = ("warn", "block-new", "strict")

FALSE_CLAIM_FIELDS = (
    "warn_stage_active",
    "block_new_stage_active",
    "strict_stage_active",
    "kit_wide_dpa_conformance_claimed",
    "production_mutation_performed",
    "generated_outputs_manually_patched",
    "stable_dpa_claimed",
)


@dataclass(frozen=True)
class Dp5StageFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Dp5StageAdoptionResult:
    root: str
    record_path: str
    record_present: bool
    record_validation_ref: str
    current_validation_ref: str
    record_status: str
    decision_token: str
    active_stage: str
    findings: tuple[Dp5StageFinding, ...]

    @property
    def ok(self) -> bool:
        return self.result_status == VALID_STATUS

    @property
    def result_status(self) -> str:
        if not self.record_present:
            return "MISSING_DP5_STAGE_RECORD"
        if self.findings:
            return "INVALID_DP5_STAGE_RECORD"
        return VALID_STATUS

    def stage_accepted(self, stage: str) -> bool:
        return self.ok and self.active_stage == stage

    def as_dict(self) -> dict[str, Any]:
        claims = _false_claims()
        claims["observe_stage_active"] = self.stage_accepted("observe")
        return {
            "schema_version": 1,
            "kind": "dpa_dp5_stage_check",
            "stage_model": DP5_STAGE_MODEL,
            "result_status": self.result_status,
            "record_path": self.record_path,
            "record_present": self.record_present,
            "record_validation_ref": self.record_validation_ref,
            "current_validation_ref": self.current_validation_ref,
            "record_status": self.record_status,
            "decision_token": self.decision_token,
            "active_stage": self.active_stage,
            "stage_status": {
                "observe": "ADOPTED" if self.stage_accepted("observe") else "BLOCKED",
                "warn": "BLOCKED",
                "block-new": "BLOCKED",
                "strict": "BLOCKED",
            },
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "claims": claims,
        }


def evaluate_dp5_stage_record(
    root: Path | str = ".",
    *,
    record_path: Path | str = DEFAULT_DP5_STAGE_RECORD_PATH,
    validation_ref: str | None = None,
) -> Dp5StageAdoptionResult:
    base = Path(root).resolve()
    path = _resolve_under_root(base, record_path)
    display_path = _display_path(path, base)
    current_ref = validation_ref or _git_head(base)

    if not path.exists():
        return Dp5StageAdoptionResult(
            root=base.as_posix(),
            record_path=display_path,
            record_present=False,
            record_validation_ref="",
            current_validation_ref=current_ref,
            record_status="MISSING",
            decision_token="",
            active_stage="none",
            findings=(
                Dp5StageFinding(
                    code="dp5-stage-record-missing",
                    message="Record an exact DP5 stage authorization before adopting a lifecycle-gate stage.",
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

    findings: list[Dp5StageFinding] = []
    _validate_header(data, findings, display_path, root=base)
    _validate_stage_scope(data, findings, display_path, root=base)
    _validate_gate_set(data, findings, display_path, root=base)
    _validate_findings_mapping(data, findings, display_path)
    _validate_rollback(data, findings, display_path, root=base)
    _validate_claims(data, findings, display_path)

    return Dp5StageAdoptionResult(
        root=base.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref=str(data.get("validation_ref", "")),
        current_validation_ref=current_ref,
        record_status=str(data.get("status", "")),
        decision_token=str(data.get("decision_token", "")),
        active_stage=str(data.get("stage", "none")),
        findings=tuple(findings),
    )


def render_dp5_stage_check(result: Dp5StageAdoptionResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP5_STAGE_CHECK",
        f"STATUS={payload['result_status']}",
        f"RECORD={payload['record_path']}",
        f"RECORD_VALIDATION_REF={payload['record_validation_ref']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"RECORD_STATUS={payload['record_status']}",
        f"DECISION_TOKEN={payload['decision_token']}",
        f"ACTIVE_STAGE={payload['active_stage']}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for stage, status in payload["stage_status"].items():
        lines.append(f"DP5_STAGE={stage}|status={status}")
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dp5_stage_check_json(
    result: Dp5StageAdoptionResult,
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
) -> Dp5StageAdoptionResult:
    return Dp5StageAdoptionResult(
        root=root.as_posix(),
        record_path=display_path,
        record_present=True,
        record_validation_ref="",
        current_validation_ref=current_ref,
        record_status="INVALID",
        decision_token="",
        active_stage="none",
        findings=(
            Dp5StageFinding(
                code="dp5-stage-record-invalid-json",
                message=message,
                path=display_path,
            ),
        ),
    )


def _validate_header(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
    *,
    root: Path,
) -> None:
    if data.get("schema_version") != 1:
        _finding(findings, "schema-version-invalid", "schema_version must be 1", path)
    if data.get("kind") != "dpa_dp5_stage_record":
        _finding(findings, "kind-invalid", "kind must be dpa_dp5_stage_record", path)
    if data.get("stage") != SUPPORTED_STAGE:
        _finding(findings, "unsupported-stage", "this bounded slice only supports DP5 observe", path)
    if data.get("status") != ACCEPTED_OBSERVE_STATUS:
        _finding(findings, "status-not-adopted", f"status must be {ACCEPTED_OBSERVE_STATUS}", path)
    if data.get("decision_token") != ACCEPTED_OBSERVE_TOKEN:
        _finding(findings, "decision-token-invalid", f"decision_token must be {ACCEPTED_OBSERVE_TOKEN}", path)
    validation_ref = str(data.get("validation_ref", ""))
    if not validation_ref:
        _finding(findings, "validation-ref-missing", "validation_ref must record an exact ref", path)
    elif _git_ref_exists(root, validation_ref) is False:
        _finding(findings, "validation-ref-unresolvable", f"validation_ref is not a known commit: {validation_ref}", path)
    if not str(data.get("maintainer", "")).strip():
        _finding(findings, "maintainer-missing", "maintainer authorization text must be recorded", path)


def _validate_stage_scope(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
    *,
    root: Path,
) -> None:
    scope = _mapping(data.get("target_scope"))
    if scope.get("id") != "DPA_POST_DP2_DP3_DP4_ACCEPTED_SCOPE":
        _finding(findings, "target-scope-id-invalid", "target_scope.id must name the accepted DP3/DP4 scope", path)
    if scope.get("enforcement_stage") != "observe":
        _finding(findings, "target-scope-stage-invalid", "target_scope.enforcement_stage must be observe", path)
    _require_existing_paths(scope.get("evidence"), root, findings, path, "target-scope-evidence-missing")


def _validate_gate_set(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
    *,
    root: Path,
) -> None:
    gate_set = _mapping(data.get("gate_set"))
    if gate_set.get("id") != "DPA_DP5_OBSERVE_GATE_SET_V1":
        _finding(findings, "gate-set-id-invalid", "gate_set.id must be DPA_DP5_OBSERVE_GATE_SET_V1", path)
    if gate_set.get("stage_behavior") != "observe-only":
        _finding(findings, "gate-set-stage-behavior-invalid", "gate_set.stage_behavior must be observe-only", path)
    if gate_set.get("blocks_unrelated_work") is not False:
        _finding(findings, "gate-set-overblocks", "observe gate set must not block unrelated work", path)
    commands = _list_of_mappings(gate_set.get("commands"))
    if not commands:
        _finding(findings, "gate-set-commands-missing", "gate_set.commands must not be empty", path)
    for index, command in enumerate(commands):
        if not str(command.get("command", "")).strip():
            _finding(findings, "gate-set-command-missing", f"gate_set.commands[{index}] needs command", path)
        _require_existing_paths(command.get("evidence"), root, findings, path, "gate-set-command-evidence-missing")


def _validate_findings_mapping(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
) -> None:
    mapping = _mapping(data.get("findings_mapping"))
    required = _mapping(mapping.get("unknown_mutation_safety_finding"))
    if required.get("disposition") != "fail_closed_for_mutation_safety":
        _finding(
            findings,
            "unknown-mutation-safety-disposition-invalid",
            "unknown mutation-safety findings must fail closed",
            path,
        )
    if mapping.get("stage_decision") != "record_only_no_new_blocking":
        _finding(findings, "stage-decision-invalid", "observe mapping must record only and add no new blocking", path)


def _validate_rollback(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
    *,
    root: Path,
) -> None:
    rollback = _mapping(data.get("rollback"))
    if rollback.get("less_strict_stage") != "pre-dp5":
        _finding(findings, "rollback-stage-invalid", "rollback.less_strict_stage must be pre-dp5", path)
    if rollback.get("tested_or_adjudicated") is not True:
        _finding(findings, "rollback-not-proven", "rollback must be tested or explicitly adjudicated", path)
    _require_existing_paths(rollback.get("evidence"), root, findings, path, "rollback-evidence-missing")


def _validate_claims(
    data: dict[str, Any],
    findings: list[Dp5StageFinding],
    path: str,
) -> None:
    claims = _mapping(data.get("claims"))
    if claims.get("observe_stage_active") is not True:
        _finding(findings, "observe-claim-missing", "claims.observe_stage_active must be true", path)
    for field in FALSE_CLAIM_FIELDS:
        if claims.get(field) is not False:
            _finding(findings, "false-claim-invalid", f"claims.{field} must be false", path)


def _require_existing_paths(
    value: Any,
    root: Path,
    findings: list[Dp5StageFinding],
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


def _finding(findings: list[Dp5StageFinding], code: str, message: str, path: str) -> None:
    findings.append(Dp5StageFinding(code=code, message=message, path=path))


def _false_claims() -> dict[str, bool]:
    return {
        "observe_stage_active": False,
        "warn_stage_active": False,
        "block_new_stage_active": False,
        "strict_stage_active": False,
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
