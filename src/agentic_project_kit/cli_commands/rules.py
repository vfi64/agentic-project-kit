from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.communication_rule_context import (
    acknowledge_communication_refresh,
    build_communication_rule_capsule,
    require_current_communication_context,
)
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
    publish: Annotated[
        bool,
        typer.Option("--publish", help="Write d2 pending state and emit carrier metadata."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = refresh_communication_rules(project_root)
    capsule = build_communication_rule_capsule(
        project_root,
        result,
        publish=publish,
        write_pending=publish,
    )
    if json_output:
        data = rule_refresh_result_as_json_data(result)
        data.update(capsule.as_json_data())
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(render_rule_refresh_result(result))
        typer.echo(f"local_only={str(capsule.local_only).lower()}")
        typer.echo(f"remote_readable={str(capsule.remote_readable).lower()}")
        typer.echo(f"blob_sha={capsule.blob_sha}")
        typer.echo(f"must_read_before_continue={str(capsule.must_read_before_continue).lower()}")
        if capsule.pending_state_path:
            typer.echo(f"pending_state_path={capsule.pending_state_path}")
        typer.echo(f"next_action={capsule.next_action}")


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


@rules_app.command("acknowledge-communication-refresh")
def acknowledge_communication_refresh_command(
    ack_file: Annotated[Path, typer.Option("--ack-file", help="Path to RULE_REFRESH_ACK JSON/text.")],
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = acknowledge_communication_refresh(project_root, ack_file)
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("COMMUNICATION_RULE_REFRESH_ACK")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"reason={result.reason}")
        typer.echo(f"source={result.source or '<none>'}")
        typer.echo(f"blob_sha={result.blob_sha or '<none>'}")
        typer.echo(f"generated_at={result.generated_at or '<none>'}")
        typer.echo(f"rules_loaded={str(result.rules_loaded).lower()}")
        typer.echo(f"next_action={result.next_action}")
    if result.result_status != "PASS":
        raise typer.Exit(2)


@rules_app.command("require-current-communication-context")
def require_current_communication_context_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    result = require_current_communication_context(project_root)
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("COMMUNICATION_CONTEXT_GATE")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"reason={result.reason}")
        typer.echo(f"required_next_reply={result.required_next_reply or '<none>'}")
        typer.echo(f"remote_path={result.remote_path}")
        typer.echo(f"communication_context_fresh={str(result.communication_context_fresh).lower()}")
        typer.echo(f"next_action={result.next_action}")
    if result.result_status != "PASS":
        raise typer.Exit(2)


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
