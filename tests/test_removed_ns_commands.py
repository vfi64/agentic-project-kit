from __future__ import annotations

from agentic_project_kit.removed_ns_commands import (
    Hit,
    _count_name,
    _is_probably_text,
    _normalize_command_names,
    _path_in_scope,
)


def test_normalize_command_names_detects_space_and_dash_forms() -> None:
    hits = [
        Hit(ref="x", path="p", line_no=1, line="./ns dev"),
        Hit(ref="x", path="p", line_no=2, line="./ns go up"),
        Hit(ref="x", path="p", line_no=3, line="tools/ns-dev-local-feature-gate.sh"),
        Hit(ref="x", path="p", line_no=4, line="ns-go"),
    ]

    names = _normalize_command_names(hits)

    assert "ns dev" in names
    assert "ns go" in names
    assert "ns go up" in names
    assert "ns-dev-local-feature-gate.sh" not in names
    assert "ns-dev-local-feature-gate" in names
    assert "ns-go" in names


def test_count_name_handles_space_commands() -> None:
    hits = [
        Hit(ref="x", path="p", line_no=1, line="./ns dev"),
        Hit(ref="x", path="p", line_no=2, line="./ns    dev --flag"),
        Hit(ref="x", path="p", line_no=3, line="./ns go up"),
    ]

    assert _count_name(hits, "ns dev") == 2
    assert _count_name(hits, "ns go") == 1


def test_source_scope_excludes_generated_reports_and_transfer_outbox() -> None:
    assert _is_probably_text("ns")
    assert _is_probably_text("tools/ns-dev-local-feature-gate.sh")
    assert _is_probably_text("src/agentic_project_kit/local_feature_gate.py")
    assert _is_probably_text("docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md")

    assert not _is_probably_text("docs/reports/terminal/old.log")
    assert not _is_probably_text("docs/reports/transfer_runs/report.json")
    assert not _is_probably_text(".agentic/transfer/inbox/next_command.py.txt")
    assert not _is_probably_text(".agentic/transfer/outbox/last_result.txt")


def test_path_scope_excludes_transfer_artifacts_directly() -> None:
    assert _path_in_scope("ns")
    assert _path_in_scope("tools/ns-dev-local-feature-gate.sh")
    assert _path_in_scope("docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md")

    assert not _path_in_scope(".agentic/transfer/inbox/current.yaml")
    assert not _path_in_scope(".agentic/transfer/inbox/b11_transfer_report_contract_semantics_apply.py.txt")
    assert not _path_in_scope(".agentic/transfer/outbox/last_result.txt")
    assert not _path_in_scope("docs/reports/terminal/old.log")
