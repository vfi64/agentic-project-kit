from pathlib import Path


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    next_start = text.find("\n## v", start + len(heading))
    if next_start == -1:
        return text[start:]
    return text[start:next_start]


def test_recent_changelog_entries_record_release_context_not_only_metadata() -> None:
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    expected_terms = {
        "## v0.4.0 - 2026-05-20": [
            "bounded GUI MVP line",
            "terminal safety",
            "successor-handoff state",
            "10.5281/zenodo.20348382",
        ],
        "## v0.3.37 - 2026-05-20": [
            "final GUI-preparation closeout line",
            "status-boundary hardening",
            "Closed the pre-v0.4.0 documentation-state line",
            "10.5281/zenodo.20329450",
        ],
        "## v0.3.36 - 2026-05-21": [
            "documentation boundary",
            "current dashboard",
            "historical regression anchor",
            "10.5281/zenodo.20329180",
        ],
    }
    for heading, terms in expected_terms.items():
        section = _section(text, heading)
        for term in terms:
            assert term in section, f"{heading} missing targeted changelog term: {term}"


def test_recent_changelog_quality_guard_uses_target_terms_not_bullet_totals() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    count_check = "count(" + '"- "' + ")"
    line_total_check = "len(" + "section.splitlines())"
    assert count_check not in test_text
    assert line_total_check not in test_text
