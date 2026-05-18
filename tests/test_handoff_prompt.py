from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state

def test_handoff_prompt_contains_required_sections_and_active_rules_only():
    data = load_handoff_state()
    prompt = render_handoff_prompt(data)
    assert "## Repo" in prompt
    assert "## Sicherer Stand" in prompt
    assert "## Aktive Regeln" in prompt
    assert "no-copy-terminal-evidence" in prompt
    assert "manual-copy-terminal-by-default" not in prompt

def test_handoff_cli_commands():
    runner = CliRunner()
    check_result = runner.invoke(app, ["handoff", "check"])
    assert check_result.exit_code == 0
    assert "check passed" in check_result.output
    show_result = runner.invoke(app, ["handoff", "show"])
    assert show_result.exit_code == 0
    assert "agentic-project-kit" in show_result.output
    prompt_result = runner.invoke(app, ["handoff", "prompt"])
    assert prompt_result.exit_code == 0
    assert "Übergabeprompt" in prompt_result.output
