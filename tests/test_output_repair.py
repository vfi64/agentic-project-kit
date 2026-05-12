from agentic_project_kit.output_contract import OutputContract
from agentic_project_kit.output_repair import append_missing_required_sections, missing_required_sections


def _contract() -> OutputContract:
    return OutputContract(version=1, name="default-answer", required_sections=("Plan", "Solution", "Check"))


def test_missing_required_sections_is_deterministic() -> None:
    assert missing_required_sections("Plan\nCheck", _contract()) == ("Solution",)


def test_append_missing_required_sections_repairs_structural_markers() -> None:
    result = append_missing_required_sections("Plan\nCheck", _contract())
    assert "Solution" in result.text
    assert "TODO: fill this section." in result.text
    payload = result.report.to_dict()
    assert payload["ok"] is True
    assert payload["repair_attempted"] is True
    assert payload["operations"] == [
        {
            "kind": "append_missing_required_section",
            "status": "applied",
            "target": "Solution",
            "message": "Appended missing required section marker with explicit placeholder.",
        }
    ]
    assert payload["final_validation"] == {"ok": True, "findings": []}


def test_append_missing_required_sections_noops_when_output_is_valid() -> None:
    text = "Plan\nSolution\nCheck"
    result = append_missing_required_sections(text, _contract())
    assert result.text == text
    payload = result.report.to_dict()
    assert payload["ok"] is True
    assert payload["repair_attempted"] is False
    assert payload["operations"] == []
