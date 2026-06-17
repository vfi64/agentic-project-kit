from __future__ import annotations

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def test_dev_local_feature_gate_delegates_to_core(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(args, *, include_pr_hygiene=False):
        observed["args"] = list(args)
        observed["include_pr_hygiene"] = include_pr_hygiene
        return 0

    monkeypatch.setattr("agentic_project_kit.cli_commands.dev.run_local_feature_gate", fake_run)

    result = runner.invoke(app, ["dev", "local-feature-gate", "tests/test_example.py"])

    assert result.exit_code == 0
    assert observed == {"args": ["tests/test_example.py"], "include_pr_hygiene": False}


def test_dev_local_feature_gate_can_include_pr_hygiene(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(args, *, include_pr_hygiene=False):
        observed["args"] = list(args)
        observed["include_pr_hygiene"] = include_pr_hygiene
        return 0

    monkeypatch.setattr("agentic_project_kit.cli_commands.dev.run_local_feature_gate", fake_run)

    result = runner.invoke(app, ["dev", "local-feature-gate", "--include-pr-hygiene", "--", "-k", "smoke"])

    assert result.exit_code == 0
    assert observed == {"args": ["-k", "smoke"], "include_pr_hygiene": True}


def test_dev_local_feature_gate_returns_core_exit_code(monkeypatch) -> None:
    def fake_run(args, *, include_pr_hygiene=False):
        return 1

    monkeypatch.setattr("agentic_project_kit.cli_commands.dev.run_local_feature_gate", fake_run)

    result = runner.invoke(app, ["dev", "local-feature-gate"])

    assert result.exit_code == 1
