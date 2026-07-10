from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from agentic_project_kit.workspace import load_workspace


@dataclass(frozen=True)
class StaleFragment:
    path: str
    fragment: str


STATE_FILES = ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md")
HANDOFF_STATE_FILE = ".agentic/handoff_state.yaml"
ACTIVE_HANDOFF_TEXT_FIELDS = (
    ("first_instruction", ("first_instruction",)),
    ("open_items.next_expected_chat_action", ("open_items", "next_expected_chat_action")),
)
VERSION_RE = re.compile(r"\bv?(\d+\.\d+\.\d+)\b")
CLOSEOUT_EVIDENCE_RE = re.compile(r"\brecord(?:\s+and\s+merge)?\s+PR\s*#?(\d+)\s+closeout\s+evidence\b", re.IGNORECASE)

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
        findings.extend(_stale_closeout_evidence_findings(base, relative, text))
    findings.extend(_stale_handoff_state_findings(base))
    return findings


def _stale_closeout_evidence_findings(base: Path, relative: str, text: str) -> list[StaleFragment]:
    findings: list[StaleFragment] = []
    seen_prs: set[str] = set()
    for match in CLOSEOUT_EVIDENCE_RE.finditer(text):
        pr_number = match.group(1)
        if pr_number in seen_prs:
            continue
        seen_prs.add(pr_number)
        workspace = load_workspace(base)
        evidence_path = workspace.terminal_report_file(f"pr{pr_number}-merge-finalize.log")
        if evidence_path.exists():
            findings.append(
                StaleFragment(
                    relative,
                    f"stale closeout instruction for PR{pr_number}; {workspace.path_text(evidence_path)} already exists",
                )
            )
    return findings


def _stale_handoff_state_findings(base: Path) -> list[StaleFragment]:
    path = base / HANDOFF_STATE_FILE
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [StaleFragment(HANDOFF_STATE_FILE, f"handoff state YAML parse failed: {exc}")]
    if not isinstance(data, dict):
        return [StaleFragment(HANDOFF_STATE_FILE, "handoff state is not a YAML mapping")]

    findings: list[StaleFragment] = []
    current_version = str(_mapping_get(data, ("release", "current_version")) or "")
    current_version_tuple = _version_tuple(current_version)
    for label, field_path in ACTIVE_HANDOFF_TEXT_FIELDS:
        text = _mapping_get(data, field_path)
        if not isinstance(text, str) or not text:
            continue
        field_label = f"{HANDOFF_STATE_FILE}:{label}"
        if current_version_tuple is not None:
            for version in sorted(set(VERSION_RE.findall(text)), key=_version_sort_key):
                parsed = _version_tuple(version)
                if parsed is not None and parsed < current_version_tuple:
                    findings.append(
                        StaleFragment(
                            field_label,
                            f"active handoff instruction references stale version {version}; current release is {current_version}",
                        )
                    )
        findings.extend(_stale_closeout_evidence_findings(base, field_label, text))
    return findings


def _mapping_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _version_tuple(version: str) -> tuple[int, int, int] | None:
    match = VERSION_RE.fullmatch(version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))  # type: ignore[return-value]


def _version_sort_key(version: str) -> tuple[int, int, int]:
    return _version_tuple(version) or (0, 0, 0)


def format_findings(findings: list[StaleFragment]) -> str:
    if not findings:
        return "PASS: no stale STATUS/HANDOFF/handoff-state current-state fragments found"
    lines = ["FAIL: stale STATUS/HANDOFF/handoff-state current-state fragments found"]
    for finding in findings:
        lines.append(f"- {finding.path}: {finding.fragment}")
    return "\n".join(lines)
