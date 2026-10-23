"""Bounded K0c evidence: potential reachability never implies mandatory locking."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "protection_audit", ROOT / "scripts/protection_mechanism_audit.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_shortest_witness_is_deterministic_with_cycles():
    edges = {"root": {"z", "a"}, "z": {"target"}, "a": {"root", "target"}}
    parents = AUDIT.shortest_paths("root", edges)
    assert AUDIT.witness(parents, "target") == ["root", "a", "target"]
    assert AUDIT.witness(parents, "absent") == []


def test_base_entry_is_not_lost_by_counting_only_alias():
    alias, base = AUDIT.MECHANISMS[1], AUDIT.LOCK_BASE
    commands = [
        {"qualified_name": name, "safety": "BOUNDED", "surface": "primitive"}
        for name in ["one", "two"]
    ]
    locations = {name: {"file": "x.py", "line": 1} for name in (*AUDIT.MECHANISMS, base)}
    rows = AUDIT.mechanism_rows(
        commands, {"one": "a", "two": "b"}, {"a": {alias}, alias: {base}, "b": {base}}, locations
    )
    assert rows[alias]["count"] == 1
    assert rows[base]["count"] == 2
    assert rows[base]["safety_counts"] == {"BOUNDED": 2}
    assert rows[base]["reached_by"][1]["witness"] == ["b", base]


def test_test_references_keep_class_ids_and_local_import_scope(tmp_path):
    path = tmp_path / "test_example.py"
    path.write_text("""from module import guard as g
class TestGuard:
    def test_call(self):
        g()
def helper():
    def test_not_collected():
        g()
def test_local():
    from other import guard as local
    local()
def test_unrelated():
    local()
""")
    refs = AUDIT.regression_references(tmp_path, [path.name], ["module:guard", "other:guard"])
    assert [r["node_id"] for r in refs["module:guard"]] == ["test_example.py::TestGuard::test_call"]
    assert [r["node_id"] for r in refs["other:guard"]] == ["test_example.py::test_local"]


def test_consumer_scan_is_bounded_and_refuses_source_drift(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("command_taxonomy command_manifest")

    def git(root, *args):
        return {"rev-parse": "a" * 40, "ls-files": "app.py\ndocs/private.py", "diff": ""}[args[0]]

    monkeypatch.setattr(AUDIT, "git", git)
    result = AUDIT.consumer_check(tmp_path)
    assert result["tracked_source_files_scanned"] == 1
    assert result["dedicated_taxonomy_token_occurrences"]["command_taxonomy"] == 1
    assert result["generic_manifest_reference_files"] == 1
    monkeypatch.setattr(
        AUDIT, "git", lambda root, *args: "app.py" if args[0] == "diff" else git(root, *args)
    )
    with pytest.raises(ValueError, match="tracked changes"):
        AUDIT.consumer_check(tmp_path)


def test_committed_report_witnesses_and_renderer_are_consistent():
    report = json.loads(
        (ROOT / "docs/reports/protection_mechanisms_20261023/reachability.json").read_text()
    )
    for row in [*report["mechanisms"], report["underlying_lock"]]:
        assert row["count"] == len(row["reached_by"])
        assert sum(row["safety_counts"].values()) == row["count"]
        assert all(item["witness"][-1] == row["function"] for item in row["reached_by"])
    assert (
        AUDIT.render_report(report)
        == (ROOT / "docs/reports/protection_mechanisms_20261023/README.md").read_text()
    )
    report["counts"]["non_read_only"] = 999
    assert "Of 999 non-READ_ONLY" in AUDIT.render_report(report)
    assert "Neither denominator nor complement is a count of mutators" in AUDIT.render_report(
        report
    )
