from pathlib import Path


def test_workflow_state_is_known_value() -> None:
    state = Path(".agentic/workflow_state").read_text(encoding="utf-8").strip()
    assert state in {"TEST", "UPLOAD"}


def test_workflow_scripts_exist() -> None:
    assert Path("tools/capture_workflow_output.sh").exists()
    assert Path("tools/local_workflow_cycle.sh").exists()
