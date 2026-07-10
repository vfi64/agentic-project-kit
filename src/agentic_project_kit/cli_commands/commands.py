from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.command_selector import (
    render_command_selection,
    select_for_raw,
    select_for_task,
)
from agentic_project_kit.command_manifest import (
    MD_PATH,
    evaluate_command_manifest,
    load_manifest,
    render_command_manifest_audit,
    render_markdown,
)


commands_app = typer.Typer(help="Inspect and render the agentic-kit command manifest.")


@commands_app.command("render-md")
def commands_render_md_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    execute: bool = typer.Option(False, "--execute", help="Write generated Markdown."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Render docs/reference/AGENTIC_KIT_COMMANDS.md from the JSON manifest."""
    root = root.resolve()
    data = load_manifest(root)
    rendered = render_markdown(data)
    path = root / MD_PATH
    changed = path.read_text(encoding="utf-8") != rendered if path.exists() else True
    if execute:
        path.write_text(rendered, encoding="utf-8")
    payload = {
        "schema_version": 1,
        "kind": "commands_render_md_result",
        "result_status": "PASS",
        "path": MD_PATH.as_posix(),
        "changed": changed,
        "written": bool(execute),
        "manifest_sha": (data.get("meta") or {}).get("manifest_sha"),
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if execute:
            typer.echo(f"COMMANDS_RENDER_MD\nSTATUS=PASS\nWRITTEN={path.as_posix()}\n")
        else:
            typer.echo(rendered, nl=False)


def audit_command_manifest_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Audit command manifest hash, CLI coverage, safety metadata, and MD sync."""
    audit = evaluate_command_manifest(root.resolve())
    if json_output:
        typer.echo(json.dumps(audit.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_command_manifest_audit(audit), nl=False)
    if not audit.ok:
        raise typer.Exit(code=audit.returncode)


def command_for_command(
    raw: str | None = typer.Option(None, "--raw", help="Raw command line to map to a wrapper."),
    task: str | None = typer.Option(None, "--task", help="Task tag to list matching commands."),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Select the deterministic wrapper command for a raw command or task tag."""
    if bool(raw) == bool(task):
        typer.echo("Provide exactly one of --raw or --task.", err=True)
        raise typer.Exit(code=2)
    manifest = load_manifest(root.resolve())
    selection = select_for_raw(manifest, raw) if raw is not None else select_for_task(manifest, str(task))
    if json_output:
        typer.echo(json.dumps(selection.payload, indent=2, sort_keys=True))
    else:
        typer.echo(render_command_selection(selection), nl=False)
