from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import (
    is_administrative_evidence_subject,
    refresh_handoff_safe_state,
    validate_handoff_state,
)


def _base_state():
    return {
        "schema_version": 1,
        "updated": {"date": "2026-05-22"},
        "repo": {"local_path": "/repo", "remote": "github.com/example/repo", "default_branch": "main"},
        "safe_state": {"branch": "main", "commit": "adc65ac", "commit_subject": "Close out GUI MVP three read-only actions (#656)", "semantics": "last_substantive_work_state", "working_tree_expected_clean": True},
        "release": {"current_version": "0.3.37", "previous_version": "0.3.36", "tag": "v0.3.37"},
        "open_items": {"prs": []},
        "completed_since_previous_handoff": ["baseline"],
        "current_capabilities": {"handoff": "available"},
        "rules": [{"id": "test-rule", "status": "active", "text": "test rule"}],
        "recent_failure_patterns": [{"id": "test-pattern", "prevention": "test prevention"}],
        "next_allowed_tasks": ["continue safely"],
        "blocked_until_closeout": [],
        "first_instruction": "continue safely",
        "handoff_maintenance": {"status": "active"},
    }


def test_administrative_evidence_subjects_are_recognized():
    assert is_administrative_evidence_subject("Record final post-PR656 handoff consistency log")
    assert is_administrative_evidence_subject("Recover post-PR656 handoff prompt")
    assert is_administrative_evidence_subject("Refresh post-PR974 bootstrap handoff state")
    assert is_administrative_evidence_subject("Refresh post-PR974 bootstrap handoff state (#975)")
    assert is_administrative_evidence_subject("Refresh post-PR974 administrative handoff state")
    assert is_administrative_evidence_subject("Refresh operational handoff after PR1245 (#1246)")
    assert not is_administrative_evidence_subject("Enable check-docs as read-only GUI action (#655)")
    assert not is_administrative_evidence_subject("Refresh post-PR974 product workflow state")


def test_administrative_evidence_head_does_not_move_substantive_safe_state():
    state = refresh_handoff_safe_state(_base_state(), "deadbee", "Record final post-PR656 handoff consistency log")
    assert state["safe_state"]["commit"] == "adc65ac"
    assert state["safe_state"]["semantics"] == "last_substantive_work_state"
    assert state["administrative_evidence_state"]["current_head"] == "deadbee"
    assert validate_handoff_state(state) == []
    prompt = render_handoff_prompt(state)
    assert "## 2a. Administrative Evidence State" in prompt
    assert "Commit: `adc65ac`" in prompt
    assert "Current HEAD at generation time: `deadbee`" in prompt


def test_substantive_head_moves_safe_state_and_clears_admin_state():
    state = _base_state()
    state["administrative_evidence_state"] = {"current_head": "old"}
    refreshed = refresh_handoff_safe_state(state, "c0ffee1", "Enable next GUI action (#999)")
    assert refreshed["safe_state"]["commit"] == "c0ffee1"
    assert "administrative_evidence_state" not in refreshed
