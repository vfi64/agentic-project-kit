from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

AUTHORITY = "docs/planning/PROJECT_DIRECTION.yaml"
DIRECTION_DIRS = [Path("docs/plans"), Path("docs/roadmap"), Path("docs/strategy")]


def _direction_docs() -> list[Path]:
    docs: list[Path] = []
    for base in DIRECTION_DIRS:
        if base.exists():
            docs.extend(sorted(base.rglob("*.md")))
    return docs


def test_direction_duplicate_docs_are_marked_superseded() -> None:
    docs = _direction_docs()
    assert docs == []

    for path in docs:
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
        assert "Status: superseded" in head, path.as_posix()
        assert f"Authority: {AUTHORITY}" in head, path.as_posix()


def test_direction_duplicate_docs_registered_as_superseded_or_historical() -> None:
    registry = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text(encoding="utf-8"))
    registered = {
        item["path"]: item
        for item in registry.get("documents", [])
        if isinstance(item, dict) and "path" in item
    }

    assert AUTHORITY in registered
    assert registered[AUTHORITY].get("status") == "active"

    for path in _direction_docs():
        rel = path.as_posix()
        assert rel in registered, rel
        entry = registered[rel]
        assert entry.get("status") == "superseded", rel
        assert entry.get("superseded_by") == AUTHORITY, rel


@pytest.mark.parametrize("path", [
    "docs/planning/MASTER_IMPLEMENTATION_Q.md",
    "docs/archive/KIT_AS_OS_MASTERPLAN.md",
    "docs/archive/COMMAND_SAFETY_HARDENING_PLAN.md",
    "docs/archive/planning/NEXT_TURN_A0_STANDARD_ERROR_ADDITIONS.md",
    "docs/archive/PRE_GUI_HARDENING_TASKS.md",
    "docs/archive/RULE_REGISTRY_IMPROVEMENT_PLAN.md",
    "docs/archive/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md",
    "docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md",
    "docs/archive/TKINTER_WORKBENCH_GUI_PLAN.md",
])
def test_retired_planning_sources_match_registry_lifecycle(path: str) -> None:
    registry = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text())
    entry = next(item for item in registry["documents"] if item["path"] == path)
    text = Path(path).read_text()
    header = text.split("\n## ", 1)[0]

    assert entry["status"] in {"archived", "superseded"}
    assert f"Status: {entry['status']}\n" in header
    assert "\nStatus: active\n" not in header
    successor = next(line.split(": ", 1)[1] for line in header.splitlines()
                     if line.startswith("Superseded-by: "))
    assert Path(successor).is_file()


def test_closed_master_sequence_does_not_remain_current_ordering() -> None:
    direction = yaml.safe_load(Path(AUTHORITY).read_text())
    master = next(item for item in direction["plans"] if item["id"] == "master-implementation-q")
    assert master["status"] == "done"
    assert master["disposition"] == "historical_superseded"
    assert not direction["meta"]["master_sequence"].startswith("Q2 rest:")


def test_paa_import_preserves_review_and_phase_authorization_boundaries() -> None:
    direction = yaml.safe_load(Path(AUTHORITY).read_text())
    plan = next(item for item in direction["plans"]
                if item["id"] == "proof-assurance-assessment")
    assert plan["status"] == "planned"
    assert plan["decision_status"] == "review_required"
    phases = plan["phases"]
    assert [phase["id"] for phase in phases] == [f"P{i}" for i in range(7)]
    assert phases[0]["decision_status"] == "proposed"
    assert all(phase["decision_status"] == "not_authorized" for phase in phases[1:])
    assert sum(plan["candidate_weights_percent"].values()) == 100
    assert sum(plan["tool_weights_percent"].values()) == 100
    assert "no PAA implementation authorized" in plan["authorization"]["integration"]
    assert "Model proof does not prove Python implementation correctness" in plan["claim_boundary"]
    snapshot = Path(plan["source_files"][0])
    text = snapshot.read_text()
    assert "Status: archived" in text
    assert "not operational authorization" in text
    assert f"Source-SHA256: {plan['source_sha256']}" in text
    original = text.split("## Original discussion draft (unaltered)\n\n", 1)[1]
    assert hashlib.sha256(original.encode("utf-8")).hexdigest() == plan["source_sha256"]
    registry = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text())
    entry = next(item for item in registry["documents"] if item["path"] == snapshot.as_posix())
    assert entry["class"] == "historical archive"
