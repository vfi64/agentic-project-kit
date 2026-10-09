"""Consume only explicitly released entries from an external changelog."""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import re


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
