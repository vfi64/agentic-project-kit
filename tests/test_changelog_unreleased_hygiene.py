"""Released changelog entries must leave the Unreleased section (KIT-GF-060 follow-up).

Release preparation removes an Unreleased bullet only when a release summary line matches it
verbatim. For 1.0.25 the summary lines were reworded, so eleven released entries stayed in
Unreleased and would have been announced again with the next release. Reworded duplicates
cannot be matched by text; the finding ids they carry can.
"""

from __future__ import annotations

import re
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
SECTION = re.compile(r"^## (?P<title>[^\n]+)\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
ID_GROUP = re.compile(r"KIT-GF-(?P<first>[A-Z0-9]+(?:-[A-Z]+)*)(?P<more>(?:/[0-9]{3})*)")


def finding_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for match in ID_GROUP.finditer(text):
        ids.add(f"KIT-GF-{match.group('first')}")
        ids.update(f"KIT-GF-{number}" for number in match.group("more").split("/") if number)
    return ids


def test_finding_ids_expand_slash_lists() -> None:
    assert finding_ids("(KIT-GF-001/003/016) and KIT-GF-RULE-REGISTRY-BOOTSTRAP") == {
        "KIT-GF-001", "KIT-GF-003", "KIT-GF-016", "KIT-GF-RULE-REGISTRY-BOOTSTRAP"}


def test_unreleased_names_no_finding_that_a_release_already_shipped() -> None:
    sections = {m.group("title"): m.group("body") for m in SECTION.finditer(CHANGELOG.read_text(encoding="utf-8"))}
    unreleased = sections.pop("Unreleased", "")
    released = finding_ids("\n".join(sections.values()))
    stale = []
    for line in unreleased.splitlines():
        if line.startswith("- ") and finding_ids(line) & released:
            stale.append(f"{sorted(finding_ids(line) & released)}: {line[:100]}")

    assert not stale, "remove released entries from Unreleased:\n" + "\n".join(stale)
