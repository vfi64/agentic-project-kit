from pathlib import Path


def test_agents_stays_within_word_limit_and_points_to_detailed_rules():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert len(text.split()) <= 2700
    assert "docs/governance/PORTABILITY_AND_OPERATIONAL_RULES.md" in text


def test_portability_rule_is_preserved_in_dedicated_rule_document():
    text = Path("docs/governance/PORTABILITY_AND_OPERATIONAL_RULES.md").read_text(encoding="utf-8")
    assert "Portable-first rule" in text
    assert "importable Python core modules" in text
    assert "Shell scripts are compatibility shims only" in text
    assert "must not report PASS when any hard gate" in text
