# Validate report schema usability source snippets

Date: 2026-05-12
Branch: feature/validate-report-schema-usability

## Git status
?? docs/reports/validate_report_schema_usability_code_inspection_20260512.md
?? docs/reports/validate_report_schema_usability_source_snippets_20260512.md
?? docs/reports/validate_report_schema_usability_start_20260512.md

## src/agentic_project_kit/cli.py
from pathlib import Path
import json
import subprocess

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

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")

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

## src/agentic_project_kit/runtime_validator.py
"""Runtime validation primitives for generated governance artifacts.

This module intentionally starts small: it provides deterministic, auditable
validation results without performing repair or invoking any model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity for runtime validation findings."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationFinding:
    """Single validation finding with stable machine-readable fields."""

    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[ValidationFinding, ...] = ()

    @property
    def ok(self) -> bool:
        return not any(finding.severity is ValidationSeverity.ERROR for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-safe representation."""
        return {
            "ok": self.ok,
            "findings": [
                {
                    "severity": finding.severity.value,
                    "code": finding.code,
                    "message": finding.message,
                }
                for finding in self.findings
            ],
        }

def validate_required_sections(text: str, required_sections: tuple[str, ...]) -> ValidationReport:
    """Validate that required section markers are present in text.

    The check is intentionally literal and deterministic. This makes it suitable
    as a first runtime skeleton for generated output contracts and governance
    wrapper artifacts.
    """
    findings: list[ValidationFinding] = []
    for section in required_sections:
        if section not in text:
            findings.append(
                ValidationFinding(
                    code="missing_required_section",
                    message=f"Missing required section: {section}",
                )
            )
    return ValidationReport(findings=tuple(findings))

## tests/test_validate_output_contract_cli.py
import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.output_contract import OutputContract, render_output_contract_yaml


runner = CliRunner()


def _write_contract(path: Path) -> None:
    contract = OutputContract(
        version=1,
        name="default-answer",
        required_sections=("Plan", "Solution", "Check"),
    )
    path.write_text(render_output_contract_yaml(contract), encoding="utf-8")


def test_validate_output_contract_cli_passes_for_complete_output(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    _write_contract(contract_path)
    output_path.write_text("Plan\nSolution\nCheck", encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
    )

    assert result.exit_code == 0
    assert "Output contract validation passed." in result.output


def test_validate_output_contract_cli_fails_for_missing_required_sections(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    _write_contract(contract_path)
    output_path.write_text("Plan\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
    )

    assert result.exit_code == 1
    assert "[error] missing_required_section: Missing required section: Solution" in result.output
    assert "[error] missing_required_section: Missing required section: Check" in result.output


def test_validate_output_contract_cli_fails_for_invalid_contract(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    contract_path.write_text("version: 2\nname: broken\nrequired_sections:\n  - Plan\n", encoding="utf-8")
    output_path.write_text("Plan", encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
    )

    assert result.exit_code == 1
    assert "Output contract invalid: output contract version must be 1" in result.output


def test_validate_output_contract_cli_writes_json_report_for_failure(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    report_path = tmp_path / "validation-report.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-output-contract",
            str(output_path),
            "--contract",
            str(contract_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == {
        "checked_file": str(output_path),
        "contract": "default-answer",
        "contract_version": 1,
        "findings": [
            {
                "code": "missing_required_section",
                "message": "Missing required section: Solution",
                "severity": "error",
            },
            {
                "code": "missing_required_section",
                "message": "Missing required section: Check",
                "severity": "error",
            },
        ],
        "ok": False,
    }


def test_validate_output_contract_cli_writes_json_report_for_success(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    report_path = tmp_path / "validation-report.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nSolution\nCheck", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-output-contract",
            str(output_path),
            "--contract",
            str(contract_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(report_path.read_text(encoding="utf-8")) == {
        "checked_file": str(output_path),
        "contract": "default-answer",
        "contract_version": 1,
        "findings": [],
        "ok": True,
    }

## tests/test_runtime_validator.py
from agentic_project_kit.runtime_validator import (
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
    validate_required_sections,
)


def test_validation_report_ok_when_no_findings() -> None:
    report = ValidationReport(findings=())

    assert report.ok is True


def test_validation_report_not_ok_when_error_finding_exists() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                code="missing_required_section",
                message="Missing required section: Final Answer",
            ),
        )
    )

    assert report.ok is False


def test_validation_report_ok_with_warning_only() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                code="soft_notice",
                message="Optional section is absent",
                severity=ValidationSeverity.WARNING,
            ),
        )
    )

    assert report.ok is True


def test_validate_required_sections_accepts_complete_text() -> None:
    report = validate_required_sections(
        "Plan\nSolution\nCheck\nFinal Answer",
        ("Plan", "Solution", "Check", "Final Answer"),
    )

    assert report.ok is True
    assert report.findings == ()


def test_validate_required_sections_reports_missing_sections_deterministically() -> None:
    report = validate_required_sections(
        "Plan\nFinal Answer",
        ("Plan", "Solution", "Check", "Final Answer"),
    )

    assert report.ok is False
    assert [finding.code for finding in report.findings] == [
        "missing_required_section",
        "missing_required_section",
    ]
    assert [finding.message for finding in report.findings] == [
        "Missing required section: Solution",
        "Missing required section: Check",
    ]


def test_validation_report_to_dict_is_json_safe_and_deterministic() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                severity=ValidationSeverity.ERROR,
                code="missing_required_section",
                message="Missing required section: Solution",
            ),
        )
    )

    assert report.to_dict() == {
        "ok": False,
        "findings": [
            {
                "severity": "error",
                "code": "missing_required_section",
                "message": "Missing required section: Solution",
            }
        ],
    }

## tests/test_generator.py
from pathlib import Path

from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project


def test_create_project_generates_core_files(tmp_path: Path):
    target = tmp_path / "demo"
    create_project(
        ProjectOptions(
            name="demo",
            description="Demo project",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    assert (target / "README.md").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / "docs/PROJECT_START.md").exists()
    assert (target / ".agentic/todo.yaml").exists()
    assert (target / ".github/workflows/ci.yml").exists()

def test_generated_ci_uses_pypi_kit_source_by_default(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-default"
    create_project(
        ProjectOptions(
            name="demo-default",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "pip install agentic-project-kit" in ci
    assert "test.pypi.org" not in ci


def test_generated_ci_can_use_testpypi_kit_source(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-testpypi"
    create_project(
        ProjectOptions(
            name="demo-testpypi",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
            kit_source="testpypi",
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "https://test.pypi.org/simple/" in ci
    assert "--extra-index-url https://pypi.org/simple/" in ci
    assert "agentic-project-kit" in ci


def test_generated_ci_can_skip_kit_install(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-none"
    create_project(
        ProjectOptions(
            name="demo-none",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
            kit_source="none",
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "agentic-project-kit install intentionally skipped" in ci
    assert "pip install agentic-project-kit" not in ci
    assert "test.pypi.org" not in ci


def test_generated_project_passes_documentation_and_doctor_gates(tmp_path: Path):
    from agentic_project_kit.checks import check_docs
    from agentic_project_kit.doctor import build_doctor_report

    target = tmp_path / "demo-gates"
    create_project(
        ProjectOptions(
            name="demo-gates",
            description="Demo gates",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    assert (target / "docs/architecture/ARCHITECTURE_CONTRACT.md").exists()
    assert (target / "docs/DOCUMENTATION_COVERAGE.yaml").exists()
    assert (target / "CHANGELOG.md").exists()
    assert "TODO" not in (target / "docs/STATUS.md").read_text(encoding="utf-8")
    assert "TODO" not in (target / "docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert check_docs(target) == []
    assert build_doctor_report(target).ok



def test_governance_wrapper_generates_output_contract_skeleton(tmp_path: Path):
    target = tmp_path / "demo-governance"
    create_project(
        ProjectOptions(
            name="demo-governance",
            description="Demo governance wrapper",
            project_type="governance-wrapper",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    evidence = (target / "docs/LOGGING_AND_EVIDENCE.md").read_text(encoding="utf-8")
    assert "Validation reports from `agentic-kit validate-output-contract --report`" in evidence
    assert "Do not auto-stage validation reports by default" in evidence
    assert (target / "docs/OUTPUT_CONTRACTS.md").exists()
    assert (target / "docs/VALIDATION_AND_REPAIR.md").exists()
    sample = target / "docs/output-contracts/default-answer.yaml"
    assert sample.exists()
    schema_path = target / "docs/schemas/validation-report.schema.json"
    assert schema_path.exists()
    schema_text = schema_path.read_text(encoding="utf-8")
    assert "agentic-project-kit validation report" in schema_text
    assert "checked_file" in schema_text
    assert "missing_required_section" not in schema_text
    sample_text = sample.read_text(encoding="utf-8")
    assert "version: 1" in sample_text
    assert "name: default-answer" in sample_text
    assert "required_sections:" in sample_text
    assert "  - Final Answer" in sample_text
    validation = (target / "docs/VALIDATION_AND_REPAIR.md").read_text(encoding="utf-8")
    assert "Use agentic-kit validate-output-contract" in validation
    assert "docs/output-contracts/default-answer.yaml" in validation
    assert "--report validation-report.json" in validation
    assert "The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`." in validation
    assert "Report shape:" in validation
    assert "missing_required_section" in validation
    assert "consume it without parsing human console output" in validation
    assert "docs/schemas/validation-report.schema.json" in validation
    assert "machine-readable schema for this report shape" in validation
    assert "Use agentic-kit validate-sections as a lower-level check" in validation
    assert "Both commands only check required literal sections" in validation
    assert "Repair attempts must be bounded" in validation
