from __future__ import annotations

from pathlib import Path

from agentic_project_kit.state_freshness import find_stale_state_fragments, format_findings


def test_state_freshness_passes_without_stale_fragments(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "STATUS.md").write_text("Current released version: 0.3.26\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Current version: 0.3.26\n", encoding="utf-8")
    assert find_stale_state_fragments(tmp_path) == []


def test_state_freshness_fails_on_old_current_state_fragment(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "STATUS.md").write_text("Current released version: 0.3.19\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Current version: 0.3.26\n", encoding="utf-8")
    findings = find_stale_state_fragments(tmp_path)
    assert len(findings) == 1
    assert findings[0].path == "docs/STATUS.md"
    assert "0.3.19" in findings[0].fragment


def test_format_findings_reports_failure() -> None:
    message = format_findings([])
    assert message.startswith("PASS")
