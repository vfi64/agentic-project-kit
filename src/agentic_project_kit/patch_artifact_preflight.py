from __future__ import annotations

import py_compile
from collections.abc import Callable
from pathlib import Path

import typer
import yaml

from agentic_project_kit import slice_gate
from agentic_project_kit.run_summary_renderer import validate_rendered_summary_text
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

SliceGateRunner = Callable[[str, Path], slice_gate.SliceGateReport]


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
        for error in validate_rendered_summary_text(text):
            errors.append(f"{path}: {error}")
    return errors


def check_rule_registry_files() -> list[str]:
    return [
        f"{finding.path}: {finding.message}"
        for finding in validate_rule_registry()
    ]


def _run_slice_gate(kind: str, project_root: Path) -> slice_gate.SliceGateReport:
    return slice_gate.run_slice_gate(kind, project_root=project_root)


def check_required_slice_gate(
    kind: str,
    *,
    project_root: Path = Path("."),
    runner: SliceGateRunner | None = None,
) -> list[str]:
    report = (runner or _run_slice_gate)(kind, project_root)
    errors: list[str] = []
    if report.slice_result != "PASS":
        errors.append(f"slice gate {kind}: slice_result={report.slice_result}")
    if report.dirty_state.state != "CLEAN":
        errors.append(f"slice gate {kind}: dirty_state={report.dirty_state.state}")
    if errors:
        rendered = slice_gate.render_slice_gate_report(report).splitlines()
        errors.extend(f"slice gate {kind}: {line}" for line in rendered)
    return errors


def run_preflight(paths: list[str], *, require_slice_gate: str | None = None, slice_gate_runner: SliceGateRunner | None = None) -> list[str]:
    checked = list(dict.fromkeys([*paths, *GOVERNANCE_YAML_FILES]))
    errors: list[str] = []
    errors.extend(check_yaml_files([path for path in checked if path.endswith((".yaml", ".yml"))]))
    errors.extend(check_python_files(checked))
    errors.extend(check_text_patterns(paths))
    errors.extend(check_final_summary_logs(paths))
    errors.extend(check_rule_registry_files())
    for finding in run_workflow_guard(paths):
        errors.append(finding.line())
    if require_slice_gate:
        errors.extend(check_required_slice_gate(require_slice_gate, project_root=Path("."), runner=slice_gate_runner))
    return errors


def patch_preflight(paths: list[str] = typer.Argument(None), require_slice_gate: str | None = typer.Option(None, "--require-slice-gate", help="Require a clean passing slice gate before accepting preflight.")) -> None:
    requested = paths or []
    errors = run_preflight(requested, require_slice_gate=require_slice_gate)
    if errors:
        typer.echo("Patch artifact preflight failed")
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(1)
    typer.echo("Patch artifact preflight passed")
    if require_slice_gate:
        typer.echo(f"Required slice gate passed: {require_slice_gate}")


def register_patch_preflight_command(app: typer.Typer) -> None:
    app.command("patch-preflight")(patch_preflight)
