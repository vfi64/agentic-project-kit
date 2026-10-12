import subprocess
import sys
from threading import Event, get_ident
from types import SimpleNamespace

import pytest

from agentic_project_kit import gui_services as services
from agentic_project_kit.gui_services import BackgroundOperation, gui_cli_argv, run_gui_command


@pytest.fixture
def discovery(monkeypatch):
    monkeypatch.setattr(services, "load_workspace", lambda *args, **kwargs: SimpleNamespace(kit=SimpleNamespace(interpreter="")))
    result = SimpleNamespace(status="NOT_FOUND", observations=(), cli_argv=())
    monkeypatch.setattr(services, "discover_kit_installation", lambda *args, **kwargs: result)
    return result


def test_owned_interpreter_wins_without_path_lookup(discovery, tmp_path, monkeypatch):
    discovery.status = "FOUND"
    discovery.cli_argv = ("/owned/python", "-m", "agentic_project_kit.cli")
    monkeypatch.setenv("PATH", "")
    assert gui_cli_argv(tmp_path) == discovery.cli_argv


def test_running_gui_python_is_fallback_when_no_owned_installation(discovery, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    assert gui_cli_argv(tmp_path) == (sys.executable, "-m", "agentic_project_kit.cli")


@pytest.mark.parametrize("declared,status", [("/missing/python", "NOT_FOUND"), ("", "BLOCKED")])
def test_explicit_or_broken_installation_never_silently_falls_back(discovery, monkeypatch, tmp_path, declared, status):
    discovery.status = status
    monkeypatch.setattr(services, "load_workspace", lambda *args, **kwargs: SimpleNamespace(kit=SimpleNamespace(interpreter=declared)))
    with pytest.raises(RuntimeError, match="unavailable"):
        gui_cli_argv(tmp_path)


@pytest.mark.parametrize("output,code", [("bad JSON", 65), ("[]", 65), ('{"result_status":"BLOCKED"}', 2), ('{"result_status":"PASS"}', 0)])
def test_json_and_verdict_are_checked_before_success(discovery, monkeypatch, tmp_path, output, code):
    monkeypatch.setattr(services.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, output, ""))
    result = run_gui_command(tmp_path, ("work", "check", "--json"))
    assert result.returncode == code
    assert result.stdout == output


def test_missing_executable_becomes_failure_result(discovery, monkeypatch, tmp_path):
    def missing(*args, **kwargs):
        raise FileNotFoundError("gone")
    monkeypatch.setattr(services.subprocess, "run", missing)
    assert run_gui_command(tmp_path, ("doctor",)).returncode == 127


def test_background_work_is_serial_and_failure_is_consumed_before_retry():
    operation = BackgroundOperation()
    release = Event()
    main_thread = get_ident()
    future = operation.start(lambda: (release.wait(2), get_ident())[1])
    with pytest.raises(RuntimeError, match="already pending"):
        operation.start(lambda: None)
    release.set()
    assert future.result(timeout=2) != main_thread
    with pytest.raises(RuntimeError, match="already pending"):
        operation.start(lambda: None)
    assert operation.consume() != main_thread
    failed = operation.start(lambda: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        failed.result(timeout=2)
    with pytest.raises(ZeroDivisionError):
        operation.consume()
    assert operation.pending is None
    operation.start(lambda: "recovered").result(timeout=2)
    assert operation.consume() == "recovered"


def test_unfinished_background_result_cannot_be_consumed():
    operation = BackgroundOperation()
    release = Event()
    future = operation.start(lambda: release.wait(2))
    with pytest.raises(RuntimeError, match="No completed"):
        operation.consume()
    release.set()
    future.result(timeout=2)
    operation.consume()


def test_basic_dispatch_uses_selected_project_instead_of_process_cwd(monkeypatch, tmp_path):
    from agentic_project_kit import gui_tkinter_shell as shell
    button = SimpleNamespace(command_id="doctor", enabled=True, safety_class="read-only", wrapper_command=("agentic-kit", "doctor"))
    monkeypatch.setattr(shell, "build_gui_gatekeeper_status", lambda root: None)
    monkeypatch.setattr(shell, "build_basic_cockpit_view_model", lambda *args, **kwargs: SimpleNamespace(buttons=(button,)))
    calls = []
    monkeypatch.setattr(shell, "run_gui_command", lambda root, parts: calls.append((root, parts)) or subprocess.CompletedProcess(parts, 0, "selected project checked", ""))
    monkeypatch.setattr(shell, "run_manual_gui_catalog_action", lambda name: pytest.fail("cwd-based runner must not execute"))
    output = shell.run_basic_cockpit_button("doctor", project_root=tmp_path)
    assert calls == [(tmp_path, ("doctor",))]
    assert "selected project checked" in output


@pytest.mark.parametrize("raw,code,expected", [('PASS', 1, 'ERROR'), ('BLOCKED', 0, 'BLOCKED'), ('FAIL', 2, 'FAIL')])
def test_process_failure_takes_precedence_over_pass_claim(raw, code, expected):
    from agentic_project_kit.gui_services import completed_gui_status
    assert completed_gui_status(subprocess.CompletedProcess([], code, '{"result_status":"'+raw+'"}', "")) == expected
