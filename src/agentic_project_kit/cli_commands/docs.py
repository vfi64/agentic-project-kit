from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.doc_lifecycle import (
    build_doc_lifecycle_apply_payload,
    build_doc_lifecycle_evidence_report_payload,
    build_doc_lifecycle_plan_payload,
    build_doc_lifecycle_triage_payload,
    render_doc_lifecycle_apply_report,
    render_doc_lifecycle_evidence_report_result,
    render_doc_lifecycle_plan_report,
    render_doc_lifecycle_triage_report,
)
from agentic_project_kit.doc_lifecycle_sweep import (
    build_doc_lifecycle_bootstrap_payload,
    build_doc_lifecycle_propose_delete_payload,
    build_doc_lifecycle_sweep_payload,
    json_dumps,
    render_doc_lifecycle_bootstrap,
    render_doc_lifecycle_propose_delete,
    render_doc_lifecycle_sweep,
)
from agentic_project_kit.removed_source_audit import (
    DEFAULT_CENTRAL_TARGET,
    build_removed_source_audit,
    render_removed_source_audit,
)

docs_app = typer.Typer(help="Documentation maintenance and migration guards.")
lifecycle_app = typer.Typer(help="Safe documentation lifecycle triage and planning.")
docs_app.add_typer(lifecycle_app, name="lifecycle")


@lifecycle_app.command("bootstrap")
def docs_lifecycle_bootstrap_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--execute", help="Preview or stamp missing lifecycle headers."),
    ] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Stamp missing lifecycle headers without claiming semantic currency."""
    payload = build_doc_lifecycle_bootstrap_payload(
        root.resolve(),
        execute=not dry_run,
    )
    if json_output:
        typer.echo(json_dumps(payload))
    else:
        typer.echo(render_doc_lifecycle_bootstrap(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)


@lifecycle_app.command("propose-delete")
def docs_lifecycle_propose_delete_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List archive documents that may be old enough for manual deletion review."""
    payload = build_doc_lifecycle_propose_delete_payload(root.resolve())
    if json_output:
        typer.echo(json_dumps(payload))
    else:
        typer.echo(render_doc_lifecycle_propose_delete(payload), nl=False)


@lifecycle_app.command("sweep")
def docs_lifecycle_sweep_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--execute", help="Preview or apply selected lifecycle hygiene actions."),
    ] = True,
    only: Annotated[
        str,
        typer.Option("--only", help="Comma-separated finding id(s) to execute. Required with --execute."),
    ] = "",
    until: Annotated[
        str | None,
        typer.Option("--until", help="YYYY-MM-DD deferral date for selected defer actions."),
    ] = None,
    review_after: Annotated[
        str | None,
        typer.Option("--review-after", help="Optional registry review_after value for confirm-current actions."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build or apply a bounded documentation lifecycle sweep plan."""
    payload = build_doc_lifecycle_sweep_payload(
        root.resolve(),
        execute=not dry_run,
        only=only,
        until=until,
        review_after=review_after,
    )
    if json_output:
        typer.echo(json_dumps(payload))
    else:
        typer.echo(render_doc_lifecycle_sweep(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)




@lifecycle_app.command("apply")
def docs_lifecycle_apply_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    scope: Annotated[str, typer.Option("--scope", help="Repository-relative documentation scope.")] = "docs",
    only: Annotated[str, typer.Option("--only", help="Plan step id to apply.")] = "",
    execute: Annotated[bool, typer.Option("--execute", help="Required explicit execution flag.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Apply one safe documentation lifecycle plan step."""
    payload = build_doc_lifecycle_apply_payload(
        root.resolve(),
        scope,
        only,
        execute=execute,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_lifecycle_apply_report(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)



@lifecycle_app.command("report")
def docs_lifecycle_report_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    scope: Annotated[str, typer.Option("--scope", help="Repository-relative documentation scope.")] = "docs",
    output: Annotated[Path, typer.Option("--output", help="Evidence JSON output path.")] = Path(
        "docs/architecture/evidence/doc-lifecycle-report.json"
    ),
    execute: Annotated[bool, typer.Option("--execute", help="Write the evidence report.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build or write one documentation lifecycle evidence report."""
    payload = build_doc_lifecycle_evidence_report_payload(
        root.resolve(),
        scope,
        output,
        execute=execute,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_lifecycle_evidence_report_result(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)


@lifecycle_app.command("plan")
def docs_lifecycle_plan_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    scope: Annotated[str, typer.Option("--scope", help="Repository-relative documentation scope.")] = "docs",
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build a dry-run lifecycle plan for one documentation scope."""
    payload = build_doc_lifecycle_plan_payload(root.resolve(), scope)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_lifecycle_plan_report(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)


@lifecycle_app.command("triage")
def docs_lifecycle_triage_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Propose safe documentation lifecycle actions without applying changes."""
    payload = build_doc_lifecycle_triage_payload(root.resolve())
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_lifecycle_triage_report(payload), nl=False)
    if payload["result_status"] == "BLOCK":
        raise typer.Exit(code=2)


@docs_app.command("removed-source-audit")
def removed_source_audit_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    path: Annotated[
        list[str] | None,
        typer.Option(
            "--path",
            help=(
                "Repository-relative removed source path to audit. "
                "May be supplied multiple times. Defaults to removed_source paths in PROJECT_DIRECTION.yaml."
            ),
        ),
    ] = None,
    central_target: Annotated[
        str,
        typer.Option("--central-target", help="Repository-relative central document that may retain removed_source metadata."),
    ] = DEFAULT_CENTRAL_TARGET,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Fail if removed documentation sources still have live refs or registry refs."""
    result = build_removed_source_audit(
        root.resolve(),
        paths=path,
        central_target=central_target,
    )
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_removed_source_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
