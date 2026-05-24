from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workflow_guard import check_yaml_parseability, run_workflow_guard


def test_workflow_guard_passes_current_repository_state() -> None:
    assert run_workflow_guard([]) == []


def test_workflow_guard_cli_passes_current_repository_state() -> None:
    result = CliRunner().invoke(app, ["workflow-guard", "check"])
    assert result.exit_code == 0
    assert "Workflow guard passed" in result.output


def test_workflow_guard_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("rules: broken: value\n", encoding="utf-8")
    findings = check_yaml_parseability([path])
    assert findings
    assert findings[0].pattern_id == "yaml-parse-failure"
    assert findings[0].severity == "HARD-FAIL"


def test_workflow_guard_policy_documents_repair_plan() -> None:
    text = Path("docs/workflow/WORKFLOW_GUARD.md").read_text(encoding="utf-8")
    assert "diagnose-and-fail" in text
    assert "protected control files" in text
    assert "repair plan" in text


def test_workflow_guard_keeps_control_file_length_policy() -> None:
    text = Path(".agentic/control_file_preservation.yaml").read_text(encoding="utf-8")
    assert "no_hard_length_limit" in text
    assert "Information preservation outranks compactness" in text
    assert "hard_length_limit_trimming" in text
