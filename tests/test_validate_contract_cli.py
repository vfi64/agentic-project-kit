from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.contract import build_contract_data, render_contract_yaml


runner = CliRunner()


def _write_contract(root: Path, data: dict) -> None:
    contract_dir = root / ".agentic"
    contract_dir.mkdir(parents=True)
    (contract_dir / "project.yaml").write_text(render_contract_yaml(data), encoding="utf-8")


def test_validate_contract_cli_passes_for_valid_project_contract(tmp_path: Path) -> None:
    data = build_contract_data(
        name="demo",
        description="Demo project",
        project_type="python-cli",
        profiles=("generic-git-repo", "python-cli"),
        policy_packs=("solo-maintainer",),
    )
    _write_contract(tmp_path, data)

    result = runner.invoke(app, ["validate-contract", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Project contract valid." in result.output
    assert "profiles: generic-git-repo, python-cli" in result.output


def test_validate_contract_cli_fails_when_contract_is_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate-contract", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Project contract not found: .agentic/project.yaml" in result.output


def test_validate_contract_cli_fails_for_invalid_project_contract(tmp_path: Path) -> None:
    data = build_contract_data(
        name="demo",
        description="Demo project",
        project_type="python-cli",
        profiles=("missing",),
        policy_packs=("solo-maintainer",),
    )
    data["project"]["name"] = ""
    _write_contract(tmp_path, data)

    result = runner.invoke(app, ["validate-contract", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Project contract validation failed" in result.output
    assert "project.name is required" in result.output
    assert "unknown profile: missing" in result.output
