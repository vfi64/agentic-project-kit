from pathlib import Path

import pytest

from agentic_project_kit.output_contract import (
    OutputContract,
    load_output_contract,
    parse_output_contract,
    render_output_contract_yaml,
)


def test_parse_output_contract_accepts_minimal_contract() -> None:
    contract = parse_output_contract(
        {
            "version": 1,
            "name": "default-answer",
            "required_sections": ["Plan", "Solution", "Check", "Final Answer"],
        }
    )

    assert contract == OutputContract(
        version=1,
        name="default-answer",
        required_sections=("Plan", "Solution", "Check", "Final Answer"),
    )


def test_output_contract_yaml_roundtrip(tmp_path: Path) -> None:
    contract = OutputContract(
        version=1,
        name="default-answer",
        required_sections=("Plan", "Solution", "Check"),
    )
    path = tmp_path / "output-contract.yaml"
    path.write_text(render_output_contract_yaml(contract), encoding="utf-8")

    assert load_output_contract(path) == contract


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([], "output contract must be a mapping"),
        ({"version": 2, "name": "x", "required_sections": ["A"]}, "output contract version must be 1"),
        ({"version": 1, "name": "", "required_sections": ["A"]}, "output contract name is required"),
        ({"version": 1, "name": "x", "required_sections": []}, "required_sections must be a non-empty list"),
        ({"version": 1, "name": "x", "required_sections": [""]}, "required_sections must contain non-empty strings"),
    ],
)
def test_parse_output_contract_rejects_invalid_shapes(data, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_output_contract(data)
