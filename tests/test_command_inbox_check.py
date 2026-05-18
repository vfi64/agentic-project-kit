from pathlib import Path

from agentic_project_kit.command_inbox_check import check_command_inbox

def write_pair(root: Path, stem: str, yaml_extra: str = "", script: str = "printf ok" + chr(10)) -> None:
    root.mkdir(parents=True, exist_ok=True)
    metadata = chr(10).join([
        f"command_id: {stem}",
        f"title: {stem}",
        "safety_class: local-only",
    ]) + chr(10) + yaml_extra
    (root / f"{stem}.yaml").write_text(metadata, encoding="utf-8")
    (root / f"{stem}.sh").write_text(script, encoding="utf-8")

def test_command_inbox_check_passes_empty_inbox(tmp_path):
    assert check_command_inbox(tmp_path / ".agentic/commands/inbox").ok

def test_command_inbox_check_passes_one_complete_pair(tmp_path):
    inbox = tmp_path / ".agentic/commands/inbox"
    write_pair(inbox, "cmd")
    assert check_command_inbox(inbox).ok

def test_command_inbox_check_rejects_orphans_and_multiple_pairs(tmp_path):
    inbox = tmp_path / ".agentic/commands/inbox"
    write_pair(inbox, "a")
    write_pair(inbox, "b")
    (inbox / "orphan.yaml").write_text("command_id: orphan" + chr(10), encoding="utf-8")
    result = check_command_inbox(inbox)
    joined = chr(10).join(result.findings)
    assert not result.ok
    assert "multiple complete pending commands" in joined
    assert "orphan metadata without script" in joined

def test_command_inbox_check_rejects_bad_metadata_and_forbidden_fragments(tmp_path):
    inbox = tmp_path / ".agentic/commands/inbox"
    write_pair(inbox, "bad", script="git switch main" + chr(10))
    metadata = chr(10).join(["command_id: bad", "title: Bad", "safety_class: invalid"]) + chr(10)
    (inbox / "bad.yaml").write_text(metadata, encoding="utf-8")
    result = check_command_inbox(inbox)
    joined = chr(10).join(result.findings)
    assert not result.ok
    assert "unsupported safety_class" in joined
    assert "forbidden fragment: git switch " in joined


def test_command_inbox_check_rejects_completed_pending_command(tmp_path, monkeypatch):
    import agentic_project_kit.command_inbox_check as cic
    inbox = tmp_path / ".agentic/commands/inbox"
    write_pair(inbox, "done")
    reports = tmp_path / "docs/reports/command_runs"
    reports.mkdir(parents=True)
    (reports / "done.md").write_text("# done\n", encoding="utf-8")
    monkeypatch.setattr(cic, "REPORT_DIR", reports)
    monkeypatch.setattr(cic, "EXECUTED_JSONL", tmp_path / "executed.jsonl")
    result = cic.check_command_inbox(inbox)
    assert not result.ok
    assert any("completed command still pending: done" in item for item in result.findings)
