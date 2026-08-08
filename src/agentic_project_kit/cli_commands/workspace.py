from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.workspace_init import (
    WorkspaceInitError,
    build_workspace_init_plan,
    execute_workspace_init,
    render_workspace_init_error,
    render_workspace_init_plan,
)
from agentic_project_kit.workspace_remove import (
    WorkspaceRemoveError,
    build_workspace_remove_plan,
    execute_workspace_remove,
    render_workspace_remove_error,
    render_workspace_remove_plan,
)
from agentic_project_kit.workspace_upgrade import (
    WorkspaceUpgradeError,
    build_workspace_upgrade_plan,
    execute_workspace_upgrade,
    render_workspace_upgrade_error,
    render_workspace_upgrade_plan,
)
from agentic_project_kit.workspace_adopt import (
    analyze_workspace_adoption,
    render_workspace_adopt_report,
)
from agentic_project_kit.workspace_dpa_intake import (
    build_workspace_dpa_intake_report,
    render_workspace_dpa_intake_report,
)

workspace_app = typer.Typer(help="Inspect and manage operating-layer workspaces.")


@workspace_app.command("adopt")
def workspace_adopt_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Analyze an existing repository without writing workspace files."""

    report = analyze_workspace_adoption(root.resolve())
    if json_output:
        typer.echo(json.dumps(report.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(render_workspace_adopt_report(report), nl=False)


@workspace_app.command("dpa-intake")
def workspace_dpa_intake_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    validation_ref: Annotated[
        str | None,
        typer.Option(
            "--validation-ref",
            help="Optional exact current ref to record instead of repository HEAD.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Optional DPA intake evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
        ),
    ] = None,
    write_evidence: Annotated[
        bool,
        typer.Option(
            "--write-evidence",
            help="Use the default bounded DPA intake evidence JSON path.",
        ),
    ] = False,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Write requested evidence output."),
    ] = False,
    require_ready: Annotated[
        bool,
        typer.Option(
            "--require-ready",
            help="Fail unless the target repo is ready for DPA intake adjudication.",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the deterministic DPA repository-intake orchestration."""

    report = build_workspace_dpa_intake_report(
        root.resolve(),
        validation_ref=validation_ref,
        output=output,
        write_evidence=write_evidence,
        execute=execute,
    )
    if json_output:
        typer.echo(json.dumps(report.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(render_workspace_dpa_intake_report(report), nl=False)
    if report.evidence_write is not None and report.evidence_write["result_status"] == "BLOCK":
        raise typer.Exit(2)
    if require_ready and not report.ok:
        raise typer.Exit(1)


@workspace_app.command("init")
def workspace_init_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    name: Annotated[str | None, typer.Option("--name", help="Project name override.")] = None,
    project_type: Annotated[str | None, typer.Option("--type", help="Project type override: python, node, or generic.")] = None,
    profile: Annotated[str | None, typer.Option("--profile", help="Workspace profile override.")] = None,
    execute: Annotated[bool, typer.Option("--execute", help="Write the planned workspace files.")] = False,
    inject_ci: Annotated[bool, typer.Option("--inject-ci", help="Opt in to GitHub Actions workflow injection.")] = False,
    inject_pre_commit: Annotated[bool, typer.Option("--inject-pre-commit", help="Opt in to pre-commit snippet injection.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or create a bounded operating-layer workspace."""

    try:
        plan = build_workspace_init_plan(
            root.resolve(),
            name=name,
            project_type=project_type,
            profile=profile,
            execute=execute,
            inject_ci=inject_ci,
            inject_pre_commit=inject_pre_commit,
        )
        if execute:
            execute_workspace_init(plan)
        if json_output:
            typer.echo(json.dumps(plan.as_json_data(written=execute), indent=2, sort_keys=True))
        else:
            typer.echo(render_workspace_init_plan(plan, written=execute), nl=False)
    except WorkspaceInitError as exc:
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "workspace_init_result",
                        "result_status": "FAIL",
                        "code": exc.code,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            typer.echo(render_workspace_init_error(exc), nl=False)
        raise typer.Exit(code=1) from exc


@workspace_app.command("remove")
def workspace_remove_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Remove exact Kit-generated workspace files."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or remove exact Kit-generated operating-layer workspace files."""

    try:
        plan = build_workspace_remove_plan(root.resolve(), execute=execute)
        if execute and plan.result_status == "PASS":
            execute_workspace_remove(plan)
        written = execute and plan.result_status == "PASS"
        if json_output:
            typer.echo(json.dumps(plan.as_json_data(written=written), indent=2, sort_keys=True))
        else:
            typer.echo(render_workspace_remove_plan(plan, written=written), nl=False)
        if plan.result_status == "BLOCKED":
            raise typer.Exit(2)
    except WorkspaceRemoveError as exc:
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "workspace_remove_result",
                        "result_status": "FAIL",
                        "code": exc.code,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            typer.echo(render_workspace_remove_error(exc), nl=False)
        raise typer.Exit(code=1) from exc


@workspace_app.command("upgrade")
def workspace_upgrade_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    execute: Annotated[
        bool, typer.Option("--execute", help="Write the upgraded manifest and backups.")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON.")
    ] = False,
) -> None:
    """Plan or run deterministic workspace manifest schema upgrades."""

    try:
        plan = build_workspace_upgrade_plan(root.resolve(), execute=execute)
        if execute:
            execute_workspace_upgrade(plan)
        if json_output:
            typer.echo(
                json.dumps(
                    plan.as_json_data(written=execute and plan.requires_upgrade),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            typer.echo(
                render_workspace_upgrade_plan(
                    plan,
                    written=execute and plan.requires_upgrade,
                ),
                nl=False,
            )
    except WorkspaceUpgradeError as exc:
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "workspace_upgrade_result",
                        "result_status": "FAIL",
                        "code": exc.code,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            typer.echo(render_workspace_upgrade_error(exc), nl=False)
        raise typer.Exit(code=1) from exc
