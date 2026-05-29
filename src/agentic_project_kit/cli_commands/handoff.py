from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer

from agentic_project_kit.documentation_registry import build_documentation_registry_summary
from agentic_project_kit.handoff_freshness import (
    assess_handoff_prompt_freshness,
    render_freshness_guard,
)
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import (
    current_git_safe_state,
    load_handoff_state,
    refresh_handoff_safe_state,
    save_handoff_state,
    summarize_handoff_state,
    validate_handoff_state,
)

from agentic_project_kit.post_merge_handoff_refresh import evaluate_post_merge_handoff_refresh, render_post_merge_handoff_refresh_status

handoff_app = typer.Typer(help="Read-only persistent handoff state commands.")


@handoff_app.command("show")
def show(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    typer.echo(summarize_handoff_state(data))
    registry_lines = _render_registry_summary(path)
    if registry_lines:
        typer.echo(registry_lines)


@handoff_app.command("check")
def check(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    errors = validate_handoff_state(data)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    typer.echo("Persistent handoff state check passed")
    registry_lines = _render_registry_summary(path)
    if registry_lines:
        typer.echo(registry_lines)


@handoff_app.command("prompt")
def prompt(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    errors = validate_handoff_state(data)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    rendered_prompt = render_handoff_prompt(data)
    guard = render_freshness_guard(
        assess_handoff_prompt_freshness(data, path, successor_prompt_text=rendered_prompt)
    )
    if guard:
        typer.echo(guard)
    typer.echo(rendered_prompt)


@handoff_app.command("refresh")
def refresh(
    path: Annotated[str, typer.Argument()] = ".agentic/handoff_state.yaml",
    write: bool = typer.Option(False, "--write", help="Write refreshed safe_state to YAML."),
) -> None:
    data = load_handoff_state(path)
    git_state = current_git_safe_state()
    refreshed = refresh_handoff_safe_state(
        data,
        git_state["commit"],
        git_state["commit_subject"],
    )
    errors = validate_handoff_state(refreshed)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    current = data.get("safe_state", {})
    updated = refreshed.get("safe_state", {})
    typer.echo(f"Current safe_state: {current.get('commit')} {current.get('commit_subject')}")
    typer.echo(f"Refreshed safe_state: {updated.get('commit')} {updated.get('commit_subject')}")
    if write:
        save_handoff_state(refreshed, path)
        typer.echo(f"Updated {path}")
    else:
        typer.echo("Dry run only. Use --write to update the YAML file.")


def _render_registry_summary(handoff_path: str) -> str:
    summary = _load_registry_summary(handoff_path)
    if summary is None:
        return ""
    lines = [
        "Documentation registry:",
        f"- registry: {summary['registry_path']}",
        f"- version: {summary['version']}",
        f"- documents: {summary['document_count']}",
        f"- broad_migration_allowed: {summary['broad_migration_allowed']}",
    ]
    class_counts = summary.get("class_counts", {})
    if isinstance(class_counts, dict):
        for class_name, count in class_counts.items():
            lines.append(f"- class:{class_name}: {count}")
    return "\n".join(lines)


def _load_registry_summary(handoff_path: str) -> dict[str, Any] | None:
    project_root = _project_root_for_handoff_path(Path(handoff_path))
    try:
        return build_documentation_registry_summary(project_root)
    except (OSError, ValueError):
        return None


def _project_root_for_handoff_path(path: Path) -> Path:
    if path.name == "handoff_state.yaml" and path.parent.name == ".agentic":
        return path.parent.parent
    return Path.cwd()


@handoff_app.command("post-merge-refresh-status")
def post_merge_refresh_status() -> None:
    status = evaluate_post_merge_handoff_refresh(Path("."))
    typer.echo(render_post_merge_handoff_refresh_status(status), nl=False)
    if status.refresh_required:
        raise typer.Exit(1)
