from pathlib import Path

from agentic_project_kit import terminal_logging as tl
from agentic_project_kit.action_registry import SafetyClass, get_action


def _write_manifest(root: Path) -> None:
    manifest = root / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )


def test_safe_name_and_log_path_are_deterministic():
    assert tl._safe_name("Dev Gate!") == "Dev_Gate_"
    path = tl.make_log_path("Dev Gate!")
    assert path.parent.as_posix() == "docs/reports/terminal"
    assert path.name.endswith("_Dev_Gate_.log")


def test_log_path_uses_manifest_terminal_namespace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_manifest(tmp_path)

    path = tl.make_log_path("Dev Gate!")

    assert path.parent.as_posix() == ".agentic/state/handoff/terminal"
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

def test_terminal_clean_check_accepts_only_terminal_logs(monkeypatch):
    monkeypatch.setattr(tl, "git_dirty_paths", lambda: ["docs/reports/terminal/x.log", "docs/reports/terminal/LATEST_TERMINAL_LOG.txt"])
    outcome, message = tl.terminal_clean_check()
    assert outcome == "PASS_ONLY_TERMINAL_LOG_DIRTY"
    assert "x.log" in message


def test_terminal_clean_check_rejects_non_log_dirty_files(monkeypatch):
    monkeypatch.setattr(tl, "git_dirty_paths", lambda: ["src/agentic_project_kit/terminal_logging.py"])
    outcome, message = tl.terminal_clean_check()
    assert outcome == "FAIL_DIRTY_NON_LOG_FILES"
    assert "terminal_logging.py" in message


def test_terminal_clean_check_is_registered():
    action = get_action("terminal-clean-check")
    assert action.safety_class is SafetyClass.READ_ONLY
    assert "PASS_ONLY_TERMINAL_LOG_DIRTY" in action.outcome_contract



def test_finalize_terminal_log_copies_tmp_log_to_terminal_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "run.log"
    source.write_text("hello\n### RESULT: PASS ###\n", encoding="utf-8")
    outcome, message = tl.finalize_terminal_log(source, "Final Run")
    assert outcome == "PASS_FINALIZED"
    target = Path(message)
    assert target.parent == tl.TERMINAL_DIR
    assert target.read_text(encoding="utf-8") == "hello\n### RESULT: PASS ###\n"
    assert tl.read_latest_pointer() == target


def test_finalize_terminal_log_rejects_terminal_dir_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tl.TERMINAL_DIR / "active.log"
    source.parent.mkdir(parents=True)
    source.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    outcome, message = tl.finalize_terminal_log(source, "bad")
    assert outcome == "FAIL_SOURCE_INSIDE_TERMINAL_DIR"
    assert "active.log" in message


def test_finalize_terminal_log_requires_result_marker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "run.log"
    source.write_text("no marker\n", encoding="utf-8")
    outcome, message = tl.finalize_terminal_log(source, "missing-marker")
    assert outcome == "FAIL_MISSING_RESULT_MARKER"
    assert "run.log" in message


def test_terminal_log_finalize_contract_words_are_stable():
    text = Path(".agentic/no_copy_terminal_policy.yaml").read_text(encoding="utf-8")
    assert "finalize terminal evidence" in text
    assert "committed and pushed repo artifacts" in text

def test_terminal_upload_refuses_main_branch(monkeypatch):
    monkeypatch.setattr(tl, "_current_branch", lambda: "main")
    assert tl.upload_terminal_output() == 1


def test_terminal_upload_accepts_required_feature_branch_without_ready_log(monkeypatch):
    monkeypatch.setattr(tl, "_current_branch", lambda: "feature/demo")
    monkeypatch.setattr(tl, "terminal_status", lambda: ("FAIL_INVALID_POINTER", "missing"))
    assert tl.upload_terminal_output(required_branch="feature/demo") == 1
