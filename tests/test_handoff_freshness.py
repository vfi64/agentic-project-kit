from pathlib import Path

from agentic_project_kit.handoff_freshness import (
    assess_handoff_prompt_freshness,
    render_freshness_guard,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_handoff_freshness_guard_reports_stale_successor_prompt(tmp_path: Path) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr690.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for old commit abc6900\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for abc6900\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for abc6900\n")
    data = {
        "safe_state": {"commit": "abc6900"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr690.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="def7010",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)
    assert any("does not mention current handoff commit marker" in warning for warning in warnings)


def test_handoff_freshness_guard_accepts_current_admin_evidence_state(tmp_path: Path) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr704.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for def7040\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for def7040\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for def7040\n")
    data = {
        "safe_state": {"commit": "abc6900"},
        "administrative_evidence_state": {"current_head": "def7040"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr704.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="def7040",
    )

    assert warnings == []


def test_handoff_freshness_guard_accepts_administrative_refresh_commit_after_state_refresh(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr709.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for ef43055\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for ef43055\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for ef43055\n")
    data = {
        "safe_state": {"commit": "ef43055"},
        "administrative_evidence_state": {"current_head": "ef43055"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr709.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc7100",
        current_subject="Refresh handoff state after PR709 (#710)",
    )

    assert warnings == []


def test_handoff_freshness_guard_still_rejects_non_admin_commit_after_state_refresh(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr709.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for ef43055\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for ef43055\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for ef43055\n")
    data = {
        "safe_state": {"commit": "ef43055"},
        "administrative_evidence_state": {"current_head": "ef43055"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr709.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc7110",
        current_subject="Add another registry consumer (#711)",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)
    assert any("does not mention current handoff commit marker" in warning for warning in warnings)


def test_handoff_freshness_guard_uses_yaml_successor_override_when_it_is_latest(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    terminal_dir = tmp_path / "docs" / "reports" / "terminal"
    _write(tmp_path / "docs" / "STATUS.md", "status for e4b2ebe\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for e4b2ebe\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(terminal_dir / "post-pr809-kit-generated-successor-handoff.md", "stale prompt for c07f8ec\n")
    _write(
        terminal_dir / "post-pr809-successor-handoff-override.yaml",
        "successor_chat_handoff:\n  main_after_pr810: e4b2ebe\n",
    )
    data = {"safe_state": {"commit": "e4b2ebe"}}

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="e4b2ebe",
    )

    assert warnings == []


def test_handoff_freshness_guard_renders_prominent_warning() -> None:
    guard = render_freshness_guard(["current git HEAD def7010 is not represented"])

    assert "## Handoff Freshness Guard" in guard
    assert "WARNING" in guard
    assert "successor handoff prompt may be stale" in guard
    assert "docs/STATUS.md" in guard