from pathlib import Path


def test_portable_contract_requires_clear_wrapper_contract_before_use() -> None:
    text = Path("docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md").read_text(encoding="utf-8")

    assert "use a wrapper only when the wrapper contract is clear" in text
    assert "instead of guessing a wrapper subcommand" in text
    assert "./.venv/bin/python -m agentic_project_kit.cli ..." in text
