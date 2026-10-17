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


def _bullets(body: str) -> list[str]:
    entries = re.findall(r"^[-*][ \t]+([^\n]*(?:\n[ \t]+[^\n]+)*)", body, re.MULTILINE)
    return [" ".join(entry.split()) for entry in entries if entry.strip()]


def unreleased_bullets(text: str) -> list[str]:
    section = re.search(r"^##[ \t]+\[?Unreleased\]?[ \t]*\n(?P<body>.*?)(?=^##[ \t]|\Z)",
                        text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return _bullets(section.group("body")) if section else []


def curated_summary_lines(text: str, version: str, explicit: Sequence[str]) -> list[str]:
    """Summary lines for `release.changelog_summary: curated`.

    The release section carries the curated lines only, never the generated PR-title list next
    to them (1.1.0 listed every change twice). Without explicit lines the Unreleased bullets are
    the summary, and on a rerun the existing section is kept. Every Unreleased bullet must be part
    of the summary; otherwise it would stay behind and be announced again with the next release.
    """
    lines = [" ".join(line.strip().removeprefix("-").split()) for line in explicit if line.strip()]
    pending = unreleased_bullets(text)
    if not lines:
        lines = pending
    if not lines:
        section = re.search(rf"^##[ \t]+\[?v?{re.escape(version)}\]?(?:[ \t][^\n]*)?\n(?P<body>.*?)(?=^##[ \t]|\Z)",
                            text, re.MULTILINE | re.DOTALL)
        lines = [line for line in _bullets(section.group("body")) if not line.startswith("Zenodo DOI verification pending")] if section else []
    left = [entry for entry in pending if entry not in lines]
    if left:
        raise ValueError("curated changelog: Unreleased entries missing from the release summary: "
                         + "; ".join(entry[:80] for entry in left))
    if not lines:
        raise ValueError("curated changelog: no summary lines and no Unreleased entries")
    return lines
