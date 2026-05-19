from pathlib import Path

from agentic_project_kit import agent_command_runner as acr


def test_agent_run_treats_already_executed_as_idempotent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(acr, "CURRENT_YAML", tmp_path / "current.yaml")
    monkeypatch.setattr(acr, "CURRENT_SCRIPT", tmp_path / "current.sh")
    monkeypatch.setattr(acr, "EXECUTED_JSONL", tmp_path / "executed.jsonl")
    monkeypatch.setattr(acr, "REPORT_DIR", tmp_path / "reports")

    acr.CURRENT_SCRIPT.write_text("#!/usr/bin/env sh\nprintf ok\n", encoding="utf-8")
    acr.CURRENT_YAML.write_text("command_id: cmd\ntitle: Cmd\nsafety_class: local-only\n", encoding="utf-8")
    acr.EXECUTED_JSONL.write_text("{\"command_id\": \"cmd\"}\n", encoding="utf-8")

    assert acr.agent_run() == 0
    report = acr.report_path("cmd")
    assert report.exists()
    assert "FAIL_ALREADY_EXECUTED" in report.read_text(encoding="utf-8")
