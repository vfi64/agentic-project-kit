from pathlib import Path

from agentic_project_kit import agent_command_runner as acr
from agentic_project_kit.action_registry import SafetyClass, get_action


def write_command(tmp_path: Path, command_id: str = "cmd-1", script: str | None = None) -> None:
    command_dir = tmp_path / ".agentic" / "commands"
    command_dir.mkdir(parents=True)
    yaml_lines = [
        f"command_id: {command_id}",
        "title: Test command",
        "safety_class: local-only",
        "",
    ]
    (command_dir / "current.yaml").write_text(chr(10).join(yaml_lines), encoding="utf-8")
    if script is None:
        script = "printf ok" + chr(10)
    (command_dir / "current.sh").write_text(script, encoding="utf-8")


def test_load_current_command_missing_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    try:
        acr.load_current_command()
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")


def test_load_current_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path)
    command = acr.load_current_command()
    assert command.command_id == "cmd-1"
    assert command.title == "Test command"
    assert command.safety_class == "local-only"


def test_reject_duplicate_command_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path)
    acr.EXECUTED_JSONL.write_text("{\"command_id\": \"cmd-1\"}" + chr(10), encoding="utf-8")
    outcome, detail = acr.validate_command(acr.load_current_command())
    assert outcome == acr.OUTCOME_FAIL_ALREADY_EXECUTED
    assert detail == "cmd-1"


def test_reject_shell_syntax_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path, script="if broken" + chr(10))
    outcome, detail = acr.validate_command(acr.load_current_command())
    assert outcome == acr.OUTCOME_FAIL_SHELL_SYNTAX
    assert detail


def test_write_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path)
    command = acr.load_current_command()
    report = acr.write_report(command, acr.OUTCOME_PASS_EXECUTED, 0, Path("docs/reports/terminal/x.log"))
    text = report.read_text(encoding="utf-8")
    assert "cmd-1" in text
    assert "PASS_EXECUTED" in text
    assert "x.log" in text


def test_agent_run_is_registered():
    action = get_action("agent-run")
    assert action.safety_class is SafetyClass.REMOTE_MUTATION
    assert "PASS_EXECUTED" in action.outcome_contract


def test_current_branch_falls_back_outside_git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert acr.current_branch() == "unknown"

def test_agent_run_executes_and_records_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path)
    log_path = Path("docs/reports/terminal/cmd-1.log")
    log_path.parent.mkdir(parents=True)
    log_path.write_text("log" + chr(10), encoding="utf-8")
    monkeypatch.setattr(acr.terminal_logging, "run_logged", lambda name, command: 0)
    monkeypatch.setattr(acr.terminal_logging, "read_latest_pointer", lambda: log_path)
    pushed_paths = []
    def fake_stage_commit_push(paths, message):
        pushed_paths.extend(path.as_posix() for path in paths)
        assert "cmd-1" in message
        return 0
    monkeypatch.setattr(acr, "stage_commit_push", fake_stage_commit_push)
    assert acr.agent_run() == 0
    assert acr.EXECUTED_JSONL.exists()
    assert acr.report_path("cmd-1").exists()
    assert "docs/reports/command_runs/cmd-1.md" in pushed_paths
    assert "docs/reports/terminal/cmd-1.log" in pushed_paths


def test_pending_inbox_command_pair_requires_exactly_one_pair(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    inbox = acr.INBOX_DIR
    inbox.mkdir(parents=True)
    (inbox / "a.yaml").write_text("command_id: a" + chr(10), encoding="utf-8")
    (inbox / "a.sh").write_text("printf a" + chr(10), encoding="utf-8")
    assert acr.pending_inbox_command_pair()[0].name == "a.yaml"
    (inbox / "b.yaml").write_text("command_id: b" + chr(10), encoding="utf-8")
    (inbox / "b.sh").write_text("printf b" + chr(10), encoding="utf-8")
    try:
        acr.pending_inbox_command_pair()
    except RuntimeError as exc:
        assert "Multiple pending commands" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_prepare_current_from_inbox_copies_and_removes_pair(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    inbox = acr.INBOX_DIR
    inbox.mkdir(parents=True)
    (inbox / "cmd.yaml").write_text("command_id: cmd" + chr(10), encoding="utf-8")
    (inbox / "cmd.sh").write_text("printf cmd" + chr(10), encoding="utf-8")
    yaml_path, script_path = acr.prepare_current_from_inbox()
    assert acr.CURRENT_YAML.exists()
    assert acr.CURRENT_SCRIPT.exists()
    assert not yaml_path.exists()
    assert not script_path.exists()
    acr.remove_current_files()
    assert not acr.CURRENT_YAML.exists()
    assert not acr.CURRENT_SCRIPT.exists()


def test_agent_next_pulls_prepares_runs_and_cleans_current(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    inbox = acr.INBOX_DIR
    inbox.mkdir(parents=True)
    (inbox / "cmd.yaml").write_text("command_id: cmd" + chr(10) + "title: Cmd" + chr(10) + "safety_class: local-only" + chr(10), encoding="utf-8")
    (inbox / "cmd.sh").write_text("printf cmd" + chr(10), encoding="utf-8")
    monkeypatch.setattr(acr, "git_pull_ff_only", lambda: 0)
    monkeypatch.setattr(acr, "agent_run", lambda extra_upload_paths=None: 0)
    assert acr.agent_next() == 0
    assert not acr.CURRENT_YAML.exists()
    assert not acr.CURRENT_SCRIPT.exists()


def test_agent_next_is_registered():
    action = get_action("agent-next")
    assert action.safety_class is SafetyClass.REMOTE_MUTATION
    assert "FAIL_AMBIGUOUS_COMMANDS" in action.outcome_contract


def test_main_dispatches_next_to_agent_next(monkeypatch):
    called = []
    monkeypatch.setattr(acr, "agent_next", lambda: called.append("next") or 0)
    assert acr.main(["next"]) == 0
    assert called == ["next"]


def test_agent_run_includes_extra_upload_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path, command_id="cmd-extra")
    extra = Path(".agentic/commands/inbox/cmd-extra.yaml")
    log_path = Path("docs/reports/terminal/cmd-extra.log")
    log_path.parent.mkdir(parents=True)
    log_path.write_text("log" + chr(10), encoding="utf-8")
    monkeypatch.setattr(acr.terminal_logging, "run_logged", lambda name, command: 0)
    monkeypatch.setattr(acr.terminal_logging, "read_latest_pointer", lambda: log_path)
    pushed_paths = []
    def fake_stage_commit_push(paths, message):
        pushed_paths.extend(path.as_posix() for path in paths)
        return 0
    monkeypatch.setattr(acr, "stage_commit_push", fake_stage_commit_push)
    assert acr.agent_run(extra_upload_paths=[extra]) == 0
    assert ".agentic/commands/inbox/cmd-extra.yaml" in pushed_paths

def test_agent_next_postconditions_detect_current_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    acr.CURRENT_YAML.parent.mkdir(parents=True)
    acr.CURRENT_YAML.write_text("command_id: stale" + chr(10), encoding="utf-8")
    failures = acr.agent_next_postcondition_failures()
    assert any("current.yaml" in item for item in failures)


def test_agent_next_postconditions_detect_complete_inbox_pair(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    acr.INBOX_DIR.mkdir(parents=True)
    (acr.INBOX_DIR / "left.yaml").write_text("command_id: left" + chr(10), encoding="utf-8")
    (acr.INBOX_DIR / "left.sh").write_text("printf left" + chr(10), encoding="utf-8")
    failures = acr.agent_next_postcondition_failures()
    assert any("complete inbox command remains" in item for item in failures)


def test_agent_next_postcondition_failure_blocks_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    acr.INBOX_DIR.mkdir(parents=True)
    (acr.INBOX_DIR / "cmd.yaml").write_text("command_id: cmd" + chr(10) + "title: Cmd" + chr(10) + "safety_class: local-only" + chr(10), encoding="utf-8")
    (acr.INBOX_DIR / "cmd.sh").write_text("printf cmd" + chr(10), encoding="utf-8")
    monkeypatch.setattr(acr, "git_pull_ff_only", lambda: 0)
    monkeypatch.setattr(acr, "agent_run", lambda extra_upload_paths=None: 0)
    monkeypatch.setattr(acr, "remove_current_files", lambda: None)
    assert acr.agent_next() == 1


def test_write_report_updates_latest_command_run_pointer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path, command_id="cmd-pointer")
    command = acr.load_current_command()
    report = acr.write_report(command, acr.OUTCOME_PASS_EXECUTED, 0, Path("docs/reports/terminal/cmd-pointer.log"))
    assert acr.LATEST_COMMAND_RUN_POINTER.exists()
    assert acr.LATEST_COMMAND_RUN_POINTER.read_text(encoding="utf-8").strip() == report.as_posix()


def test_agent_run_uploads_latest_command_run_pointer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_command(tmp_path, command_id="cmd-upload-pointer")
    log_path = Path("docs/reports/terminal/cmd-upload-pointer.log")
    log_path.parent.mkdir(parents=True)
    log_path.write_text("log\n", encoding="utf-8")
    monkeypatch.setattr(acr.terminal_logging, "run_logged", lambda name, command: 0)
    monkeypatch.setattr(acr.terminal_logging, "read_latest_pointer", lambda: log_path)
    pushed_paths = []
    def fake_stage_commit_push(paths, message):
        pushed_paths.extend(path.as_posix() for path in paths)
        return 0
    monkeypatch.setattr(acr, "stage_commit_push", fake_stage_commit_push)
    assert acr.agent_run() == 0
    assert "docs/reports/command_runs/LATEST_COMMAND_RUN.txt" in pushed_paths
