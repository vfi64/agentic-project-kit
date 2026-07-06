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
from agentic_project_kit.workspace_adopt import (
    analyze_workspace_adoption,
    render_workspace_adopt_report,
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
