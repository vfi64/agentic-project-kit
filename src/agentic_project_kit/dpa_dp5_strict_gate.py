from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agentic_project_kit.dpa_dp5_stage_adoption import DEFAULT_DP5_STAGE_RECORD_PATH
from agentic_project_kit.dpa_post_dp2_scope_assessment import evaluate_post_dp2_scope_assessment
from agentic_project_kit.workspace import load_workspace

EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")
PASS_STATUS = "PASS"
BLOCK_STATUS = "BLOCK"


@dataclass(frozen=True)
class Dp5StrictFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Dp5StrictGateResult:
    root: str
    current_validation_ref: str
    current_kit_wide_status: str
    active_stage: str
    blocker_count: int
    warning_count: int
    final_closeout_ready: bool
    findings: tuple[Dp5StrictFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings and self.final_closeout_ready and self.blocker_count == 0

    @property
    def result_status(self) -> str:
        return PASS_STATUS if self.ok else BLOCK_STATUS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_dp5_strict_gate",
            "result_status": self.result_status,
            "current_validation_ref": self.current_validation_ref,
            "current_kit_wide_status": self.current_kit_wide_status,
            "active_stage": self.active_stage,
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "final_closeout_ready": self.final_closeout_ready,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "claims": {
                "strict_stage_active": self.ok,
                "kit_wide_dpa_conformance_claimed": False,
                "production_mutation_performed": False,
                "generated_outputs_manually_patched": False,
                "stable_dpa_claimed": False,
            },
        }


def evaluate_dp5_strict_gate(
    root: Path | str = ".",
    *,
    dp5_stage_record_path: Path | str = DEFAULT_DP5_STAGE_RECORD_PATH,
    validation_ref: str | None = None,
) -> Dp5StrictGateResult:
    base = Path(root).resolve()
    assessment = evaluate_post_dp2_scope_assessment(
        base,
        dp5_stage_record_path=dp5_stage_record_path,
        validation_ref=validation_ref,
    )
    payload = assessment.as_dict()
    findings = [
        Dp5StrictFinding(
            code=f"post-dp2-{finding.code}",
            message=finding.message,
            path=finding.path,
        )
        for finding in assessment.findings
    ]
    if not assessment.dp5_stage_record.stage_accepted("strict"):
        findings.append(
            Dp5StrictFinding(
                code="strict-stage-not-active",
                message="DP5 strict gate requires an accepted strict stage record.",
                path=assessment.dp5_stage_record.record_path,
            )
        )
    if payload["kit_wide_dpa_conformance_claimed"] is not False:
        findings.append(
            Dp5StrictFinding(
                code="conformance-claim-present",
                message="Strict gate must not create the final Kit-wide conformance claim.",
                path=assessment.readiness_record,
            )
        )
    if payload["blocker_count"] != 0:
        findings.append(
            Dp5StrictFinding(
                code="configured-noncompliance-present",
                message="Strict gate blocks all configured noncompliance in the accepted scope.",
                path=assessment.dp5_stage_record.record_path,
            )
        )

    return Dp5StrictGateResult(
        root=base.as_posix(),
        current_validation_ref=str(payload["validation_ref"]),
        current_kit_wide_status=str(payload["kit_wide_dpa_status"]),
        active_stage=assessment.dp5_stage_record.active_stage,
        blocker_count=int(payload["blocker_count"]),
        warning_count=int(payload["dp5"]["warning_count"]),
        final_closeout_ready=bool(payload["final_closeout_ready"]),
        findings=tuple(findings),
    )


def render_dp5_strict_gate(result: Dp5StrictGateResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP5_STRICT_GATE",
        f"STATUS={payload['result_status']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"CURRENT_KIT_WIDE_DPA_STATUS={payload['current_kit_wide_status']}",
        f"ACTIVE_STAGE={payload['active_stage']}",
        f"BLOCKERS={payload['blocker_count']}",
        f"WARNINGS={payload['warning_count']}",
        f"FINAL_CLOSEOUT_READY={str(payload['final_closeout_ready']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dp5_strict_gate_json(
    result: Dp5StrictGateResult,
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


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()
