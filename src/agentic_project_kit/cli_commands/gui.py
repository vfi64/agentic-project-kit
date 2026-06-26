from __future__ import annotations

import json

import typer

from agentic_project_kit.gui_task_editor import build_initial_llm_prompt


gui_app = typer.Typer(help="Render GUI-facing prompts and helper metadata.")


@gui_app.command("initial-llm-prompt")
def initial_llm_prompt(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    result = build_initial_llm_prompt()
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(result.prompt_text)
