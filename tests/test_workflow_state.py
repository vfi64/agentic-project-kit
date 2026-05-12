from pathlib import Path


def test_workflow_state_is_known_value() -> None:
    state = Path(".agentic/workflow_state").read_text(encoding="utf-8").strip()
    assert state in {"IDLE", "TEST", "UPLOAD", "CLEANUP", "REQUESTED", "RUNNING", "UPLOADED", "FAILED"}


def test_workflow_scripts_exist() -> None:
    assert Path("tools/capture_workflow_output.sh").exists()
    assert Path("tools/local_workflow_cycle.sh").exists()
    assert Path("tools/workflow_runner.py").exists()
    assert Path(".agentic/current_work.yaml").exists()


def test_next_step_script_exists() -> None:
    assert Path("tools/next-step.py").exists()


def test_workflow_state_supports_idle_cycle() -> None:
    script = Path("tools/next-step.py").read_text(encoding="utf-8")
    assert "IDLE" in script
    assert "TEST" in script
    assert "UPLOAD" in script
    assert "CLEANUP" in script
    assert "REQUESTED" in script
    assert "RUNNING" in script
    assert "UPLOADED" in script
    assert "FAILED" in script
    assert "No workflow action requested" in script
    assert "Next state: IDLE" in script
    assert "temp/workflow-evidence-" in script


def test_declarative_workflow_runner_uses_allowlist() -> None:
    runner = Path("tools/workflow_runner.py").read_text(encoding="utf-8")
    assert "ALLOWED_SIMPLE_STEPS" in runner
    assert "shell=True" not in runner
    assert "gh_pr_checks" in runner
    assert "gh_pr_view" in runner
    assert "timeout" in runner
