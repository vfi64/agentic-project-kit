from pathlib import Path

from agentic_project_kit import terminal_logging as tl
from agentic_project_kit.action_registry import SafetyClass, get_action


def test_safe_name_and_log_path_are_deterministic():
    assert tl._safe_name("Dev Gate!") == "Dev_Gate_"
    path = tl.make_log_path("Dev Gate!")
    assert path.parent.as_posix() == "docs/reports/terminal"
    assert path.name.endswith("_Dev_Gate_.log")


def test_latest_pointer_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = Path("docs/reports/terminal/example.log")
    log.parent.mkdir(parents=True)
    log.write_text("x\n", encoding="utf-8")
    tl.write_latest_pointer(log)
    assert tl.read_latest_pointer() == log
    outcome, message = tl.terminal_status()
    assert outcome == "PASS_LOG_READY"
    assert "example.log" in message


def test_terminal_status_without_pointer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outcome, message = tl.terminal_status()
    assert outcome == "PASS_NO_LOG"
    assert "No latest" in message


def test_terminal_status_rejects_missing_pointer_target(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tl.LATEST_POINTER.parent.mkdir(parents=True)
    tl.LATEST_POINTER.write_text("docs/reports/terminal/missing.log\n", encoding="utf-8")
    outcome, message = tl.terminal_status()
    assert outcome == "FAIL_INVALID_POINTER"
    assert "missing.log" in message


def test_terminal_artifact_allowlist():
    assert tl._is_allowed_terminal_artifact("docs/reports/terminal/x.log") is True
    assert tl._is_allowed_terminal_artifact("docs/reports/terminal/LATEST_TERMINAL_LOG.txt") is True
    assert tl._is_allowed_terminal_artifact("src/app.py") is False
    assert tl._is_allowed_terminal_artifact("docs/reports/terminal/x.txt") is False


def test_terminal_actions_are_registered_with_safety_classes():
    assert get_action("run-logged").safety_class is SafetyClass.LOCAL_ONLY
    assert get_action("terminal-status").safety_class is SafetyClass.READ_ONLY
    assert get_action("terminal-upload").safety_class is SafetyClass.REMOTE_MUTATION
