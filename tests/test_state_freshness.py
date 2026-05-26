from __future__ import annotations

from pathlib import Path

import yaml

from agentic_project_kit.state_freshness import find_stale_state_fragments, format_findings


def write_handoff_state(tmp_path: Path, *, first_instruction: str, next_action: str | None = None) -> None:
    (tmp_path / ".agentic").mkdir(parents=True)
    data = {
        "release": {"current_version": "0.4.3"},
        "open_items": {"next_expected_chat_action": next_action or "Continue safely."},
        "first_instruction": first_instruction,
    }
    (tmp_path / ".agentic" / "handoff_state.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def test_state_freshness_passes_without_stale_fragments(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "STATUS.md").write_text("Current released version: 0.3.26\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Current version: 0.3.26\n", encoding="utf-8")
    write_handoff_state(tmp_path, first_instruction="Continue with the next safe slice.")
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


def test_state_freshness_fails_when_active_handoff_instruction_references_old_release(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "STATUS.md").write_text("Current release: 0.4.3\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Current release: 0.4.3\n", encoding="utf-8")
    write_handoff_state(
        tmp_path,
        first_instruction="Merge and verify v0.4.2 release metadata, then continue.",
    )

    findings = find_stale_state_fragments(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == ".agentic/handoff_state.yaml:first_instruction"
    assert "stale version 0.4.2" in findings[0].fragment


def test_state_freshness_fails_when_closeout_instruction_points_to_existing_evidence(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    terminal_dir = tmp_path / "docs" / "reports" / "terminal"
    terminal_dir.mkdir(parents=True)
    (terminal_dir / "pr823-merge-finalize.log").write_text("### RESULT: PASS ###\n", encoding="utf-8")
    (tmp_path / "docs" / "STATUS.md").write_text(
        "Immediate next safe step: record PR823 closeout evidence.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Continue safely.\n", encoding="utf-8")
    write_handoff_state(tmp_path, first_instruction="Continue with the next safe slice.")

    findings = find_stale_state_fragments(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == "docs/STATUS.md"
    assert "pr823-merge-finalize.log already exists" in findings[0].fragment


def test_state_freshness_checks_handoff_next_expected_chat_action(tmp_path: Path) -> None:
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    terminal_dir = tmp_path / "docs" / "reports" / "terminal"
    terminal_dir.mkdir(parents=True)
    (terminal_dir / "pr823-merge-finalize.log").write_text("### RESULT: PASS ###\n", encoding="utf-8")
    (tmp_path / "docs" / "STATUS.md").write_text("Continue safely.\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text("Continue safely.\n", encoding="utf-8")
    write_handoff_state(
        tmp_path,
        first_instruction="Continue with the next safe slice.",
        next_action="Record PR823 closeout evidence, then continue.",
    )

    findings = find_stale_state_fragments(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == ".agentic/handoff_state.yaml:open_items.next_expected_chat_action"
    assert "pr823-merge-finalize.log already exists" in findings[0].fragment
