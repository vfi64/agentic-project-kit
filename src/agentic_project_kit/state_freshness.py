from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StaleFragment:
    path: str
    fragment: str


STATE_FILES = ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md")

STALE_CURRENT_STATE_FRAGMENTS = (
    "Current released version: 0.3.19",
    "Current completed slice: GUI Tk setup documentation",
    "Status-date: 2026-05-16",
    "v0.3.23 is released and post-release verified",
    "v0.3.25 is released and post-release verified",
    "v0.3.19 is released and post-release verified",
    "Completed slice: v0.3.19 Cockpit Action Selection UX",
    "Current slice: document GUI i18n",
)


def find_stale_state_fragments(root: Path | None = None) -> list[StaleFragment]:
    base = Path.cwd() if root is None else root
    findings: list[StaleFragment] = []
    for relative in STATE_FILES:
        path = base / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in STALE_CURRENT_STATE_FRAGMENTS:
            if fragment in text:
                findings.append(StaleFragment(relative, fragment))
    return findings


def format_findings(findings: list[StaleFragment]) -> str:
    if not findings:
        return "PASS: no stale STATUS/HANDOFF current-state fragments found"
    lines = ["FAIL: stale STATUS/HANDOFF current-state fragments found"]
    for finding in findings:
        lines.append(f"- {finding.path}: {finding.fragment}")
    return "\n".join(lines)
