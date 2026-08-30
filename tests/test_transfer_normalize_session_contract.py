from pathlib import Path

from agentic_project_kit.volatile_paths import (
    KNOWN_VOLATILE_TRANSFER_PATHS,
    RULE_ACK_CURRENT_PATH,
    TRANSFER_INBOX_NEXT_COMMAND_PATH,
    TRANSFER_OUTBOX_LAST_RESULT_PATH,
)


def test_normalize_session_defaults_to_no_outbox_write() -> None:
    text = Path("src/agentic_project_kit/cli_commands/transfer_handoff_flow.py").read_text(encoding="utf-8")
    start = text.index("def normalize_session(")
    end = text.index("def _emit_successor_package(")
    section = text[start:end]

    assert "--write-outbox/--no-write-outbox" in section
    assert "write_outbox: bool = typer.Option(\n        False" in section
    assert "if write_outbox:" in section
    assert "payload[\"outbox_written\"] = None" in section
    assert section.count("volatile_repair_result = None") == 1


def test_normalize_session_rule_ack_accepts_rule_ack_sha_prefix() -> None:
    from pathlib import Path

    text = Path("src/agentic_project_kit/cli_commands/transfer_handoff_flow.py").read_text(encoding="utf-8")

    assert 'ack_data.get("repo_head") == head[:7]' not in text
    assert "head.startswith(ack_head)" in text


def test_normalize_session_known_volatile_paths_include_canonical_inbox() -> None:
    from pathlib import Path

    text = Path("src/agentic_project_kit/cli_commands/transfer_context_helpers.py").read_text(
        encoding="utf-8"
    )

    assert "KNOWN_VOLATILE_TRANSFER_PATHS" in text
    assert TRANSFER_INBOX_NEXT_COMMAND_PATH in KNOWN_VOLATILE_TRANSFER_PATHS
    assert TRANSFER_OUTBOX_LAST_RESULT_PATH in KNOWN_VOLATILE_TRANSFER_PATHS
    assert RULE_ACK_CURRENT_PATH in KNOWN_VOLATILE_TRANSFER_PATHS


def test_normalize_session_ignores_current_rule_ack_dirty_state(tmp_path: Path, monkeypatch) -> None:
    import json
    import subprocess

    from typer.testing import CliRunner

    from agentic_project_kit.cli import app

    work = tmp_path / "work"
    work.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=work, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work, check=True)
    (work / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=work, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=work, check=True, capture_output=True, text=True)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=work, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True, text=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    rule_ack = work / RULE_ACK_CURRENT_PATH
    rule_ack.parent.mkdir(parents=True)
    rule_ack.write_text(json.dumps({"repo_head": head[:7]}) + "\n", encoding="utf-8")

    monkeypatch.chdir(work)
    result = CliRunner().invoke(app, ["transfer", "normalize-session", "--json"])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["checks"]["worktree_clean"] is True
    assert payload["rule_ack"]["matches_head"] is True
    assert payload["repo"]["dirty_status"] == ""
    assert set(payload["repo"]["ignored_known_volatile_dirty_status"]) == {
        f"?? {RULE_ACK_CURRENT_PATH}",
        "?? tmp/local-command-stack-state.json",
        "?? tmp/local-gc-last-run-id.txt",
        "?? tmp/local-gc-last.json",
    }
