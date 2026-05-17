from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentic_project_kit.scaffold import PlanningDocSpec, planning_doc_path, write_planning_doc


console = Console()
scaffold_app = typer.Typer(help="Create governed repository scaffolding artifacts.")


@scaffold_app.command("planning-doc")
def planning_doc_command(
    title: Annotated[str, typer.Argument(help="Planning document title")],
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    status: Annotated[str, typer.Option("--status")] = "active",
    decision_status: Annotated[str, typer.Option("--decision-status")] = "proposed",
    scope: Annotated[str, typer.Option("--scope")] = "planning",
    review_policy: Annotated[str, typer.Option("--review-policy")] = "review before implementation and after each milestone",
    output: Annotated[Path | None, typer.Option("--output")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    spec = PlanningDocSpec(
        title=title,
        status=status,
        decision_status=decision_status,
        scope=scope,
        review_policy=review_policy,
    )
    root = project_root.resolve()
    target = output.resolve() if output is not None else planning_doc_path(root, title)
    try:
        written = write_planning_doc(target, spec, overwrite=overwrite)
    except FileExistsError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=2) from exc
    console.print("Planning document scaffolded", markup=False)
    console.print(f"path={written}", markup=False)
    console.print("Safety: created or updated only the requested planning document path.", markup=False)
