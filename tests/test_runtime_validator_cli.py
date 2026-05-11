from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def test_validate_sections_cli_passes_when_sections_are_present(tmp_path) -> None:
    target = tmp_path / "answer.txt"
    target.write_text("Plan\nSolution\nCheck\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-sections",
            str(target),
            "--required-section",
            "Plan",
            "--required-section",
            "Solution",
            "--required-section",
            "Check",
        ],
    )

    assert result.exit_code == 0
    assert "Runtime validation passed." in result.output


def test_validate_sections_cli_fails_when_section_is_missing(tmp_path) -> None:
    target = tmp_path / "answer.txt"
    target.write_text("Plan\nFinal Answer", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate-sections",
            str(target),
            "--required-section",
            "Plan",
            "--required-section",
            "Solution",
            "--required-section",
            "Check",
        ],
    )

    assert result.exit_code == 1
    assert "[error] missing_required_section: Missing required section: Solution" in result.output
    assert "[error] missing_required_section: Missing required section: Check" in result.output
