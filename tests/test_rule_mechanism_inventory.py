from pathlib import Path
import yaml
INVENTORY = Path(".agentic/rule_mechanism_inventory.yaml")
def test_inventory_is_parseable_and_complete() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert {item["id"] for item in data["mechanisms"]} == {"summary-renderer", "execution-mode-switch"}
def test_inventory_sources_exist_and_keep_terms() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    for mechanism in data["mechanisms"]:
        assert mechanism["status"] == "active"
        assert mechanism["protected_rule_intent"]
        for source in mechanism["sources"]:
            path = Path(source["path"])
            assert path.exists(), source["path"]
            text = path.read_text(encoding="utf-8")
            for term in source["required_terms"]:
                assert term in text, f"{term} missing from {path}"
