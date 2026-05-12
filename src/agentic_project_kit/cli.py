from pathlib import Path
import json
import subprocess
from typing import Any

import typer
from .runtime_validator import validate_required_sections
from rich.console import Console
from rich.prompt import Confirm, Prompt

from agentic_project_kit.checks import check_all, check_docs, check_todo
from agentic_project_kit.contract import (
    default_profiles,
    recommended_policy_packs,
    validate_ids,
    PROFILE_DEFINITIONS,
    POLICY_PACK_DEFINITIONS,
)
from agentic_project_kit.doctor import build_doctor_report, render_doctor_report
from agentic_project_kit.github import create_github_repo
from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
from agentic_project_kit.release import (
    build_release_plan,
    build_release_state_report,
    render_release_plan,
    render_release_state_report,
)
from agentic_project_kit.todo import complete_item, list_items, load_todo, render_markdown
from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project
from agentic_project_kit.workflow_cli import workflow_app

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")

workflow_app_registered = workflow_app
app.add_typer(workflow_app_registered, name="workflow")

todo_app = typer.Typer(help="Manage generated project TODO items.")
app.add_typer(todo_app, name="todo")


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

console = Console()


@app.command()
def init(
    name: str | None = typer.Argument(None, help="Project directory/name."),
    project_type: str = typer.Option("python-cli", "--type", help="python-cli, python-lib, generic, governance-wrapper"),
    description: str | None = typer.Option(None, "--description"),
    license_name: str = typer.Option("MIT", "--license"),
    github_actions: bool = typer.Option(True, "--github-actions/--no-github-actions"),
    pre_commit: bool = typer.Option(True, "--pre-commit/--no-pre-commit"),
    agent_docs: bool = typer.Option(True, "--agent-docs/--no-agent-docs"),
    logging_evidence: bool = typer.Option(True, "--logging-evidence/--no-logging-evidence"),
    profiles: str | None = typer.Option(
        None,
        "--profiles",
        help="Comma-separated profile ids. Defaults are recommended from project type.",
    ),
    policy_packs: str | None = typer.Option(
        None,
        "--policy-packs",
        help="Comma-separated policy pack ids. Defaults are recommended from project type.",
    ),
    github: bool = typer.Option(False, "--github/--no-github"),
    github_owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility", help="private or public"),
    kit_source: str = typer.Option(
        "pypi",
        "--kit-source",
        help="agentic-kit install source for generated CI: pypi, testpypi, or none",
    ),
) -> None:
    if name is None:
        name = Prompt.ask("Project name")
    if description is None:
        description = Prompt.ask("Project description", default=f"{name} project")
    if project_type not in {"python-cli", "python-lib", "generic", "governance-wrapper"}:
        raise typer.BadParameter("project type must be python-cli, python-lib, generic, or governance-wrapper")
    if visibility not in {"private", "public"}:
        raise typer.BadParameter("visibility must be private or public")
    if kit_source not in {"pypi", "testpypi", "none"}:
        raise typer.BadParameter("kit source must be pypi, testpypi, or none")

    selected_profiles = _parse_csv(profiles) or default_profiles(
        project_type,
        github_actions=github_actions,
    )
    selected_policy_packs = _parse_csv(policy_packs) or recommended_policy_packs(
        project_type,
        github_actions=github_actions,
        logging_evidence=logging_evidence,
    )
    errors = validate_ids("profile", selected_profiles, PROFILE_DEFINITIONS)
    errors.extend(validate_ids("policy pack", selected_policy_packs, POLICY_PACK_DEFINITIONS))
    if errors:
        raise typer.BadParameter("; ".join(errors))

    target = Path(name).resolve()
    options = ProjectOptions(
        name=name,
        description=description,
        project_type=project_type,
        license_name=license_name,
        github_actions=github_actions,
        pre_commit=pre_commit,
        agent_docs=agent_docs,
        logging_evidence=logging_evidence,
        target_dir=target,
        kit_source=kit_source,
        profiles=selected_profiles,
        policy_packs=selected_policy_packs,
    )

    create_project(options)
    console.print(f"[green]Created project:[/green] {target}")
    console.print("Recommended profiles: " + ", ".join(selected_profiles))
    console.print("Recommended policy packs: " + ", ".join(selected_policy_packs))

    subprocess.run(["git", "add", "."], cwd=target, check=False)
    subprocess.run(["git", "commit", "-m", "Initialize agentic project"], cwd=target, check=False)

    if github:
        if visibility == "public":
            console.print("[bold yellow]Public repository selected. Check for secrets before continuing.[/bold yellow]")
            if not Confirm.ask("Continue with public GitHub repository creation?", default=False):
                raise typer.Exit(code=1)
        create_github_repo(target, owner=github_owner, visibility=visibility, push=True)
        console.print("[green]GitHub repository created and pushed.[/green]")

    console.print("Next:")
    console.print(f"  cd {target}")
    if project_type in {"python-cli", "python-lib"}:
        console.print("  python -m venv .venv")
        console.print("  source .venv/bin/activate")
        console.print('  pip install -e ".[dev]"', markup=False)
        console.print("  pytest -q")
    else:
        console.print("  agentic-kit check-docs")
    console.print("  agentic-kit check")
    console.print("  agentic-kit doctor")


@app.command("check")
def check_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_all(project_root.resolve())
    _print_result(errors)


@app.command("check-docs")
def check_docs_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_docs(project_root.resolve())
    _print_result(errors)


@app.command("check-todo")
def check_todo_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_todo(project_root.resolve())
    _print_result(errors)


@app.command("doctor")
def doctor_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    """Run a compact project health check."""
    report = build_doctor_report(project_root.resolve())
    console.print(render_doctor_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


@app.command("release-plan")
def release_plan_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Print a release preparation checklist for the current project."""
    plan = build_release_plan(project_root.resolve(), version=version)
    console.print(render_release_plan(plan), markup=False)


@app.command("release-check")
def release_check_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Validate release state for a target version."""
    report = build_release_state_report(project_root.resolve(), version=version)
    console.print(render_release_state_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


@app.command("post-release-check")
def post_release_check_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Validate post-release GitHub and Zenodo state without guessing DOI metadata."""
    report = build_post_release_report(project_root.resolve(), version=version)
    console.print(render_post_release_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


@app.command("profile-explain")
def profile_explain_command() -> None:
    """List available project profiles and policy packs."""
    console.print("Project profiles:")
    for profile_id, definition in PROFILE_DEFINITIONS.items():
        description = getattr(definition, "description", str(definition))
        console.print(f"- {profile_id}: {description}")

    console.print("")
    console.print("Policy packs:")
    for policy_pack_id, definition in POLICY_PACK_DEFINITIONS.items():
        description = getattr(definition, "description", str(definition))
        console.print(f"- {policy_pack_id}: {description}")


@app.command("github-create")
def github_create_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility"),
) -> None:
    if visibility not in {"private", "public"}:
        raise typer.BadParameter("visibility must be private or public")
    if visibility == "public":
        console.print("[bold yellow]Public repository selected. Check for secrets before continuing.[/bold yellow]")
        if not Confirm.ask("Continue?", default=False):
            raise typer.Exit(code=1)

    create_github_repo(project_root.resolve(), owner=owner, visibility=visibility, push=True)
    console.print("[green]GitHub repository created and pushed.[/green]")


def _print_result(errors: list[str]) -> None:
    if errors:
        console.print("[bold red]Agentic project check failed[/bold red]")
        for error in errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold green]Agentic project check passed[/bold green]")


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


@app.command("validate-contract")
def validate_contract(
    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/project.yaml."),
) -> None:
    """Validate the machine-readable project contract."""
    from agentic_project_kit.contract import contract_summary, load_project_contract, validate_project_contract

    contract_data = load_project_contract(project_root.resolve())
    if contract_data is None:
        typer.echo("Project contract not found: .agentic/project.yaml", err=True)
        raise typer.Exit(1)

    errors = validate_project_contract(contract_data)
    if errors:
        typer.echo("Project contract validation failed", err=True)
        for error in errors:
            typer.echo(f"- {error}", err=True)
        raise typer.Exit(1)

    typer.echo("Project contract valid.")
    typer.echo(contract_summary(contract_data))


@app.command("validate-output-contract")
def validate_output_contract(
    output_path: Path = typer.Argument(..., help="Output text file to validate."),
    contract_path: Path = typer.Option(..., "--contract", "-c", help="Output contract YAML file."),
    report_path: Path | None = typer.Option(None, "--report", help="Write a JSON validation report."),
    report_schema_path: Path | None = typer.Option(
        None,
        "--report-schema",
        help="Validate the JSON report against a generated validation-report.schema.json file.",
    ),
    repair_output_path: Path | None = typer.Option(
        None,
        "--repair-output",
        help="Write a deterministically repaired output file when supported.",
    ),
    repair_report_path: Path | None = typer.Option(
        None,
        "--repair-report",
        help="Write a JSON repair report. Requires --repair-output.",
    ),
) -> None:
    """Validate an output file against a machine-readable output contract."""
    from agentic_project_kit.output_contract import load_output_contract, validate_output_against_contract

    if repair_report_path is not None and repair_output_path is None:
        typer.echo("--repair-report requires --repair-output.", err=True)
        raise typer.Exit(1)

    try:
        contract = load_output_contract(contract_path)
    except ValueError as exc:
        typer.echo(f"Output contract invalid: {exc}", err=True)
        raise typer.Exit(1) from exc

    output_text = output_path.read_text(encoding="utf-8")
    report = validate_output_against_contract(output_text, contract)
    payload = {
        "ok": report.ok,
        "contract": contract.name,
        "contract_version": contract.version,
        "checked_file": str(output_path),
        "findings": report.to_dict()["findings"],
    }
    if report_schema_path is not None:
        if report_path is None:
            typer.echo("--report-schema requires --report.", err=True)
            raise typer.Exit(1)
        schema_payload = json.loads(report_schema_path.read_text(encoding="utf-8"))
        schema_errors = _validate_report_payload_against_schema(payload, schema_payload)
        if schema_errors:
            typer.echo("Validation report schema check failed:", err=True)
            for error in schema_errors:
                typer.echo(f"- {error}", err=True)
            raise typer.Exit(1)

    if report_path is not None:
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if report.ok:
        typer.echo("Output contract validation passed.")
        raise typer.Exit(0)

    if repair_output_path is not None:
        from agentic_project_kit.output_repair import append_missing_required_sections
        repair_result = append_missing_required_sections(output_text, contract)
        repair_output_path.write_text(repair_result.text, encoding="utf-8")
        if repair_report_path is not None:
            repair_report_path.write_text(
                json.dumps(repair_result.report.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        typer.echo("Output contract validation failed; deterministic repair output written.")
        if repair_result.report.ok:
            typer.echo("Repaired output contract validation passed.")
            raise typer.Exit(0)
        typer.echo("Repaired output contract validation failed.", err=True)
        raise typer.Exit(1)

    for finding in report.findings:
        typer.echo(
            f"[{finding.severity.value}] {finding.code}: {finding.message}",
            err=True,
        )
    raise typer.Exit(1)


def _validate_report_payload_against_schema(
    payload: dict[str, Any],
    schema_payload: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if schema_payload.get("type") != "object":
        errors.append("report schema root type must be object")
        return errors
    required = schema_payload.get("required", [])
    if not isinstance(required, list):
        errors.append("report schema required field must be a list")
        return errors
    for key in required:
        if not isinstance(key, str):
            errors.append("report schema required entries must be strings")
        elif key not in payload:
            errors.append(f"report payload missing required key: {key}")
    properties = schema_payload.get("properties", {})
    if not isinstance(properties, dict):
        errors.append("report schema properties field must be an object")
        return errors
    if schema_payload.get("additionalProperties") is False:
        allowed = set(properties)
        for key in sorted(set(payload) - allowed):
            errors.append(f"report payload contains unexpected key: {key}")
    for key, value in payload.items():
        spec = properties.get(key)
        if isinstance(spec, dict):
            expected_type = spec.get("type")
            if expected_type and not _json_schema_type_matches(value, expected_type):
                errors.append(f"report payload key has wrong type: {key}")
    return errors


def _json_schema_type_matches(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
        return any(_json_schema_type_matches(value, item) for item in expected_type)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "null":
        return value is None
    return True


@app.command("validate-sections")
def validate_sections(
    path: Path = typer.Argument(..., help="Text file to validate."),
    required_section: list[str] = typer.Option(
        ...,
        "--required-section",
        "-s",
        help="Required literal section marker. Repeat the option for multiple sections.",
    ),
) -> None:
    """Validate that a text file contains required literal section markers."""
    report = validate_required_sections(path.read_text(encoding="utf-8"), tuple(required_section))
    if report.ok:
        typer.echo("Runtime validation passed.")
        raise typer.Exit(0)

    for finding in report.findings:
        typer.echo(
            f"[{finding.severity.value}] {finding.code}: {finding.message}",
            err=True,
        )
    raise typer.Exit(1)

if __name__ == "__main__":
    app()
