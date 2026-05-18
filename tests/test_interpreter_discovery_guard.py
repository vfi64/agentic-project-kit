from pathlib import Path
import yaml


def test_handoff_state_records_interpreter_discovery_guard():
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    patterns = data.get("recent_failure_patterns", [])
    match = [item for item in patterns if item.get("id") == "interpreter-discovery-before-python"]
    assert match
    prevention = match[0].get("prevention", "")
    assert ".venv/bin/python" in prevention
    assert "python3" in prevention
    assert "set -e" in prevention
    assert "naked python" in prevention
