"""Lossless changelog consumption and bounded release-layout diagnostics."""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import re


def release_layout_problem(text: str, version: str) -> str:
    section = re.search(rf"^##[ \t]+\[?v?{re.escape(version)}\]?(?:[ \t][^\n]*)?\n(?P<body>.*?)(?=^##[ \t]|\Z)",
                        text, re.MULTILINE | re.DOTALL)
    if section is None:
        return ""
    lines = section.group("body").splitlines()
    nonempty = [index for index, line in enumerate(lines) if line.strip()]
    if not nonempty:
        return ""
    offset = text[:section.start("body")].count("\n") + 1
    issues: list[str] = []
    for index, line in enumerate(lines):
        if not line.strip():
            if nonempty[0] < index < nonempty[-1]:
                issues.append(f"line {offset + index}: blank separator between list items")
        elif not line.startswith("- "):
            kind = "indented continuation or nested list" if line[0].isspace() else "paragraph or unsupported list"
            issues.append(f"line {offset + index}: {kind}: {line.strip()[:120]}")
    if not issues:
        return ""
    detail = "; ".join(issues[:20])
    if len(issues) > 20:
        detail += f"; {len(issues) - 20} further layout issue(s)"
    return f"CHANGELOG.md v{version}: {detail}. The release section must be one list of one-line bullets."


def consume_unreleased(text: str, summary_lines: Sequence[str]) -> str:
    section = re.search(r"^##[ \t]+\[?Unreleased\]?[ \t]*\n(?P<body>.*?)(?=^##[ \t]|\Z)",
                        text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if section is None:
        return text
    remaining = Counter(" ".join(line.strip().removeprefix("-").strip().split()) for line in summary_lines)
    body = section.group("body")
    # Top-level bullets only; include indented continuation lines in the match.
    entries = re.compile(r"^[-*][ \t]+[^\n]*(?:\n[ \t]+[^\n]+)*(?:\n|\Z)", re.MULTILINE)

    def keep(match: re.Match[str]) -> str:
        value = " ".join(match.group().strip()[1:].strip().split())
        if remaining[value]:
            remaining[value] -= 1
            return ""
        return match.group()

    updated = entries.sub(keep, body)
    if updated == body:
        return text
    if not updated.strip():
        updated = "\n"
    return text[:section.start("body")] + updated + text[section.end("body"):]
