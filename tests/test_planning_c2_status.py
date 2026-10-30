"""Owner-approved planning order and evidence boundaries, 2026-10-30."""
from pathlib import Path

from agentic_project_kit.project_direction import load_project_direction

ROOT = Path(__file__).resolve().parents[1]


def test_owner_order_preserves_blocked_c2_without_blocking_approved_followups():
    data = load_project_direction(ROOT).data
    order = data["meta"]["planning_reconciliation"]["owner_order"]
    assert order["decided"] == "2026-10-30"
    followups = [(x["id"], x.get("step")) for x in order["sequence"] if x["status"] == "planned"]
    assert followups == [
        ("decomplexification-audit-roadmap", "transfer-lifecycle-consolidation"),
        ("mechanize-doc-registry-scope-reconcile", None),
        ("context-budgeted-handoff-projections", None),
        ("lifecycle-backlog-clearance", None),
        ("reports-retention-policy", None),
    ]
    plans = {x["id"]: x for x in data["plans"]}
    retests = plans["external-retest-machine-contracts"]
    assert retests["status"] == "active"
    c2 = next(x for x in retests["steps"] if x["id"] == "c2-external-ledger-resync")
    assert c2["status"] == "blocked"
    assert c2["ledger_reconciliation"]["status"] == "done"
    assert c2["ledger_reconciliation"]["verified_families"] == ["KIT-GF-087", "KIT-GF-088"]
    assert c2["ledger_reconciliation"]["evidence_sha256"] == "c52675701a0df01498210c253274b1e70b570d31da4967e661169088e5020b93"
    assert all(any(fid in text for text in c2["remaining_work"]) for fid in ("003", "009/012", "018", "081", "082"))
    assert order["reordered_20261030"]["gates_preserved"] is True
    assert order["reordered_20261030"]["implementation_authorized_by_queue"] is False
    benchmark = next(x for x in order["sequence"] if x.get("step") == "gate-and-context-benchmark")
    assert benchmark["status"] == "deferred"


def test_website_completion_retains_done_steps_and_release_is_separate():
    data = load_project_direction(ROOT).data
    website = next(x for x in data["plans"] if x["id"] == "website-evidence-and-command-navigation")
    assert website["status"] == "done"
    assert all(x["status"] == "done" for x in website["steps"])
    progress = data["meta"]["planning_reconciliation"]["progress_update_20261030"]
    assert progress["gf091_implementation_pr"] == 2686
    assert progress["gf091_publication_status"] == "unreleased"
    assert progress["release_authorized"] is False
