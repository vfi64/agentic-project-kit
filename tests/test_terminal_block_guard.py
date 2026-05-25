from __future__ import annotations

from agentic_project_kit.terminal_block_guard import (
    FORBIDDEN_TERMINAL_PATTERNS,
    check_terminal_block,
)


def test_terminal_block_guard_accepts_safe_block() -> None:
    block = """
printf '\\n\\n\\n'
printf '-------------------------------------------------------------------------\\n'
printf '-------------------------------------------------------------------------\\n'
printf '-------------------------------------------------------------------------\\n'
printf '\\n\\n\\n'
printf '### START ###\\n'
set -e
python3 -m pytest -q tests/test_terminal_block_guard.py
ruff check src tests
sh -n tools/example.sh
printf '### RESULT: PASS ###\\n'
printf 'Terminal bleibt offen. Kein exit am Blockende.\\n'
"""
    report = check_terminal_block(block)
    assert report.ok is True
    assert report.findings == ()


def test_terminal_block_guard_rejects_heredoc() -> None:
    report = check_terminal_block("cat <<EOF > /tmp/x\nhello\nEOF\n")
    assert report.ok is False
    assert any(f.rule_id == "no-heredoc" for f in report.findings)


def test_terminal_block_guard_rejects_multiline_python_c() -> None:
    block = "python3 -c \"print('a')\\nprint('b')\"\n"
    report = check_terminal_block(block)
    assert report.ok is False
    assert any(f.rule_id == "no-multiline-python-c" for f in report.findings)


def test_terminal_block_guard_rejects_open_quote_prompt_markers() -> None:
    report = check_terminal_block("hof@MBP repo % >....\n")
    assert report.ok is False
    assert any(f.rule_id == "no-shell-continuation-prompts" for f in report.findings)


def test_terminal_block_guard_rejects_risky_unquoted_regex_token() -> None:
    report = check_terminal_block("grep -E [0-9]+ file.txt\n")
    assert report.ok is False
    assert any(f.rule_id == "quote-regex-tokens" for f in report.findings)


def test_terminal_block_guard_rejects_terminal_exit() -> None:
    report = check_terminal_block("printf done\nexit\n")
    assert report.ok is False
    assert any(f.rule_id == "no-terminal-exit" for f in report.findings)


def test_terminal_block_guard_rejects_unchecked_final_pass_after_pytest() -> None:
    block = "\n".join(
        [
            "python3 -m pytest -q tests/test_handoff_state_completed_list.py",
            "printf '### RESULT: PASS ###\\n'",
        ]
    )
    report = check_terminal_block(block)
    assert report.ok is False
    assert any(f.rule_id == "no-unchecked-final-pass" for f in report.findings)


def test_terminal_block_guard_rejects_unchecked_final_pass_after_ns_gate() -> None:
    block = "\n".join(
        [
            "./ns check-docs",
            "printf '### RESULT: PASS ###\\n'",
        ]
    )
    report = check_terminal_block(block)
    assert report.ok is False
    assert any(f.rule_id == "no-unchecked-final-pass" for f in report.findings)


def test_terminal_block_guard_accepts_explicit_status_handling() -> None:
    block = "\n".join(
        [
            "python3 -m pytest -q tests/test_handoff_state_completed_list.py",
            'TEST_STATUS="$?"',
            'if [ "$TEST_STATUS" -eq 0 ]; then',
            "  printf '### RESULT: PASS ###\\n'",
            "else",
            "  printf '### RESULT: FAIL ###\\n'",
            "fi",
        ]
    )
    report = check_terminal_block(block)
    assert report.ok is True


def test_terminal_block_guard_accepts_set_e_guarded_pass() -> None:
    block = "\n".join(
        [
            "set -e",
            "python3 -m pytest -q tests/test_handoff_state_completed_list.py",
            "printf '### RESULT: PASS ###\\n'",
        ]
    )
    report = check_terminal_block(block)
    assert report.ok is True


def test_forbidden_pattern_registry_is_non_empty() -> None:
    assert FORBIDDEN_TERMINAL_PATTERNS
    assert {pattern.rule_id for pattern in FORBIDDEN_TERMINAL_PATTERNS} >= {
        "no-heredoc",
        "no-multiline-python-c",
        "no-shell-continuation-prompts",
        "quote-regex-tokens",
        "no-terminal-exit",
        "no-unchecked-final-pass",
    }
