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
