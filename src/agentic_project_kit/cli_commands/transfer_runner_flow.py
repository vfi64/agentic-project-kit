from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.workspace import load_workspace


@transfer_app.command("run-local")
def run_local(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_local_transfer(Path("."), path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"transfer_id={result.transfer_id}")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"next_action={result.next_action}")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("state")
def state(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    snapshot = build_transfer_state(Path("."))
    data = snapshot.as_json_data()
    if json_output:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(f"primary_state={snapshot.primary_state}")
        typer.echo(f"next_action={snapshot.next_action}")

@transfer_app.command("status")
def status(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("inspect")
def inspect(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("apply")
def apply(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:

    from agentic_project_kit.instruction_lint import lint_transfer_instruction

    lint_result = lint_transfer_instruction(path)
    if lint_result.result_status == "BLOCKED":
        payload = lint_result.to_dict()
        if json_output:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            from agentic_project_kit.instruction_lint import render_instruction_lint_result

            print(render_instruction_lint_result(lint_result), end="")
        raise typer.Exit(2)
    warning_text = ""
    if lint_result.result_status == "WARN":
        from agentic_project_kit.instruction_lint import render_instruction_lint_result

        warning_text = render_instruction_lint_result(lint_result)

    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("run_next_command")
    if warning_text:
        warning_path = load_workspace(Path(".")).tmp_file("instruction-lint-warnings.log")
        warning_path.parent.mkdir(parents=True, exist_ok=True)
        warning_path.write_text(warning_text, encoding="utf-8")
    order = _load_or_exit(path)
    result = apply_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("publish-last-report")
def publish_last_report(
    label: str = typer.Option(
        "transfer-handoff",
        "--label",
        help="Label for the published tracked handoff report.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print JSON instead of concise handoff lines.",
    ),
) -> None:
    try:
        result = publish_latest_transfer_report(Path("."), label=label)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        typer.echo("TRANSFER_UPLOAD=missing")
        typer.echo("REMOTE_REPORT=")
        typer.echo("CHAT_REPLY=f")
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_UPLOAD=done")
        typer.echo(f"REMOTE_REPORT={result['remote_report']}")
        typer.echo(f"CHAT_REPLY={result['chat_reply']}")


__all__ = [name for name in globals() if not name.startswith("__")]
