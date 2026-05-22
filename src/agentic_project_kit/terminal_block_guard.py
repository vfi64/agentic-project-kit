from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TerminalBlockFinding:
    code: str
    line: int
    message: str
    text: str


@dataclass(frozen=True)
class TerminalBlockReport:
    ok: bool
    findings: tuple[TerminalBlockFinding, ...]


def check_terminal_block_text(text: str) -> TerminalBlockReport:
    findings: list[TerminalBlockFinding] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if "<<" in line:
            findings.append(TerminalBlockFinding("heredoc", index, "heredoc markers are forbidden", line))
        if "python -c" in line and ("\\n" in line or line.count("'") >= 4 or line.count('"') >= 4):
            findings.append(TerminalBlockFinding("python-c-multiline", index, "multiline python -c is quote-prone", line))
        if "[0-9]+" in line and not _line_has_balanced_quote_around(line, "[0-9]+"):
            findings.append(TerminalBlockFinding("unquoted-regex-glob", index, "unquoted regex fragments can be expanded by zsh", line))
        if stripped == "exit" or stripped.startswith("exit ") or stripped.startswith("exec "):
            findings.append(TerminalBlockFinding("interactive-shell-close", index, "pasted blocks must not close the interactive shell", line))
    return TerminalBlockReport(ok=not findings, findings=tuple(findings))


def check_terminal_block_file(path: Path) -> TerminalBlockReport:
    return check_terminal_block_text(path.read_text(encoding="utf-8"))


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
