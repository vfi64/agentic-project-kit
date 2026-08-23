from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.planner_executor import (
    build_planner_executor_plan,
    load_planner_executor_intent,
    planner_executor_plan_as_json_data,
    planner_executor_result_as_json_data,
    render_planner_executor_plan,
    render_planner_executor_result,
    run_planner_executor_intent,
)

executor_app = typer.Typer(help="Plan and run governed Planner-Kit-Executor intents.")


@executor_app.command("plan")
def executor_plan_command(
    intent_path: Annotated[Path, typer.Argument(help="Planner-executor intent YAML path.")],
    project_root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    """Resolve a planner intent against Kit-owned command and cockpit authorities."""
    intent = load_planner_executor_intent(intent_path)
    plan = build_planner_executor_plan(intent, project_root.resolve())
    if json_output:
        typer.echo(json.dumps(planner_executor_plan_as_json_data(plan), indent=2, sort_keys=True))
        return
    typer.echo(render_planner_executor_plan(plan))


@executor_app.command("run")
def executor_run_command(
    intent_path: Annotated[Path, typer.Argument(help="Planner-executor intent YAML path.")],
    project_root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    execute: Annotated[bool, typer.Option("--execute", help="Execute allowed steps. Default is dry-run.")] = False,
    allow_bounded: Annotated[
        bool,
        typer.Option("--allow-bounded", help="Allow steps that are both bounded and marked allow_bounded in the intent."),
    ] = False,
    report: Annotated[
        Path | None,
        typer.Option("--report", help="Write bounded JSON result under docs/reports/ or tmp/."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    """Run a governed planner intent through Kit-owned execution surfaces."""
    intent = load_planner_executor_intent(intent_path)
    result = run_planner_executor_intent(
        intent,
        project_root.resolve(),
        execute=execute,
        allow_bounded=allow_bounded,
        report_path=report,
    )
    if json_output:
        typer.echo(json.dumps(planner_executor_result_as_json_data(result), indent=2, sort_keys=True))
    else:
        typer.echo(render_planner_executor_result(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
