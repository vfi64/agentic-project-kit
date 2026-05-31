from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.rule_ack import build_rule_acknowledgement
from agentic_project_kit.rule_refresh import (
    refresh_communication_rules,
    refresh_handoff_rules,
    render_rule_refresh_result,
    rule_refresh_result_as_json_data,
)
from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot
from agentic_project_kit.rule_source_validator import (
    render_rule_source_validation,
    validate_rule_sources,
)

rules_app = typer.Typer(help="Generate repo-backed rule refresh files.")


def _run_git(project_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        return ""
    return process.stdout.strip()


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


@rules_app.command("snapshot")
def snapshot(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = build_derived_rule_snapshot(project_root)
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("RULE_SNAPSHOT")
        typer.echo(f"schema_version={result.schema_version}")
        typer.echo(f"snapshot_id={result.snapshot_id}")
        typer.echo(f"sources_total={result.sources_total}")
        typer.echo(f"is_valid={result.is_valid}")
        typer.echo(f"fail_closed={result.fail_closed}")
        typer.echo(f"source_digests_total={len(result.source_digests)}")
        for reason in result.validation.blocking_reasons:
            typer.echo(f"blocking_reason={reason}")
    if result.fail_closed:
        raise typer.Exit(1)


@rules_app.command("acknowledge")
def acknowledge(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    output_path: Annotated[Path, typer.Option("--output")] = Path(".agentic/rule_ack/current.json"),
    next_allowed_action: Annotated[str, typer.Option("--next-allowed-action")] = "run_next_command",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    root = project_root.resolve()
    snapshot = build_derived_rule_snapshot(root)
    if snapshot.fail_closed:
        if json_output:
            typer.echo(json.dumps(snapshot.as_json_data(), indent=2, sort_keys=True))
        else:
            typer.echo("RULE_ACKNOWLEDGEMENT")
            typer.echo("written=False")
            typer.echo("reason=rule_snapshot_fail_closed")
            for reason in snapshot.validation.blocking_reasons:
                typer.echo(f"blocking_reason={reason}")
        raise typer.Exit(1)

    repo_head = _run_git(root, "rev-parse", "--short", "HEAD") or "UNKNOWN"
    acknowledgement = build_rule_acknowledgement(
        snapshot,
        repo_head=repo_head,
        declared_next_allowed_action=next_allowed_action,
    )

    target = output_path
    if not target.is_absolute():
        target = root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(acknowledgement.as_json_data(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    relative_path = target.relative_to(root) if target.is_relative_to(root) else target

    if json_output:
        data = {
            "path": str(relative_path),
            "written": True,
            "acknowledgement": acknowledgement.as_json_data(),
        }
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo("RULE_ACKNOWLEDGEMENT")
        typer.echo(f"path={relative_path}")
        typer.echo("written=True")
        typer.echo(f"schema_version={acknowledgement.schema_version}")
        typer.echo(f"snapshot_id={acknowledgement.snapshot_id}")
        typer.echo(f"repo_head={acknowledgement.repo_head}")
        typer.echo(f"declared_next_allowed_action={acknowledgement.declared_next_allowed_action}")


@rules_app.command("validate-sources")
def validate_sources(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = validate_rule_sources(project_root)
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(render_rule_source_validation(result))
    if result.fail_closed:
        raise typer.Exit(1)


def register_rules_commands(app: typer.Typer) -> None:
    app.add_typer(rules_app, name="rules")
