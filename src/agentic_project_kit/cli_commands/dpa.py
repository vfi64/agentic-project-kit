from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.dpa_probe_002_readiness import (
    evaluate_probe_002_lifecycle_readiness,
    render_probe_002_lifecycle_readiness,
    write_probe_002_readiness_json,
)
from agentic_project_kit.dpa_readiness import (
    DEFAULT_READINESS_PATH,
    evaluate_dpa_readiness,
    render_dpa_readiness_result,
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
