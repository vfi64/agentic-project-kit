from pathlib import Path
import yaml

def test_handoff_completed_entries_are_informative() -> None:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    entries = data["completed_since_previous_handoff"]
    assert entries
    for entry in entries:
        assert isinstance(entry, str)
        assert len(entry.split()) >= 6, entry
        assert entry != "PR"
        assert entry.startswith("PR #"), entry
