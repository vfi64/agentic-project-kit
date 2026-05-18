from pathlib import Path

from agentic_project_kit.command_inbox_check import check_command_inbox

def write_pair(root: Path, stem: str, yaml_extra: str = "", script: str = "printf ok\\n") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{stem}.yaml").write_text(f"command_id: {stem}\\ntitle: {stem}\\nsafety_class: local-only\\n" + yaml_extra, encoding="utf-8")
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
    (inbox / "orphan.yaml").write_text("command_id: orphan\\n", encoding="utf-8")
    result = check_command_inbox(inbox)
    joined = "\\n".join(result.findings)
    assert not result.ok
    assert "multiple complete pending commands" in joined
    assert "orphan metadata without script" in joined

def test_command_inbox_check_rejects_bad_metadata_and_forbidden_fragments(tmp_path):
    inbox = tmp_path / ".agentic/commands/inbox"
    write_pair(inbox, "bad", script="git switch main\\n")
    (inbox / "bad.yaml").write_text("command_id: bad\\ntitle: Bad\\nsafety_class: invalid\\n", encoding="utf-8")
    result = check_command_inbox(inbox)
    joined = "\\n".join(result.findings)
    assert not result.ok
    assert "unsupported safety_class" in joined
    assert "forbidden fragment: git switch " in joined
