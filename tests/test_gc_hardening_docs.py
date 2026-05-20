from pathlib import Path


def test_gc_hardening_documentation_records_pre_gui_baseline() -> None:
    gc = Path("docs/workflow/COMMUNICATION_ARTIFACT_GC.md").read_text(encoding="utf-8")
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Implemented hardening status" in gc
    assert "./ns artifact-gc --tmp-logs" in gc
    assert "PENDING_EXPIRED_TMP_LOGS" in gc
    assert "FAIL_SYMLINK_ARTIFACT" in gc
    assert "Communication artifact GC hardening is now part of the pre-GUI baseline" in status
    assert "Communication artifact GC hardening is now part of the pre-GUI baseline" in handoff
