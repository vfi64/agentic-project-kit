from __future__ import annotations

import py_compile
from pathlib import Path

import typer
import yaml

from agentic_project_kit.final_summary_contract import validate_final_summary
from agentic_project_kit.rule_registry_validator import validate_rule_registry
from agentic_project_kit.workflow_guard import run_workflow_guard

FORBIDDEN_TEXT_PATTERNS = (
    ("heredoc", "<" + "<"),
    ("multiline-python-c", "python " + "-c"),
    ("shell-pipestatus", "PIPE" + "STATUS"),
    ("interactive-exit", "exit " + "0"),
    ("interactive-exit", "exit " + "1"),
)

GOVERNANCE_YAML_FILES = (
    ".agentic/handoff_state.yaml",
    ".agentic/no_copy_terminal_policy.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_migrations.yaml",
    ".agentic/rule_test_coverage.yaml",
    "docs/DOCUMENTATION_COVERAGE.yaml",
)


def existing_paths(paths: list[str]) -> list[Path]:
    return [Path(path) for path in paths if Path(path).exists()]


def check_yaml_files(paths: list[str]) -> list[str]:
    errors: list[str] = []
    for path in existing_paths(paths):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: YAML parse failed: {exc}")
    return errors


def check_python_files(paths: list[str]) -> list[str]:
    errors: list[str] = []
    for path in existing_paths(paths):
        if path.suffix != ".py":
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path}: Python compile failed: {exc.msg}")
    return errors


def check_text_patterns(paths: list[str]) -> list[str]:
    errors: list[str] = []
    for path in existing_paths(paths):
        if path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern in text:
                errors.append(f"{path}: forbidden pattern {name}: {pattern}")
    return errors


def check_final_summary_logs(paths: list[str]) -> list[str]:
    errors: list[str] = []
    for path in existing_paths(paths):
        if path.suffix != ".log":
            continue
        text = path.read_text(encoding="utf-8")
        if "SUMMARY" not in text:
            continue
        for error in validate_final_summary(text):
            errors.append(f"{path}: {error}")
    return errors


def check_rule_registry_files() -> list[str]:
    return [
        f"{finding.path}: {finding.message}"
        for finding in validate_rule_registry()
    ]


def run_preflight(paths: list[str]) -> list[str]:
    checked = list(dict.fromkeys([*paths, *GOVERNANCE_YAML_FILES]))
    errors: list[str] = []
    errors.extend(check_yaml_files([path for path in checked if path.endswith((".yaml", ".yml"))]))
    errors.extend(check_python_files(checked))
    errors.extend(check_text_patterns(paths))
    errors.extend(check_final_summary_logs(paths))
    errors.extend(check_rule_registry_files())
    for finding in run_workflow_guard(paths):
        errors.append(finding.line())
    return errors


def patch_preflight(paths: list[str] = typer.Argument(None)) -> None:
    requested = paths or []
    errors = run_preflight(requested)
    if errors:
        typer.echo("Patch artifact preflight failed")
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(1)
    typer.echo("Patch artifact preflight passed")


def register_patch_preflight_command(app: typer.Typer) -> None:
    app.command("patch-preflight")(patch_preflight)
