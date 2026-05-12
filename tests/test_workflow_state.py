from pathlib import Path


def test_workflow_state_is_known_value() -> None:
    state = Path(".agentic/workflow_state").read_text(encoding="utf-8").strip()
    assert state in {"TEST", "UPLOAD", "CLEANUP"}


def test_workflow_scripts_exist() -> None:
    assert Path("tools/capture_workflow_output.sh").exists()
    assert Path("tools/local_workflow_cycle.sh").exists()

def test_next_step_script_exists() -> None:
    assert Path("tools/next-step.py").exists()

def test_workflow_state_supports_three_step_cycle() -> None:
    script = Path("tools/next-step.py").read_text(encoding="utf-8")
    assert "TEST" in script
    assert "UPLOAD" in script
    assert "CLEANUP" in script
    assert "temp/workflow-evidence-" in script
