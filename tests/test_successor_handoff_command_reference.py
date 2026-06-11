from pathlib import Path


def test_clean_handoff_command_is_repo_discoverable() -> None:
    required = {
        "AGENTS.md": [
            "Clean Handoff Command",
            "agentic-kit transfer chat-switch-complete",
            "docs/reference/agentic-kit-commands.json",
            "A chat must not reconstruct this command from memory",
        ],
        "README.md": [
            "Clean handoff",
            "agentic-kit transfer chat-switch-complete",
            "successor handoff package",
            "validation_report.json",
        ],
        "docs/DOCUMENTATION_COVERAGE.yaml": [
            "successor-handoff-package-command-coverage",
            "chat-switch-complete",
        ],
        "docs/reference/AGENTIC_KIT_COMMANDS.md": [
            "chat-switch-complete",
            "--render-prompt",
        ],
        "docs/reference/agentic-kit-commands.json": [
            "chat-switch-complete",
        ],
    }
    for rel, terms in required.items():
        text = Path(rel).read_text(encoding="utf-8")
        for term in terms:
            assert term in text, f"{term!r} missing from {rel}"
