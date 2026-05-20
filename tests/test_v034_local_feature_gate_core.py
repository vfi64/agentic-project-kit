from __future__ import annotations

import sys

from agentic_project_kit.local_feature_gate import main, run_local_feature_gate


def test_local_feature_gate_runs_expected_commands(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command, env=None, check=False):
        calls.append(list(command))

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr("agentic_project_kit.local_feature_gate.subprocess.run", fake_run)
    assert run_local_feature_gate(["tests/test_example.py"], include_pr_hygiene=True) == 0

    assert ["git", "branch", "--show-current"] in calls
    assert ["git", "status", "--short"] in calls
    assert [sys.executable, "-m", "pytest", "-q", "tests/test_example.py"] in calls
    assert [sys.executable, "-m", "ruff", "check", "."] in calls
    assert [sys.executable, "-m", "agentic_project_kit.cli", "check-docs"] in calls
    assert [sys.executable, "-m", "agentic_project_kit.cli", "doctor"] in calls
    assert [sys.executable, "-m", "agentic_project_kit.cli", "pr-hygiene"] in calls


def test_local_feature_gate_returns_failure_when_a_command_fails(monkeypatch) -> None:
    def fake_run(command, env=None, check=False):
        class Completed:
            returncode = 1 if "-m" in command and "pytest" in command else 0

        return Completed()

    monkeypatch.setattr("agentic_project_kit.local_feature_gate.subprocess.run", fake_run)
    assert run_local_feature_gate([]) == 1


def test_local_feature_gate_main_parses_pr_hygiene_flag(monkeypatch) -> None:
    observed = {}

    def fake_run(args, *, include_pr_hygiene=False):
        observed["args"] = list(args)
        observed["include_pr_hygiene"] = include_pr_hygiene
        return 0

    monkeypatch.setattr("agentic_project_kit.local_feature_gate.run_local_feature_gate", fake_run)
    assert main(["--include-pr-hygiene", "tests/test_one.py"]) == 0
    assert observed == {"args": ["tests/test_one.py"], "include_pr_hygiene": True}


def test_local_feature_gate_accumulates_multiple_failures(monkeypatch, capsys) -> None:
    failing_modules = {"pytest", "ruff"}
    calls: list[list[str]] = []

    def fake_run(command, env=None, check=False):
        calls.append(list(command))
        command_text = " ".join(command)

        class Completed:
            returncode = 1 if any(name in command_text for name in failing_modules) else 0

        return Completed()

    monkeypatch.setattr("agentic_project_kit.local_feature_gate.subprocess.run", fake_run)
    assert run_local_feature_gate([]) == 1
    assert any("pytest" in " ".join(call) for call in calls)
    assert any("ruff" in " ".join(call) for call in calls)
    assert any("check-docs" in " ".join(call) for call in calls)
    assert "Local feature gate failed." in capsys.readouterr().out


def test_local_feature_gate_uses_src_pythonpath_without_mutating_process_env(monkeypatch) -> None:
    observed_envs = []
    monkeypatch.setenv("PYTHONPATH", "existing")

    def fake_run(command, env=None, check=False):
        if env is not None:
            observed_envs.append(env.get("PYTHONPATH"))

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr("agentic_project_kit.local_feature_gate.subprocess.run", fake_run)
    assert run_local_feature_gate([]) == 0
    assert observed_envs
    assert all(value.startswith("src") for value in observed_envs if value is not None)
    assert "existing" in observed_envs[0]
