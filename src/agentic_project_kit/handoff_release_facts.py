"""Derive the handoff_state ``release`` block from Kit-written release evidence.

The ``release`` section of ``.agentic/handoff_state.yaml`` feeds the rendered successor
chat handoffs. It used to be maintained by hand and stopped following releases after
0.4.13. The authoritative record of a completed release is the post-release DOI closeout
evidence that ``agentic-kit post-release-doi-closeout --write`` stores; this module reads
that evidence and rewrites only the matching keys of the existing ``release`` section.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.post_release_closeout import DOI_CLOSEOUT_EVIDENCE_DIR

_EVIDENCE_GLOB = "post-release-doi-closeout-*.json"
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class VerifiedRelease:
    version: str
    tag: str
    concept_doi: str
    version_doi: str
    evidence_path: str


def _version_key(version: str) -> tuple[int, int, int] | None:
    match = _VERSION.match(version)
    if not match:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def verified_releases(root: Path) -> list[VerifiedRelease]:
    """Return PASS closeout evidence ordered by semantic version, oldest first."""
    evidence_dir = root / DOI_CLOSEOUT_EVIDENCE_DIR
    releases: list[tuple[tuple[int, int, int], VerifiedRelease]] = []
    for path in sorted(evidence_dir.glob(_EVIDENCE_GLOB)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("result_status") != "PASS":
            continue
        version = str(data.get("version") or "").removeprefix("v")
        key = _version_key(version)
        if key is None:
            continue
        releases.append(
            (
                key,
                VerifiedRelease(
                    version=version,
                    tag=str(data.get("tag") or f"v{version}"),
                    concept_doi=str(data.get("concept_doi") or ""),
                    version_doi=str(data.get("version_doi") or ""),
                    evidence_path=path.relative_to(root).as_posix(),
                ),
            )
        )
    return [release for _, release in sorted(releases, key=lambda item: item[0])]


def release_section_values(root: Path) -> dict[str, str]:
    """Values for the handoff_state ``release`` keys; empty when no verified release exists."""
    releases = verified_releases(root)
    if not releases:
        return {}
    latest = releases[-1]
    values = {
        "current_version": latest.version,
        "tag": latest.tag,
        "post_release_check": "PASS",
        "post_release_evidence": latest.evidence_path,
    }
    if len(releases) > 1:
        values["previous_version"] = releases[-2].version
    if latest.concept_doi:
        values["zenodo_concept_doi"] = latest.concept_doi
    if latest.version_doi:
        values["zenodo_version_doi"] = latest.version_doi
    return values


def sync_release_section(text: str, root: Path) -> str:
    """Rewrite existing keys of the top-level ``release:`` mapping from release evidence.

    Keys that are absent from the section are not added, other sections are untouched,
    and the text is returned unchanged when there is no ``release:`` section or no
    verified release evidence.
    """
    values = release_section_values(root)
    if not values:
        return text
    match = re.search(r"(?ms)^(?P<header>release:\n)(?P<body>(?:^[ \t].*\n?)*)", text)
    if not match:
        return text
    body = match.group("body")
    for key, value in values.items():
        body = re.sub(
            rf"^(\s*{re.escape(key)}:\s*).*$",
            lambda m, value=value: f"{m.group(1)}{value}",
            body,
            count=1,
            flags=re.MULTILINE,
        )
    return text[: match.start("body")] + body + text[match.end("body") :]
