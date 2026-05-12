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



def test_validate_output_contract_cli_validates_json_report_against_schema(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    report_path = tmp_path / "validation-report.json"
    schema_path = tmp_path / "validation-report.schema.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nSolution\nCheck", encoding="utf-8")
    schema_path.write_text(json.dumps({"type": "object", "additionalProperties": False, "required": ["checked_file", "contract", "contract_version", "findings", "ok"], "properties": {"checked_file": {"type": "string"}, "contract": {"type": "string"}, "contract_version": {"type": "integer"}, "findings": {"type": "array"}, "ok": {"type": "boolean"}}}), encoding="utf-8")
    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
    assert result.exit_code == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["ok"] is True


def test_validate_output_contract_cli_report_schema_requires_report(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    schema_path = tmp_path / "validation-report.schema.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nSolution\nCheck", encoding="utf-8")
    schema_path.write_text(json.dumps({"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}), encoding="utf-8")
    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report-schema", str(schema_path)])
    assert result.exit_code == 1
    assert "--report-schema requires --report." in result.output


def test_validate_output_contract_cli_fails_when_report_schema_rejects_payload(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    report_path = tmp_path / "validation-report.json"
    schema_path = tmp_path / "validation-report.schema.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nSolution\nCheck", encoding="utf-8")
    schema_path.write_text(json.dumps({"type": "object", "required": ["ok", "missing"], "properties": {"ok": {"type": "boolean"}, "missing": {"type": "string"}}}), encoding="utf-8")
    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
    assert result.exit_code == 1
    assert "Validation report schema check failed:" in result.output
    assert "report payload missing required key: missing" in result.output
    assert not report_path.exists()


def test_validate_output_contract_cli_repairs_missing_required_sections(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    repaired_path = tmp_path / "output.repaired.md"
    repair_report_path = tmp_path / "repair-report.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-output-contract",
            str(output_path),
            "--contract",
            str(contract_path),
            "--repair-output",
            str(repaired_path),
            "--repair-report",
            str(repair_report_path),
        ],
    )

    assert result.exit_code == 0
    assert "deterministic repair output written" in result.output
    assert "Repaired output contract validation passed." in result.output
    repaired_text = repaired_path.read_text(encoding="utf-8")
    assert "Solution\nTODO: fill this section." in repaired_text
    assert "Check\nTODO: fill this section." in repaired_text
    payload = json.loads(repair_report_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["repair_attempted"] is True
    assert [operation["target"] for operation in payload["operations"]] == ["Solution", "Check"]
    assert payload["final_validation"] == {"findings": [], "ok": True}


def test_validate_output_contract_cli_repair_report_requires_repair_output(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    output_path = tmp_path / "output.md"
    repair_report_path = tmp_path / "repair-report.json"
    _write_contract(contract_path)
    output_path.write_text("Plan\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-output-contract",
            str(output_path),
            "--contract",
            str(contract_path),
            "--repair-report",
            str(repair_report_path),
        ],
    )

    assert result.exit_code == 1
    assert "--repair-report requires --repair-output." in result.output
    assert not repair_report_path.exists()
