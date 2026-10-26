"""W1-P0 inventories metadata without inventing semantic task authority."""
import importlib.util
import json
from pathlib import Path

import pytest

from agentic_project_kit.command_selector import select_for_task

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task_tag_inventory", ROOT / "scripts/task_tag_inventory.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def command(name, tags, *, group="work", surface="orchestrator", safety="BOUNDED"):
    return {"qualified_name": name, "task_tags": tags, "group": group,
            "surface": surface, "safety": safety, "when_to_use": "Fixture description"}


def test_tags_are_not_semantic_assignments_and_names_do_not_fill_gaps():
    data = AUDIT.inventory({"commands": [command("agentic-kit work deploy", ["work", "bounded"]),
                                       command("agentic-kit work unknown", [])]})
    assert data["counts"]["with_any_tags"] == 1
    assert data["counts"]["with_additional_tag_candidates"] == 0
    assert data["counts"]["unassigned"] == 2
    assert "agentic-kit work deploy" in data["unassigned"]
    assert data["orchestrators"][1]["missing_structural_tags"] == ["bounded", "work"]


def test_explicit_additional_tags_and_producer_overrides_stay_visible():
    data = AUDIT.inventory({"commands": [command("agentic-kit work launch", ["launch"])]})
    row = data["orchestrators"][0]
    assert row["additional_tag_candidates"] == ["launch"]
    assert row["missing_structural_tags"] == ["bounded", "work"]
    assert row["producer_default_matches"] is False
    assert row["assignment"] == "candidate_tags_present"


def test_structural_tags_reuse_nested_group_and_safety_derivation():
    data = AUDIT.inventory({"commands": [command("agentic-kit docs lifecycle sweep",
                         ["docs-lifecycle", "read-only"], group="docs lifecycle", safety="READ_ONLY")]})
    assert data["orchestrators"][0]["structural_tags"] == ["docs-lifecycle", "read-only"]
    assert data["orchestrators"][0]["additional_tag_candidates"] == []


def test_collisions_are_candidates_and_actual_selector_order_is_preserved():
    manifest = {"commands": [command("agentic-kit work first", ["bounded", "work", "shared"]),
                             command("agentic-kit work second", ["bounded", "work", "shared"]),
                             command("agentic-kit status", ["shared"], group="root", surface="diagnostic", safety="READ_ONLY")]}
    data = AUDIT.inventory(manifest)
    row = next(r for r in data["tag_selections"] if r["tag"] == "shared")
    actual = select_for_task(manifest, "shared")
    assert row["selector_matches_all_surfaces"] == [c["qualified_name"] for c in actual.payload["commands"]]
    assert row["semantic_ambiguity"] == "NOT_ASSESSED"
    assert row["multiple_orchestrators"] is True
    assert data["identical_tag_sets"][0]["commands"] == ["agentic-kit work first", "agentic-kit work second"]
    assert data["counts"]["orchestrators"] == 2


@pytest.mark.parametrize("tags", ["work", [""], [None]])
def test_malformed_tags_are_rejected(tags):
    with pytest.raises(ValueError, match="invalid task tags"):
        AUDIT.inventory({"commands": [command("agentic-kit work first", tags)]})


def test_duplicate_command_identity_is_rejected():
    row = command("agentic-kit work first", [])
    with pytest.raises(ValueError, match="identity"):
        AUDIT.inventory({"commands": [row, row]})


def test_inventory_is_stable_under_manifest_order_changes():
    rows = [command("agentic-kit work b", ["work", "bounded"]), command("agentic-kit work a", ["work", "bounded", "task"])]
    assert AUDIT.inventory({"commands": rows}) == AUDIT.inventory({"commands": list(reversed(rows))})


def test_pinned_input_drift_is_refused(monkeypatch):
    monkeypatch.setattr(AUDIT, "git", lambda *args: "a" * 40 if args[1] == "rev-parse" else "changed")
    with pytest.raises(ValueError, match="pinned source"):
        AUDIT.generate(ROOT, "HEAD")


def test_committed_report_renderer_and_input_counts_are_consistent():
    out = ROOT / "docs/reports/task_tag_inventory_20261026"
    data = json.loads((out / "inventory.json").read_text())
    assert AUDIT.render(data) == (out / "README.md").read_text()
    assert data["counts"]["orchestrators"] == len(data["orchestrators"])
    assert data["counts"]["unassigned"] == len(data["unassigned"])
    assert data["historical_baseline"]["counts"]["orchestrators"] == 34
    assert data["historical_baseline"]["counts"]["with_additional_tag_candidates"] == 2
    assert "NOT_ASSESSED" in AUDIT.render(data)
    data["counts"]["orchestrators"] = 999
    assert "| 999 |" in AUDIT.render(data)


def test_current_pinned_inputs_are_reproducible_without_running_workflows():
    a = AUDIT.generate(ROOT, "HEAD")
    b = AUDIT.generate(ROOT, "HEAD")
    assert a == b
    assert a["analysis_status"] == "COMPLETE_METADATA_INVENTORY"
    assert a["semantic_coverage"] == "NOT_ASSESSED"
