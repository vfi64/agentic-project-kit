import importlib.util
from pathlib import Path


def _load_next_step_module():
    module_path = Path("tools/next-step.py")
    spec = importlib.util.spec_from_file_location("next_step_tool", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_idle_with_workflow_file_auto_requests_workflow(monkeypatch, tmp_path: Path) -> None:
    module = _load_next_step_module()
    workflow_file = tmp_path / "current_work.yaml"
    state_file = tmp_path / "workflow_state"
    workflow_file.write_text("name: demo\nsteps:\n  - doctor\n", encoding="utf-8")
    state_file.write_text("IDLE\n", encoding="utf-8")

    called = []
    monkeypatch.setattr(module, "WORKFLOW_FILE", workflow_file)
    monkeypatch.setattr(module, "STATE_FILE", state_file)
    monkeypatch.setattr(module, "step_requested", lambda: called.append("requested"))

    module.step_idle()

    assert state_file.read_text(encoding="utf-8") == "REQUESTED\n"
    assert called == ["requested"]


def test_idle_without_workflow_file_remains_idle(monkeypatch, tmp_path: Path) -> None:
    module = _load_next_step_module()
    workflow_file = tmp_path / "missing-current-work.yaml"
    state_file = tmp_path / "workflow_state"
    state_file.write_text("IDLE\n", encoding="utf-8")

    called = []
    monkeypatch.setattr(module, "WORKFLOW_FILE", workflow_file)
    monkeypatch.setattr(module, "STATE_FILE", state_file)
    monkeypatch.setattr(module, "step_requested", lambda: called.append("requested"))

    module.step_idle()

    assert state_file.read_text(encoding="utf-8") == "IDLE\n"
    assert called == []


def test_ensure_project_environment_creates_venv_when_missing(monkeypatch, tmp_path: Path) -> None:
    module = _load_next_step_module()
    calls = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module.sys, "executable", "python3")
    monkeypatch.setattr(module, "run", lambda args, check=True: calls.append(args))

    module.ensure_project_environment()

    assert calls == [
        ["python3", "-m", "venv", ".venv"],
        [".venv/bin/python", "-m", "pip", "install", "-e", ".[dev]"],
    ]


def test_ensure_project_environment_installs_missing_dev_tools(monkeypatch, tmp_path: Path) -> None:
    module = _load_next_step_module()
    calls = []
    venv_bin = tmp_path / ".venv/bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "run", lambda args, check=True: calls.append(args))

    module.ensure_project_environment()

    assert calls == [[".venv/bin/python", "-m", "pip", "install", "-e", ".[dev]"]]


def test_ensure_project_environment_noops_when_tools_exist(monkeypatch, tmp_path: Path) -> None:
    module = _load_next_step_module()
    calls = []
    venv_bin = tmp_path / ".venv/bin"
    venv_bin.mkdir(parents=True)
    for name in ["python", "ruff", "agentic-kit"]:
        (venv_bin / name).write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "run", lambda args, check=True: calls.append(args))

    module.ensure_project_environment()

    assert calls == []
