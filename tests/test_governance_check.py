from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.governance import CONSTITUTION_FILES, governance_check, render_governance_check

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
