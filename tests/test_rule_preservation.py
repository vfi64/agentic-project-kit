from pathlib import Path

import yaml

from agentic_project_kit.rule_preservation import load_rule_registry, validate_rule_preservation

def test_rule_preservation_registry_loads() -> None:
    data = load_rule_registry()
    ids = {rule["id"] for rule in data["rules"]}
    assert "structured-summary-must-be-enforced" in ids
    assert "no-copy-terminal-evidence" in ids

def test_rule_preservation_current_repository_passes() -> None:
    assert validate_rule_preservation() == []

def test_rule_preservation_rejects_missing_required_term(tmp_path: Path) -> None:
    surface = tmp_path / "surface.md"
    surface.write_text("present only", encoding="utf-8")
    registry = tmp_path / "rules.yaml"
    registry.write_text(yaml.safe_dump({"rules": [{"id": "x", "status": "active", "surfaces": [str(surface)], "required_terms": ["missing"]}]}), encoding="utf-8")
    findings = validate_rule_preservation(registry)
    assert findings
    assert findings[0].rule_id == "x"
