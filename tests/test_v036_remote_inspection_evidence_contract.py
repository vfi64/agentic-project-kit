from pathlib import Path


def test_remote_inspection_evidence_rules_exist() -> None:
    text = Path("docs/governance/REMOTE_INSPECTION_EVIDENCE_RULES.md").read_text(encoding="utf-8")
    assert "docs/reports/terminal/tmp-inspection/" in text
    assert "registered for later cleanup" in text
    assert "d` or `done" in text
    assert "REMOTE_EVIDENCE" in text


def test_agents_points_to_remote_inspection_evidence_rules() -> None:
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "docs/governance/REMOTE_INSPECTION_EVIDENCE_RULES.md" in text


def test_status_records_remote_inspection_evidence_contract() -> None:
    text = Path("docs/STATUS.md").read_text(encoding="utf-8")
    assert "remote inspection evidence contract" in text
    assert "registered for later GC" in text
