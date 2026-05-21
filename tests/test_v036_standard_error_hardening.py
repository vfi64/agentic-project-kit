from pathlib import Path


def test_ns_dev_include_pr_hygiene_is_not_forwarded_to_pytest():
    text = Path("./ns").read_text(encoding="utf-8")
    assert "--include-pr-hygiene" in text or "dev-local-feature-gate" in text
    assert "agentic_project_kit.local_feature_gate" in text or "tools/ns_dev_local_feature_gate.sh" in text


def test_local_feature_gate_core_owns_pr_hygiene_flag():
    text = Path("src/agentic_project_kit/local_feature_gate.py").read_text(encoding="utf-8")
    assert "--include-pr-hygiene" in text
    assert "raw_args.remove" in text
    assert "include_pr_hygiene=True" in text or "include_pr_hygiene=include_pr_hygiene" in text


def test_terminal_log_contract_is_documented_for_standard_error_hardening():
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    assert "Remote-log evidence is mandatory for standard-error hardening slices" in combined
    assert "FAIL without terminal kill uses NEXT_CHAT_REPLY: f" in combined
    assert "terminal_log=docs/reports/terminal/" in combined
