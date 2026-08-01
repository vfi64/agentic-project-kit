from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.dpa_dp3_dp4_adjudication import (
    DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
    evaluate_dp3_dp4_adjudication_record,
    render_dp3_dp4_adjudication_check,
    write_dp3_dp4_adjudication_check_json,
)
from agentic_project_kit.dpa_dp5_block_new_gate import (
    DEFAULT_DP5_BLOCK_NEW_BASELINE_PATH,
    DEFAULT_DP5_BLOCK_NEW_STAGE_RECORD_PATH,
    evaluate_dp5_block_new_gate,
    render_dp5_block_new_gate,
    write_dp5_block_new_gate_json,
)
from agentic_project_kit.dpa_dp5_strict_gate import (
    evaluate_dp5_strict_gate,
    render_dp5_strict_gate,
    write_dp5_strict_gate_json,
)
from agentic_project_kit.dpa_final_closeout import (
    DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH,
    evaluate_dpa_final_closeout_record,
    render_dpa_final_closeout_check,
    write_dpa_final_closeout_check_json,
)
from agentic_project_kit.dpa_dp5_stage_adoption import (
    DEFAULT_DP5_STAGE_RECORD_PATH,
    evaluate_dp5_stage_record,
    render_dp5_stage_check,
    write_dp5_stage_check_json,
)
from agentic_project_kit.dpa_dp2_decision_readiness import (
    evaluate_dp2_decision_readiness,
    render_dp2_decision_readiness,
    write_dp2_decision_readiness_json,
)
from agentic_project_kit.dpa_fixture_evidence import (
    AUTHORIZATION_TOKEN,
    evaluate_dpa_fixture_evidence,
    render_dpa_fixture_evidence,
    write_dpa_fixture_evidence_json,
)
from agentic_project_kit.dpa_maintainer_record_check import (
    DEFAULT_MAINTAINER_RECORD_PATH,
    evaluate_dp2_maintainer_record,
    render_dp2_maintainer_record_check,
    write_dp2_maintainer_record_check_json,
)
from agentic_project_kit.dpa_current_handoff_lifecycle import (
    DEFAULT_ACCEPTANCE_STATE_PATH,
    evaluate_current_handoff_lifecycle,
    render_current_handoff_lifecycle_result,
)
from agentic_project_kit.dpa_probe_002_readiness import (
    evaluate_probe_002_lifecycle_readiness,
    render_probe_002_lifecycle_readiness,
    write_probe_002_readiness_json,
)
from agentic_project_kit.dpa_probe_003_readiness import (
    evaluate_probe_003_workflow_readiness,
    render_probe_003_workflow_readiness,
    write_probe_003_readiness_json,
)
from agentic_project_kit.dpa_probe_004_readiness import (
    evaluate_probe_004_migration_readiness,
    render_probe_004_migration_readiness,
    write_probe_004_readiness_json,
)
from agentic_project_kit.dpa_post_dp2_scope_assessment import (
    evaluate_post_dp2_scope_assessment,
    render_post_dp2_scope_assessment,
    write_post_dp2_scope_assessment_json,
)
from agentic_project_kit.dpa_readiness import (
    DEFAULT_READINESS_PATH,
    evaluate_dpa_readiness,
    render_dpa_readiness_result,
)
from agentic_project_kit.dpa_readonly_probe_execution import (
    DEFAULT_FIXTURE_MANIFEST_PATH,
    evaluate_dpa_readonly_probe_execution,
    render_dpa_readonly_probe_execution,
    write_dpa_readonly_probe_execution_json,
)
from agentic_project_kit.dpa_renderer_readiness import (
    evaluate_renderer_probe_readiness,
    render_renderer_probe_readiness,
    write_renderer_readiness_json,
)
from agentic_project_kit.dpa_wrt_ch001_evidence import (
    evaluate_wrt_ch001_admin_refresh_observation,
    fetch_admin_refresh_pr_data,
    load_pr_data,
    render_wrt_ch001_evidence,
    write_wrt_ch001_evidence_json,
)

dpa_app = typer.Typer(help="Inspect Document Projection Architecture readiness state.")


@dpa_app.command("readiness")
def dpa_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_dp2_ready: bool = typer.Option(
        False,
        "--require-dp2-ready",
        help="Fail unless the readiness record structurally authorizes DP2.",
    ),
) -> None:
    """Validate the DPA DP1 Assessment readiness record without mutating files."""
    result = evaluate_dpa_readiness(root, readiness_path=record)
    if output_json:
        typer.echo(json.dumps(result.as_dict(), indent=2))
    else:
        typer.echo(render_dpa_readiness_result(result), nl=False)
    if result.findings or (require_dp2_ready and not result.dp2_ready):
        raise typer.Exit(1)


@dpa_app.command("post-dp2-scope-assessment")
def dpa_post_dp2_scope_assessment_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    adjudication_record: Path = typer.Option(
        DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
        "--adjudication-record",
        help="Optional DP3/DP4 adjudication record to inspect when clearing post-DP2 blockers.",
    ),
    dp5_stage_record: Path = typer.Option(
        DEFAULT_DP5_STAGE_RECORD_PATH,
        "--dp5-stage-record",
        help="Optional DP5 stage-adoption record to inspect when clearing stage blockers.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_closeout_ready: bool = typer.Option(
        False,
        "--require-closeout-ready",
        help="Fail unless DP3, DP4, DP5 and final closeout are structurally ready.",
    ),
) -> None:
    """Assess post-DP2 DP3-DP5 rollout, migration and strict-gate scope."""
    resolved_root = root.resolve()
    result = evaluate_post_dp2_scope_assessment(
        resolved_root,
        readiness_path=record,
        adjudication_record_path=adjudication_record,
        dp5_stage_record_path=dp5_stage_record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_post_dp2_scope_assessment_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_post_dp2_scope_assessment(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_closeout_ready and not result.final_closeout_ready:
        raise typer.Exit(1)


@dpa_app.command("dp3-dp4-adjudication-check")
def dpa_dp3_dp4_adjudication_check_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
        "--record",
        help="DPA DP3/DP4 bounded adjudication record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact current ref to record instead of repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_valid: bool = typer.Option(
        False,
        "--require-valid",
        help="Fail unless the record structurally accepts the bounded DP3/DP4 slice.",
    ),
) -> None:
    """Validate a bounded DP3/DP4 adjudication record without authorizing DP5."""
    resolved_root = root.resolve()
    result = evaluate_dp3_dp4_adjudication_record(
        resolved_root,
        record_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp3_dp4_adjudication_check_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp3_dp4_adjudication_check(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_valid and not result.ok:
        raise typer.Exit(1)


@dpa_app.command("dp5-stage-check")
def dpa_dp5_stage_check_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_DP5_STAGE_RECORD_PATH,
        "--record",
        help="DPA DP5 stage-adoption record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact current ref to record instead of repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_valid: bool = typer.Option(
        False,
        "--require-valid",
        help="Fail unless the DP5 stage record is structurally valid.",
    ),
) -> None:
    """Validate a bounded DP5 lifecycle stage record."""
    resolved_root = root.resolve()
    result = evaluate_dp5_stage_record(
        resolved_root,
        record_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp5_stage_check_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp5_stage_check(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_valid and not result.ok:
        raise typer.Exit(1)


@dpa_app.command("dp5-block-new-gate")
def dpa_dp5_block_new_gate_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    baseline: Path = typer.Option(
        DEFAULT_DP5_BLOCK_NEW_BASELINE_PATH,
        "--baseline",
        help="Accepted DP5 warn-stage baseline assessment to compare against.",
    ),
    dp5_stage_record: Path = typer.Option(
        DEFAULT_DP5_BLOCK_NEW_STAGE_RECORD_PATH,
        "--dp5-stage-record",
        help="DP5 block-new stage-adoption record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact current ref to record instead of repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_pass: bool = typer.Option(
        False,
        "--require-pass",
        help="Fail unless no new DP5 noncompliance is present against the accepted warn baseline.",
    ),
) -> None:
    """Block new DP5 noncompliance against the accepted warn-stage baseline."""
    resolved_root = root.resolve()
    result = evaluate_dp5_block_new_gate(
        resolved_root,
        baseline_path=baseline,
        dp5_stage_record_path=dp5_stage_record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp5_block_new_gate_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp5_block_new_gate(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_pass and not result.ok:
        raise typer.Exit(1)


@dpa_app.command("dp5-strict-gate")
def dpa_dp5_strict_gate_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    dp5_stage_record: Path = typer.Option(
        DEFAULT_DP5_STAGE_RECORD_PATH,
        "--dp5-stage-record",
        help="DP5 strict stage-adoption record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact current ref to record instead of repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_pass: bool = typer.Option(
        False,
        "--require-pass",
        help="Fail unless strict has zero configured noncompliance in the accepted DPA scope.",
    ),
) -> None:
    """Block all configured DP5 noncompliance in the accepted DPA scope."""
    resolved_root = root.resolve()
    result = evaluate_dp5_strict_gate(
        resolved_root,
        dp5_stage_record_path=dp5_stage_record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp5_strict_gate_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp5_strict_gate(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_pass and not result.ok:
        raise typer.Exit(1)


@dpa_app.command("final-closeout-check")
def dpa_final_closeout_check_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_DPA_FINAL_CLOSEOUT_RECORD_PATH,
        "--record",
        help="DPA final closeout record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact current ref to record instead of repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_valid: bool = typer.Option(
        False,
        "--require-valid",
        help="Fail unless the final closeout record is structurally valid.",
    ),
) -> None:
    """Validate the bounded DP1-DP5 final closeout record."""
    resolved_root = root.resolve()
    result = evaluate_dpa_final_closeout_record(
        resolved_root,
        record_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dpa_final_closeout_check_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dpa_final_closeout_check(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_valid and not result.ok:
        raise typer.Exit(1)


@dpa_app.command("current-handoff-refresh")
def dpa_current_handoff_refresh_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    target: Path | None = typer.Option(
        None,
        "--target",
        help="Optional registered CURRENT_HANDOFF target override; defaults to the workspace handoff resolver.",
    ),
    acceptance_state: Path | None = typer.Option(
        None,
        "--acceptance-state",
        help=f"Optional DPA acceptance-state record override; legacy default is {DEFAULT_ACCEPTANCE_STATE_PATH.as_posix()}.",
    ),
    readiness_record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--readiness-record",
        help="DPA Assessment readiness record that must authorize DP2.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact repository ref; when supplied it must match current HEAD.",
    ),
    initialize_acceptance: bool = typer.Option(
        False,
        "--initialize-acceptance",
        help="Allow first acceptance-state creation when no prior DPA state exists.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write target bytes and acceptance state."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Refresh CURRENT_HANDOFF through DPA freshness, locking and acceptance-state gates."""
    resolved_root = root.resolve()
    result = evaluate_current_handoff_lifecycle(
        resolved_root,
        target_path=target,
        acceptance_state_path=acceptance_state,
        readiness_path=readiness_record,
        validation_ref=validation_ref,
        execute=execute,
        initialize_acceptance=initialize_acceptance,
    )
    if output_json:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_current_handoff_lifecycle_result(result), nl=False)
    if not result.ok:
        raise typer.Exit(2)


@dpa_app.command("readonly-probe-execution")
def dpa_readonly_probe_execution_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    fixture_manifest: Path = typer.Option(
        DEFAULT_FIXTURE_MANIFEST_PATH,
        "--fixture-manifest",
        help="DPA DP1 Probe fixture manifest to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    plan_only: bool = typer.Option(
        False,
        "--plan-only",
        help="Classify eligible read-only fixture cases without executing commands.",
    ),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    timeout_seconds: int = typer.Option(180, "--timeout-seconds", min=1, help="Per-command timeout."),
    require_no_command_failures: bool = typer.Option(
        False,
        "--require-no-command-failures",
        help="Fail unless every executed read-only command succeeds.",
    ),
) -> None:
    """Execute only non-mutating DP1 Probe fixture cases."""
    resolved_root = root.resolve()
    result = evaluate_dpa_readonly_probe_execution(
        resolved_root,
        fixture_manifest_path=fixture_manifest,
        validation_ref=validation_ref,
        plan_only=plan_only,
        timeout_seconds=timeout_seconds,
    )
    write_result = None
    if output is not None:
        write_result = write_dpa_readonly_probe_execution_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dpa_readonly_probe_execution(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings or result.command_failures:
        raise typer.Exit(2)
    if require_no_command_failures and result.command_failures:
        raise typer.Exit(1)


@dpa_app.command("fixture-evidence")
def dpa_fixture_evidence_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    fixture_manifest: Path = typer.Option(
        DEFAULT_FIXTURE_MANIFEST_PATH,
        "--fixture-manifest",
        help="DPA DP1 Probe fixture manifest to execute.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    authorized_by: str | None = typer.Option(
        None,
        "--authorized-by",
        help="Maintainer/operator authorization identity for non-production fixture execution.",
    ),
    authorization_token: str | None = typer.Option(
        None,
        "--authorization-token",
        help=f"Required token for non-production fixture execution: {AUTHORIZATION_TOKEN}.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    plan_only: bool = typer.Option(
        False,
        "--plan-only",
        help="Classify fixture cases without executing temporary/disposable fixture actions.",
    ),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_full_evidence: bool = typer.Option(
        False,
        "--require-full-evidence",
        help="Fail unless every fixture case executes and all full-evidence families are satisfied.",
    ),
) -> None:
    """Execute authorized non-production DPA fixture evidence cases."""
    resolved_root = root.resolve()
    result = evaluate_dpa_fixture_evidence(
        resolved_root,
        fixture_manifest_path=fixture_manifest,
        validation_ref=validation_ref,
        authorized_by=authorized_by,
        authorization_token=authorization_token,
        plan_only=plan_only,
    )
    write_result = None
    if output is not None:
        write_result = write_dpa_fixture_evidence_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dpa_fixture_evidence(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings or not result.authorization_ok or result.failed_cases:
        raise typer.Exit(2)
    if require_full_evidence and (
        result.result_status != "FULL_FIXTURE_EVIDENCE_RECORDED"
        or not all(result.full_evidence_by_family.values())
        or not result.rollback_cleanup_proven
    ):
        raise typer.Exit(1)


@dpa_app.command("dp2-decision-readiness")
def dpa_dp2_decision_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_ready: bool = typer.Option(
        False,
        "--require-ready",
        help="Fail unless the decision package is structurally ready for Maintainer review.",
    ),
) -> None:
    """Prepare DP2 decision readiness without recording Maintainer authorization."""
    resolved_root = root.resolve()
    result = evaluate_dp2_decision_readiness(
        resolved_root,
        readiness_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp2_decision_readiness_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp2_decision_readiness(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_ready and result.result_status != "READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED":
        raise typer.Exit(1)


@dpa_app.command("maintainer-record-check")
def dpa_maintainer_record_check_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_MAINTAINER_RECORD_PATH,
        "--record",
        help="DPA DP2 Maintainer Assessment record to inspect.",
    ),
    readiness_record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--readiness-record",
        help="DPA Assessment readiness JSON record that the Maintainer record must bind to.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA Assessment evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_authorization: bool = typer.Option(
        False,
        "--require-authorization",
        help="Fail unless the record is a valid DP2 authorization record.",
    ),
) -> None:
    """Validate a DP2 Maintainer Assessment record without authorizing DP2."""
    resolved_root = root.resolve()
    result = evaluate_dp2_maintainer_record(
        resolved_root,
        record_path=record,
        readiness_path=readiness_record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_dp2_maintainer_record_check_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_dp2_maintainer_record_check(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_authorization and result.result_status != "VALID_AUTHORIZATION_RECORD":
        raise typer.Exit(1)


@dpa_app.command("probe-002-readiness")
def dpa_probe_002_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_full_evidence: bool = typer.Option(
        False,
        "--require-full-evidence",
        help="Fail unless PROBE-002 full evidence is structurally satisfied.",
    ),
) -> None:
    """Inspect PROBE-002 lifecycle and selected-writer readiness without production mutation."""
    resolved_root = root.resolve()
    result = evaluate_probe_002_lifecycle_readiness(resolved_root, readiness_path=record)
    write_result = None
    if output is not None:
        write_result = write_probe_002_readiness_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_probe_002_lifecycle_readiness(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_full_evidence and not result.full_evidence_satisfied:
        raise typer.Exit(1)


@dpa_app.command("wrt-ch001-evidence")
def dpa_wrt_ch001_evidence_command(
    source_pr: int = typer.Option(..., "--source-pr", help="Substantive PR that triggered the admin refresh."),
    admin_pr: int = typer.Option(..., "--admin-pr", help="Administrative handoff refresh PR to observe."),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    input_path: Path | None = typer.Option(
        None,
        "--input",
        help="Optional gh-pr-view JSON input. If omitted, gh pr view is used.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_disposable_fixture: bool = typer.Option(
        False,
        "--require-disposable-fixture",
        help="Fail unless this evidence satisfies disposable WRT-CH-001 fixture execution.",
    ),
) -> None:
    """Observe a WRT-CH-001 admin refresh PR without claiming disposable fixture PASS."""
    resolved_root = root.resolve()
    pr_data = load_pr_data(input_path) if input_path is not None else fetch_admin_refresh_pr_data(admin_pr, root=resolved_root)
    result = evaluate_wrt_ch001_admin_refresh_observation(
        resolved_root,
        source_pr=source_pr,
        admin_pr=admin_pr,
        pr_data=pr_data,
    )
    write_result = None
    if output is not None:
        write_result = write_wrt_ch001_evidence_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_wrt_ch001_evidence(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_disposable_fixture and not result.full_wrt_ch001_fixture_satisfied:
        raise typer.Exit(1)


@dpa_app.command("probe-003-readiness")
def dpa_probe_003_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_full_evidence: bool = typer.Option(
        False,
        "--require-full-evidence",
        help="Fail unless PROBE-003 full evidence is structurally satisfied.",
    ),
) -> None:
    """Inspect PROBE-003 workflow serialization readiness without workflow mutation."""
    resolved_root = root.resolve()
    result = evaluate_probe_003_workflow_readiness(
        resolved_root,
        readiness_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_probe_003_readiness_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_probe_003_workflow_readiness(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_full_evidence and not result.full_evidence_satisfied:
        raise typer.Exit(1)


@dpa_app.command("renderer-readiness")
def dpa_renderer_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_full_evidence: bool = typer.Option(
        False,
        "--require-full-evidence",
        help="Fail unless Renderer Probe full evidence is structurally satisfied.",
    ),
) -> None:
    """Inspect Renderer Probe readiness without renderer conformance claims."""
    resolved_root = root.resolve()
    result = evaluate_renderer_probe_readiness(
        resolved_root,
        readiness_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_renderer_readiness_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_renderer_probe_readiness(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_full_evidence and not result.full_evidence_satisfied:
        raise typer.Exit(1)


@dpa_app.command("probe-004-readiness")
def dpa_probe_004_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    validation_ref: str | None = typer.Option(
        None,
        "--validation-ref",
        help="Optional exact target ref to record instead of the current repository HEAD.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional DPA probe evidence JSON path under docs/architecture/evidence/dpa/probes/.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Write --output when supplied."),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_full_evidence: bool = typer.Option(
        False,
        "--require-full-evidence",
        help="Fail unless PROBE-004 full evidence is structurally satisfied.",
    ),
) -> None:
    """Inspect PROBE-004 migration and rollback readiness without migration."""
    resolved_root = root.resolve()
    result = evaluate_probe_004_migration_readiness(
        resolved_root,
        readiness_path=record,
        validation_ref=validation_ref,
    )
    write_result = None
    if output is not None:
        write_result = write_probe_004_readiness_json(
            result,
            resolved_root,
            output,
            execute=execute,
        )
    payload = result.as_dict()
    if write_result is not None:
        payload["evidence_write"] = write_result
    if output_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_probe_004_migration_readiness(result), nl=False)
        if write_result is not None:
            reason = f"|reason={write_result['reason']}" if "reason" in write_result else ""
            typer.echo(
                "EVIDENCE_WRITE="
                f"{write_result['result_status']}|"
                f"path={write_result['output_path']}|"
                f"written={str(write_result.get('written', False)).lower()}"
                f"{reason}"
            )
    if write_result is not None and write_result["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if result.findings:
        raise typer.Exit(2)
    if require_full_evidence and not result.full_evidence_satisfied:
        raise typer.Exit(1)
