from pathlib import Path


def test_gc_hardening_documentation_records_pre_gui_baseline() -> None:
    gc = Path("docs/workflow/COMMUNICATION_ARTIFACT_GC.md").read_text(encoding="utf-8")
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Implemented hardening status" in gc
    assert "agentic-kit artifact-gc --tmp-logs" in gc
    assert "agentic-kit artifact-gc --local-tmp-contents" in gc
    assert "local-only" in gc
    assert "agentic-kit artifact-gc --report-retention" in gc
    assert "generated successor-handoff Markdown snapshots" in gc
    assert "Generic Markdown reports" in Path("docs/TEST_GATES.md").read_text(encoding="utf-8")
    assert "PENDING_EXPIRED_TMP_LOGS" in gc
    assert "FAIL_SYMLINK_ARTIFACT" in gc
    assert "Communication artifact GC hardening is now part of the pre-GUI baseline" in status
    assert "Communication artifact GC hardening is now part of the pre-GUI baseline" in handoff


def test_gc_closeout_docs_do_not_render_literal_newline_escapes() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "\\n\\n## Active Workflow Rules" not in status
    assert "\\n\\n## Active Rules For The Next Chat Or Slice" not in handoff
