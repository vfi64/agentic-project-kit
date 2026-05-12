from __future__ import annotations

import typer
from rich.console import Console

from agentic_project_kit.todo import complete_item, list_items, load_todo, render_markdown

console = Console()
todo_app = typer.Typer(help="Manage generated project TODO items.")


@todo_app.command("list")
def todo_list(
    all_items: bool = typer.Option(False, "--all", help="Show completed items too."),
) -> None:
    """List project TODO items from .agentic/todo.yaml."""
    data = load_todo()
    items = list_items(data, include_done=all_items)

    if not items:
        console.print("[green]No open TODO items.[/green]")
        return

    for item in items:
        status = item.get("status", "open")
        item_id = item.get("id", "UNKNOWN")
        title = item.get("title", "")
        owner = item.get("owner", "unknown")
        priority = item.get("priority", "normal")
        marker = "✓" if status == "done" else "•"
        console.print(f"{marker} [bold]{item_id}[/bold] [{status}] {title} ({owner}, {priority})")


@todo_app.command("complete")
def todo_complete(
    item_id: str,
    evidence: str = typer.Option(..., "--evidence", help="Evidence for completing the item."),
    render: bool = typer.Option(True, "--render/--no-render", help="Regenerate docs/TODO.md."),
) -> None:
    """Mark a TODO item as done and store evidence."""
    item = complete_item(item_id, evidence=evidence)
    console.print(f"[green]Completed TODO item:[/green] {item.get('id')}")

    if render:
        render_markdown()
        console.print("[green]Rendered docs/TODO.md[/green]")


@todo_app.command("render")
def todo_render() -> None:
    """Regenerate docs/TODO.md from .agentic/todo.yaml."""
    render_markdown()
    console.print("[green]Rendered docs/TODO.md[/green]")
