from pathlib import Path


def text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_quality_rule_is_front_loaded_in_handoff_state_docs():
    doc = text("docs/workflow/HANDOFF_STATE.md")
    early = doc[:1200]
    assert "technically deterministic solution" in early
    assert "quickest workaround" in early
    assert "guards, tests, and documented contracts" in early


def test_recurring_standard_errors_are_recorded_in_handoff_state():
    state = text(".agentic/handoff_state.yaml")
    for item in ["standard-error-guards", "interactive-terminal-exit", "global-cli-or-venv-assumption"]:
        assert item in state


def test_terminal_log_finalization_is_required_before_commit():
    rule = text("docs/workflow/TERMINAL_LOG_HANDOFF_RULE.md")
    assert "tee into a temporary log outside `docs/reports/terminal/`" in rule
    assert "./ns terminal-finalize <tmp-log> <name>" in rule
    assert "Do not commit a repository log file while the current process is still writing to it" in rule


def test_artifact_gc_is_centralized_and_dry_run_first():
    doc = text("docs/workflow/HANDOFF_STATE.md")
    assert ".agentic/communication_artifacts.yaml" in doc
    assert "./ns artifact-gc" in doc
    assert "must not delete arbitrary `docs/reports` files" in doc


def test_interactive_terminal_rule_forbids_shell_termination():
    doc = text("docs/workflow/HANDOFF_STATE.md")
    assert "must never terminate that shell" in doc
    assert "Do not use `exit`, `logout`, `kill`, or top-level `exec`" in doc
    assert "Use exit codes only inside saved scripts executed as child processes" in doc


def test_work_order_standard_local_gates_use_project_local_venv():
    work_order = text(".agentic/work_orders/standard-local-gates.yaml")
    assert ".venv/bin/python" in work_order
    assert ".venv/bin/ruff" in work_order
    assert " agentic-kit " not in work_order


def test_ns_exposes_standard_recovery_shortcuts():
    ns = text("ns")
    for shortcut in ["terminal-finalize", "terminal-clean-check", "artifact-gc", "handoff-check", "handoff-show"]:
        assert shortcut in ns
