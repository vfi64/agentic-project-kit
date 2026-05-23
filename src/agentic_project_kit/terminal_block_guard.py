from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForbiddenTerminalPattern:
    rule_id: str
    message: str


@dataclass(frozen=True)
class TerminalBlockFinding:
    code: str
    line: int
    message: str
    text: str

    @property
    def rule_id(self) -> str:
        return self.code


@dataclass(frozen=True)
class TerminalBlockReport:
    ok: bool
    findings: tuple[TerminalBlockFinding, ...]


FORBIDDEN_TERMINAL_PATTERNS: tuple[ForbiddenTerminalPattern, ...] = (
    ForbiddenTerminalPattern("no-heredoc", "heredoc markers are forbidden"),
    ForbiddenTerminalPattern("no-multiline-python-c", "multiline python -c is quote-prone"),
    ForbiddenTerminalPattern(
        "no-shell-continuation-prompts",
        "shell continuation prompts indicate a broken paste state",
    ),
    ForbiddenTerminalPattern(
        "quote-regex-tokens",
        "unquoted regex fragments can be expanded by zsh",
    ),
    ForbiddenTerminalPattern(
        "no-terminal-exit",
        "pasted blocks must not close the interactive shell",
    ),
)

_RULE_MESSAGES = {pattern.rule_id: pattern.message for pattern in FORBIDDEN_TERMINAL_PATTERNS}


def check_terminal_block(text: str) -> TerminalBlockReport:
    return check_terminal_block_text(text)


def check_terminal_block_text(text: str) -> TerminalBlockReport:
    findings: list[TerminalBlockFinding] = []
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if _contains_heredoc_marker(line):
            findings.append(_finding("no-heredoc", index, line))
        if _contains_risky_multiline_python_c(line):
            findings.append(_finding("no-multiline-python-c", index, line))
        if _looks_like_shell_continuation_prompt(stripped):
            findings.append(_finding("no-shell-continuation-prompts", index, line))
        if "[0-9]+" in line and not _line_has_balanced_quote_around(line, "[0-9]+"):
            findings.append(_finding("quote-regex-tokens", index, line))
        if stripped == "exit" or stripped.startswith("exit ") or stripped.startswith("exec "):
            findings.append(_finding("no-terminal-exit", index, line))
    return TerminalBlockReport(ok=not findings, findings=tuple(findings))


def check_terminal_block_file(path: Path) -> TerminalBlockReport:
    return check_terminal_block_text(path.read_text(encoding="utf-8"))


def _finding(rule_id: str, line: int, text: str) -> TerminalBlockFinding:
    return TerminalBlockFinding(rule_id, line, _RULE_MESSAGES[rule_id], text)


def _contains_heredoc_marker(line: str) -> bool:
    return "<<" in line


def _contains_risky_multiline_python_c(line: str) -> bool:
    python_c_tokens = ("python -c", "python3 -c", "python3.12 -c", "python3.13 -c")
    if not any(token in line for token in python_c_tokens):
        return False
    return "\\n" in line or line.count("'") >= 4 or line.count('"') >= 4


def _looks_like_shell_continuation_prompt(stripped: str) -> bool:
    if stripped in {"quote>", "dquote>", "heredoc>"}:
        return True
    return stripped.endswith("% >....") or stripped.startswith(">....")


def _line_has_balanced_quote_around(line: str, needle: str) -> bool:
    pos = line.find(needle)
    if pos < 0:
        return True
    prefix = line[:pos]
    suffix = line[pos + len(needle) :]
    return (prefix.count("'") % 2 == 1 and suffix.count("'") % 2 == 1) or (
        prefix.count('"') % 2 == 1 and suffix.count('"') % 2 == 1
    )


def render_terminal_block_report(report: TerminalBlockReport) -> str:
    lines = ["Terminal block quote-safety report", ""]
    if report.ok:
        lines.append("Overall: PASS")
        return "\n".join(lines)
    for finding in report.findings:
        lines.append(f"[FAIL] line {finding.line}: {finding.code}: {finding.message}")
        lines.append(f"       {finding.text}")
    lines.append("")
    lines.append("Overall: FAIL")
    return "\n".join(lines)
