from __future__ import annotations

from pathlib import Path


def test_terminal_safety_governance_documents_machine_checked_rules() -> None:
    text = Path("docs/governance/TERMINAL_SAFETY.md").read_text(encoding="utf-8")
    required_terms = [
        "ruff-python-only",
        "terminal-quote-safety",
        "heredoc",
        "python -c",
        "sh -n",
        "terminal_block_guard.py",
    ]
    for term in required_terms:
        assert term in text
