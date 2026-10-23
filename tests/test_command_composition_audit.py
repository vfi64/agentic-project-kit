"""K0 report boundaries; no new product behavior or live workflow execution."""

from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "k0_audit", ROOT / "scripts/command_composition_audit.py"
)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_closure_handles_cycles_and_missing_nodes():
    assert AUDIT.closure("a", {"a": {"b"}, "b": {"a", "external"}}) == {"a", "b", "external"}


def test_shared_candidates_do_not_invent_command_ownership():
    callbacks = {"first": "cli:first", "second": "cli:second"}
    graph = {
        "cli:first": {"core:shared", "core:one"},
        "cli:second": {"core:shared"},
        "core:shared": {"core:deep"},
        "core:one": {"core:deep"},
    }
    locations = {"core:shared": {"file": "core.py", "line": 2}}
    rows = AUDIT.shared_candidates(callbacks, graph, locations)
    assert [r["function"] for r in rows] == ["core:shared"]
    assert rows[0]["direct_command_callers"] == ["first", "second"]
    assert rows[0]["function_callers"] == ["cli:first", "cli:second"]
    assert "not execution" in rows[0]["uncertainty"]


def test_views_remain_orthogonal_and_preserve_manifest_authority():
    row = {
        "qualified_name": "kit run",
        "surface": "orchestrator",
        "safety": "READ_ONLY",
        "task_tags": ["task"],
        "remote_effects": ["none"],
    }

    def classified(_):
        return SimpleNamespace(as_dict=lambda: {"composition_level": "elementary"})

    result = AUDIT.compare_views([row], classified)
    assert result[0]["surface"] == "orchestrator"
    assert result[0]["composition_level"] == "elementary"
    assert result[0]["safety"] == "READ_ONLY"


def test_website_selection_reports_missing_and_computed_without_execution():
    source = """
_quickstart_commands(catalog, ("known", "missing"))
_quickstart_commands(catalog, compute())
text = "not a command selection"
"""
    rows = AUDIT.website_selections(source, {"known"})
    assert rows[0]["commands"] == ["known", "missing"]
    assert rows[0]["missing"] == ["missing"]
    assert rows[1]["unresolved"] is True


def test_pinned_source_refuses_product_drift(monkeypatch):
    monkeypatch.setattr(
        AUDIT, "checked", lambda argv, _: "src/changed.py" if "diff" in argv else "a" * 40
    )
    with pytest.raises(ValueError, match="differs from pinned commit"):
        AUDIT.generate(ROOT, "HEAD")


def test_current_static_report_is_deterministic_and_complete(monkeypatch):
    # Inspect only: no Kit command callback, suite, simulation or external service runs.
    head = AUDIT.checked(["git", "rev-parse", "HEAD"], ROOT)
    one = AUDIT.generate(ROOT, head)
    original_rglob = Path.rglob

    def reversed_rglob(path, pattern, *args, **kwargs):
        return iter(reversed(list(original_rglob(path, pattern, *args, **kwargs))))

    monkeypatch.setattr(Path, "rglob", reversed_rglob)
    two = AUDIT.generate(ROOT, head)
    assert json.dumps(one, sort_keys=True) == json.dumps(two, sort_keys=True)
    assert one["dynamic_dispatch_sites"] == sorted(
        one["dynamic_dispatch_sites"],
        key=lambda site: (
            site["location"]["file"],
            site["location"]["line"],
            site["expression"],
            site["function"],
        ),
    )
    commands = json.loads((ROOT / "docs/reference/agentic-kit-commands.json").read_text())[
        "commands"
    ]
    assert {r["qualified_name"] for r in one["commands"]} == {c["qualified_name"] for c in commands}
    assert one["counts"]["callbacks"] == len(commands)
    assert all(not r.get("missing") and not r.get("unresolved") for r in one["website_selections"])
    assert all(
        one["execution"][key] == "NOT_RUN" for key in ("test_trace", "simulation", "remote_effects")
    )
    assert one["same_callback_alias_groups"] == [
        ["agentic-kit workflow upload", "agentic-kit workflow upload-output"]
    ]
    assert {t["table"] for t in one["data_driven_tables"]} == {
        "REQUIRED_STANDARD_GATE_COMMANDS",
        "EXTERNAL_STANDARD_GATE_COMMANDS",
    }
    rows = {row["qualified_name"]: row for row in one["commands"]}
    assert set(rows["agentic-kit transfer sync-main"]["direct_callback_argv_candidates"]) == {
        "agentic-kit rules acknowledge",
        "agentic-kit transfer branch-switch",
        "agentic-kit transfer normalize-session",
        "agentic-kit transfer restore-known-volatile",
    }
    required = next(
        table["commands"]
        for table in one["data_driven_tables"]
        if table["table"] == "REQUIRED_STANDARD_GATE_COMMANDS"
    )
    assert set(required) <= set(
        rows["agentic-kit standard-gates-audit-suite"]["potential_command_closure"]
    )
    assert (
        "agentic_project_kit.standard_gates_audit_suite:evaluate_standard_gates_audit_suite"
        in rows["agentic-kit standard-gates-audit-suite"]["direct_callback_callees"]
    )


def test_markdown_projects_current_counts_without_upgrading_static_evidence():
    spec = importlib.util.spec_from_file_location(
        "k0_render", ROOT / "scripts/command_composition_render.py"
    )
    assert spec and spec.loader
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    report = json.loads(
        (ROOT / "docs/reports/command_composition_20261023/composition.json").read_text()
    )
    rendered = renderer.render_report(report)
    assert report["source_commit"] in rendered
    assert "unsuitable for G0 execution diagrams" in rendered
    assert "this audit does not support the designation Microkernel" in rendered
    assert f"**{report['counts']['commands']} manifest entries**" in rendered
    assert f"**{report['counts']['shared_direct_candidates']} shared_core_candidates**" in rendered
    assert "call analysis PARTIAL_STATIC" in rendered
    assert "NOT_RUN / NOT_RUN / NOT_RUN" in rendered


def test_alias_spellings_alone_do_not_create_shared_mechanisms():
    callbacks = {"first": "cli:same", "alias": "cli:same"}
    assert AUDIT.shared_candidates(callbacks, {"cli:same": {"core:one"}}, {}) == []


def test_historical_inventory_diff_uses_names_and_reports_removals():
    before = {
        "base_commit": "old",
        "manifest_sha": "old-sha",
        "commands": [{"command": "kept"}, {"command": "removed"}],
    }
    after = [{"qualified_name": "kept"}, {"qualified_name": "new-z"}, {"qualified_name": "new-a"}]
    report = AUDIT.inventory_diff(after, before)
    assert report["command_count"] == 2
    assert report["added"] == ["new-a", "new-z"]
    assert report["removed"] == ["removed"]
    assert report["source_commit"] == "old"


def test_renderer_changes_when_underlying_facts_change():
    spec = importlib.util.spec_from_file_location(
        "k0_render_mutation", ROOT / "scripts/command_composition_render.py"
    )
    assert spec and spec.loader
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    report = deepcopy(
        json.loads(
            (ROOT / "docs/reports/command_composition_20261023/composition.json").read_text()
        )
    )
    report["historical_inventory"].update(
        command_count=7,
        added=["agentic-kit added-by-test"],
        removed=["agentic-kit removed-by-test"],
    )
    report["commands"] = [
        {
            "qualified_name": "agentic-kit changed-orchestrator",
            "surface": "orchestrator",
            "composition_level": "elementary",
            "reachable_function_count": 1,
            "potential_command_closure": [],
        },
        {
            "qualified_name": "agentic-kit changed-diagnostic",
            "surface": "diagnostic",
            "composition_level": "composite",
        },
    ]
    report["counts"].update(functions=9876, callbacks=313)
    report["execution"].update(callback_mapping_rc=2, legacy_static_rc=3, reconciliation_rc=4)
    rendered = renderer.render_report(report)
    assert "7-entry historical inventory" in rendered
    assert (
        "1 added (`agentic-kit added-by-test`); 1 removed (`agentic-kit removed-by-test`)"
        in rendered
    )
    assert "1 manifest orchestrators are elementary" in rendered
    assert "1 diagnostics are composite: `agentic-kit changed-diagnostic`" in rendered
    assert "agentic-kit changed-orchestrator" in rendered
    assert "completion rc=2; 313 entries" in rendered
    assert "completion rc=3; 9876 functions, 313 callback mappings" in rendered
    assert "completion rc=4" in rendered
    assert "4,230" not in rendered
    assert "map_callbacks.py preflight" not in rendered
    assert "25 manifest orchestrators" not in rendered
