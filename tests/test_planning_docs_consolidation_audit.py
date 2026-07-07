from __future__ import annotations

from pathlib import Path

from agentic_project_kit.planning_docs_consolidation_audit import (
    audit_planning_docs_consolidation,
    render_planning_docs_consolidation_audit,
)


def test_planning_docs_audit_flags_possible_authoritative_plan(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "PLAN.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Plan\nThis is the source of truth for GUI and handoff.\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is False
    assert result.blockers
    assert result.blockers[0].classification == "possible_authoritative_plan"


def test_planning_docs_audit_classifies_current_handoff_as_authoritative(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Current\nsource of truth\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "authoritative_current_handoff"


def test_planning_docs_audit_classifies_next_chat_bootstrap_as_projection(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# NEXT CHAT BOOTSTRAP\nnext active task\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "handoff_projection"


def test_planning_docs_audit_classifies_project_direction_as_active_anchor(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.yaml"
    doc.parent.mkdir(parents=True)
    doc.write_text("status: active\nauthority: docs/planning/PROJECT_DIRECTION.yaml\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "authoritative_planning_anchor"


def test_planning_docs_audit_classifies_project_direction_view(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Project Direction\nThis view points to PROJECT_DIRECTION.yaml.\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "planning_authority_view"


def test_planning_docs_audit_classifies_pre_gui_tasks_as_scoped_anchor(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "PRE_GUI_HARDENING_TASKS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(
        "# Pre-GUI Hardening Tasks\n"
        "Status: active\n"
        "Authoritative target for pre-GUI hardening planning.\n",
        encoding="utf-8",
    )

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "authoritative_scoped_planning_anchor"


def test_render_planning_docs_audit_reports_blockers(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "PLAN.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Plan\nThis is the source of truth for GUI and handoff.\n", encoding="utf-8")

    rendered = render_planning_docs_consolidation_audit(
        audit_planning_docs_consolidation(tmp_path)
    )

    assert "PLANNING_DOCS_CONSOLIDATION_AUDIT" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER=" in rendered

def test_planning_docs_audit_classifies_workflow_reduction_focus_as_historical(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "WORKFLOW_REDUCTION_FOCUS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Workflow Reduction Focus\nsource of truth for active GUI planning\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "historical_planning_doc"


def test_planning_docs_audit_classifies_known_historical_plan(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "WORKFLOW_REDUCTION_FOCUS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Old\nsource of truth for old handoff workflow\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "historical_planning_doc"


def test_planning_docs_audit_classifies_known_legacy_review_doc(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "POST_MERGE_LIFECYCLE_STATE_MODEL.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Model\nnext handoff work\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "legacy_review_candidate"

def test_planning_docs_audit_classifies_gui_gatekeeper_as_historical_plan(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "GUI_DETERMINISTIC_GATEKEEPER_PLAN.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# GUI\ncurrent source of truth for GUI gatekeeper planning\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "historical_planning_doc"


def test_planning_docs_audit_classifies_next_turn_work_order_as_legacy_review(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning" / "NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Next-Turn\ncurrent source of truth for previous next-turn workflow\n", encoding="utf-8")

    result = audit_planning_docs_consolidation(tmp_path)

    assert result.ok is True
    assert result.records[0].classification == "legacy_review_candidate"
