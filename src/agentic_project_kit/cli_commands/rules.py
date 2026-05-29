from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.rule_refresh import (
    refresh_communication_rules,
    refresh_handoff_rules,
    render_rule_refresh_result,
    rule_refresh_result_as_json_data,
)

rules_app = typer.Typer(help="Generate repo-backed rule refresh files.")


@rules_app.command("communication-refresh")
def communication_refresh(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = refresh_communication_rules(project_root)
    if json_output:
        typer.echo(json.dumps(rule_refresh_result_as_json_data(result), indent=2, sort_keys=True))
    else:
        typer.echo(render_rule_refresh_result(result))


@rules_app.command("handoff-refresh")
def handoff_refresh(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = refresh_handoff_rules(project_root)
    if json_output:
        typer.echo(json.dumps(rule_refresh_result_as_json_data(result), indent=2, sort_keys=True))
    else:
        typer.echo(render_rule_refresh_result(result))


def register_rules_commands(app: typer.Typer) -> None:
    app.add_typer(rules_app, name="rules")
