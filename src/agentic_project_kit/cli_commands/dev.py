from __future__ import annotations

import typer

from agentic_project_kit.local_feature_gate import run_local_feature_gate

dev_app = typer.Typer(help="Run local developer gates without remote side effects.")


@dev_app.command("local-feature-gate", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def local_feature_gate_command(
    ctx: typer.Context,
    include_pr_hygiene: bool = typer.Option(
        False,
        "--include-pr-hygiene",
        help="Also run PR hygiene after the local feature gate.",
    ),
) -> None:
    """Run the local feature gate through the supported agentic-kit CLI."""
    pytest_args = list(ctx.args)
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    raise typer.Exit(code=run_local_feature_gate(pytest_args, include_pr_hygiene=include_pr_hygiene))
