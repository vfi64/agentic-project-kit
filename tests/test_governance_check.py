from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.governance import (
    CONSTITUTION_FILES,
    EXTERNAL_WORKSPACE_CONSTITUTION_FILES,
    governance_check,
    render_governance_check,
)
from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init

def test_constitution_files_are_declared_and_present():
    assert ".agentic/project.yaml" in CONSTITUTION_FILES
    assert "docs/architecture/ARCHITECTURE_CONTRACT.md" in CONSTITUTION_FILES
    assert "docs/workflow/WORK_ORDERS.md" in CONSTITUTION_FILES
    for file_name in CONSTITUTION_FILES:
        assert Path(file_name).exists()

def test_governance_check_passes_for_repository_state():
    assert governance_check() == []
    assert render_governance_check([]) == "Governance check passed"

def test_governance_check_cli_passes():
    result = CliRunner().invoke(app, ["governance", "check"])
    assert result.exit_code == 0
    assert "Governance check passed" in result.output


def test_governance_check_passes_for_external_manifest_workspace(tmp_path: Path):
    plan = build_workspace_init_plan(tmp_path, execute=True)
    execute_workspace_init(plan)

    assert governance_check(tmp_path) == []
    for file_name in EXTERNAL_WORKSPACE_CONSTITUTION_FILES:
        assert (tmp_path / file_name).exists()


def test_governance_check_cli_accepts_external_root(tmp_path: Path):
    plan = build_workspace_init_plan(tmp_path, execute=True)
    execute_workspace_init(plan)

    result = CliRunner().invoke(app, ["governance", "check", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Governance check passed" in result.output
