from __future__ import annotations

import json
from pathlib import Path

import typer

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
from agentic_project_kit.dpa_readiness import (
    DEFAULT_READINESS_PATH,
    evaluate_dpa_readiness,
    render_dpa_readiness_result,
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
