from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from agentic_project_kit.runtime_validator import validate_required_sections


def register_validation_commands(app: typer.Typer) -> None:
    app.command("validate-contract")(validate_contract)
    app.command("validate-output-contract")(validate_output_contract)
    app.command("validate-sections")(validate_sections)


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
