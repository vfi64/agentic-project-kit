from pathlib import Path


def contract_text() -> str:
    return Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")


def test_remote_evidence_pass_cannot_use_terminal_log_none_for_local_mutation() -> None:
    text = contract_text()
    assert "Terminal-log mandate for local mutation blocks" in text
    assert "must not claim `REMOTE_EVIDENCE: PASS` with `terminal_log=NONE`" in text
    assert "non-trivial local mutation block" in text


def test_terminal_log_repo_path_is_required_anchor() -> None:
    text = contract_text()
    assert "terminal_log=docs/reports/terminal/" in text
    assert "chat-only transcript" in text
    assert "not remote evidence" in text


def test_local_mutation_summary_must_downgrade_without_repo_log() -> None:
    text = contract_text()
    assert "mutates files" in text
    assert "creates commits" in text
    assert "opens PRs" in text
    assert "explicitly downgrade evidence" in text
