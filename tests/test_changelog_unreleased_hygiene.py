"""Released changelog entries must leave the Unreleased section (KIT-GF-060 follow-up).

Release preparation removes an Unreleased bullet only when a release summary line matches it
verbatim. For 1.0.25 the summary lines were reworded, so eleven released entries stayed in
Unreleased and would have been announced again with the next release. Reworded duplicates
cannot be matched by text; the finding ids they carry can.

K8 (V1): whether a finding shipped is read from the greenfield catalog (``fixed_in`` names a
released version), not from any mention in a released section. The v1.2.0 section named
KIT-GF-096 as a future obligation; the text rule then rejected the 1.3.0 Unreleased line that
fixed it and closed the Unreleased path for the Kit's own curated release.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
CATALOG = ROOT / ".agentic" / "greenfield_findings.json"
SECTION = re.compile(r"^## (?P<title>[^\n]+)\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
RELEASE_TITLE = re.compile(r"v(?P<version>\d+\.\d+\.\d+)\b")
ID_GROUP = re.compile(r"KIT-GF-(?P<first>[A-Z0-9]+(?:-[A-Z]+)*)(?P<more>(?:/[0-9]{3})*)")


def finding_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for match in ID_GROUP.finditer(text):
        ids.add(f"KIT-GF-{match.group('first')}")
        ids.update(f"KIT-GF-{number}" for number in match.group("more").split("/") if number)
    return ids


def shipped_ids(changelog: str, catalog: dict) -> set[str]:
    """Finding ids whose catalog ``fixed_in`` is a version with a released changelog section."""
    released = {m.group("version") for title in (s.group("title") for s in SECTION.finditer(changelog))
                if (m := RELEASE_TITLE.match(title))}
    return {entry["id"] for entry in catalog.get("findings", [])
            if str(entry.get("fixed_in") or "") in released}


def stale_unreleased_lines(changelog: str, catalog: dict) -> list[str]:
    sections = {m.group("title"): m.group("body") for m in SECTION.finditer(changelog)}
    shipped = shipped_ids(changelog, catalog)
    stale = []
    for line in sections.get("Unreleased", "").splitlines():
        if line.startswith("- ") and finding_ids(line) & shipped:
            stale.append(f"{sorted(finding_ids(line) & shipped)}: {line[:100]}")
    return stale


def test_finding_ids_expand_slash_lists() -> None:
    assert finding_ids("(KIT-GF-001/003/016) and KIT-GF-RULE-REGISTRY-BOOTSTRAP") == {
        "KIT-GF-001", "KIT-GF-003", "KIT-GF-016", "KIT-GF-RULE-REGISTRY-BOOTSTRAP"}


def test_a_finding_named_as_future_obligation_in_a_release_is_not_shipped() -> None:
    """V1: v1.2.0 named KIT-GF-096 as a future duty; the catalog still said unreleased."""
    changelog = ("## Unreleased\n\n- Fixed: projection v2 everywhere (KIT-GF-096).\n\n"
                 "## v1.2.0 - 2026-11-03\n\n- Changed: KIT-GF-096 becomes mandatory in 1.3.0.\n")
    catalog = {"findings": [{"id": "KIT-GF-096", "fixed_in": "unreleased"}]}
    assert stale_unreleased_lines(changelog, catalog) == []
    catalog = {"findings": [{"id": "KIT-GF-096", "fixed_in": "1.2.0"}]}
    assert len(stale_unreleased_lines(changelog, catalog)) == 1


def test_unreleased_names_no_finding_that_a_release_already_shipped() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    stale = stale_unreleased_lines(CHANGELOG.read_text(encoding="utf-8"), catalog)
    assert not stale, "remove released entries from Unreleased:\n" + "\n".join(stale)
