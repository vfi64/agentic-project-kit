from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.patch_artifact_preflight import (
    check_python_files,
    check_rule_registry_files,
    check_text_patterns,
    check_yaml_files,
    run_preflight,
)


def test_preflight_accepts_current_governance_yaml() -> None:
    assert check_yaml_files([
        ".agentic/handoff_state.yaml",
        ".agentic/no_copy_terminal_policy.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_migrations.yaml",
        "docs/DOCUMENTATION_COVERAGE.yaml",
    ]) == []


def test_preflight_rule_registry_validation_passes_current_state() -> None:
    assert check_rule_registry_files() == []


def test_preflight_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("key: value: broken\n", encoding="utf-8")
    assert check_yaml_files([str(path)])


def test_preflight_rejects_invalid_python(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_text("def broken(:\n", encoding="utf-8")
    assert check_python_files([str(path)])


def test_preflight_rejects_forbidden_shell_patterns(tmp_path: Path) -> None:
    path = tmp_path / "patch.sh"
    path.write_text("python " + "-c bad\n", encoding="utf-8")
    errors = check_text_patterns([str(path)])
    assert any("multiline-python-c" in error for error in errors)


def test_preflight_cli_passes_for_current_yaml_files() -> None:
    result = CliRunner().invoke(app, ["patch-preflight"])
    assert result.exit_code == 0
    assert "Patch artifact preflight passed" in result.output


def test_preflight_full_runner_includes_governance_yaml() -> None:
    errors = run_preflight([])
    assert errors == []


def test_preflight_includes_rule_registry_files() -> None:
    assert ".agentic/rule_mechanism_inventory.yaml" in tuple(
        __import__("agentic_project_kit.patch_artifact_preflight", fromlist=["GOVERNANCE_YAML_FILES"]).GOVERNANCE_YAML_FILES
    )
    assert ".agentic/rule_migrations.yaml" in tuple(
        __import__("agentic_project_kit.patch_artifact_preflight", fromlist=["GOVERNANCE_YAML_FILES"]).GOVERNANCE_YAML_FILES
    )


def test_coverage_terms_still_parse_as_strings() -> None:
    data = yaml.safe_load(Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8"))
    for rule in data.get("rules", []):
        for document in rule.get("documents", []):
            assert all(isinstance(term, str) for term in document.get("terms", []))
