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
