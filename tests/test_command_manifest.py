from __future__ import annotations

import copy
import json
from pathlib import Path

from typer import Typer

from agentic_project_kit.command_manifest import (
    JSON_PATH,
    MD_PATH,
    SURFACE_VALUES,
    build_reference_from_app,
    evaluate_command_manifest,
    manifest_sha,
    render_markdown,
)


def _fixture_app() -> Typer:
    app = Typer()

    @app.command("hello")
    def hello_command() -> None:
        """Say hello."""

    return app


def _write_manifest(root: Path, data: dict[str, object]) -> None:
    path = root / JSON_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / MD_PATH).write_text(render_markdown(data), encoding="utf-8")


def test_manifest_sha_is_stable_for_field_order() -> None:
    commands = [
        {"qualified_name": "agentic-kit beta", "safety": "READ_ONLY"},
        {"safety": "BOUNDED", "qualified_name": "agentic-kit alpha"},
    ]
    reordered = [
        {"safety": "READ_ONLY", "qualified_name": "agentic-kit beta"},
        {"qualified_name": "agentic-kit alpha", "safety": "BOUNDED"},
    ]

    assert manifest_sha(commands) == manifest_sha(reordered)


def test_manifest_sha_changes_when_command_changes() -> None:
    commands = [{"qualified_name": "agentic-kit beta", "safety": "READ_ONLY"}]
    changed = [{"qualified_name": "agentic-kit beta", "safety": "BOUNDED"}]

    assert manifest_sha(commands) != manifest_sha(changed)


def test_fixture_reference_contains_required_manifest_fields() -> None:
    data = build_reference_from_app(_fixture_app())
    command = data["commands"][0]

    assert data["meta"]["manifest_sha"] == manifest_sha(data["commands"])
    assert command["safety"] in {"READ_ONLY", "BOUNDED", "DESTRUCTIVE"}
    assert command["surface"] in SURFACE_VALUES
    assert command["task_tags"]
    assert command["when_to_use"] == "Say hello."
    assert command["replaces_raw"] == []
    assert command["dry_run_available"] is False


def test_selector_commands_are_read_only_in_current_reference() -> None:
    from agentic_project_kit.command_manifest import build_current_reference

    data = build_current_reference()
    by_name = {command["qualified_name"]: command for command in data["commands"]}

    assert by_name["agentic-kit command-for"]["safety"] == "READ_ONLY"
    assert by_name["agentic-kit commands render-md"]["safety"] == "READ_ONLY"


def test_workspace_adopt_is_read_only_in_current_reference() -> None:
    from agentic_project_kit.command_manifest import build_current_reference

    data = build_current_reference()
    by_name = {command["qualified_name"]: command for command in data["commands"]}

    assert by_name["agentic-kit workspace adopt"]["safety"] == "READ_ONLY"


def test_workspace_remove_is_bounded_dry_run_available_in_current_reference() -> None:
    from agentic_project_kit.command_manifest import build_current_reference

    data = build_current_reference()
    by_name = {command["qualified_name"]: command for command in data["commands"]}

    assert by_name["agentic-kit workspace remove"]["safety"] == "BOUNDED"
    assert by_name["agentic-kit workspace remove"]["dry_run_available"] is True
    assert by_name["agentic-kit workspace remove"]["surface"] == "orchestrator"


def test_current_reference_classifies_every_command_surface() -> None:
    from agentic_project_kit.command_manifest import build_current_reference

    data = build_current_reference()
    by_name = {command["qualified_name"]: command for command in data["commands"]}
    surfaces = {name: command.get("surface") for name, command in by_name.items()}

    assert surfaces
    assert all(surface in SURFACE_VALUES for surface in surfaces.values())
    assert surfaces["agentic-kit transfer pr-create-complete"] == "orchestrator"
    assert surfaces["agentic-kit audit-command-manifest"] == "diagnostic"
    assert surfaces["agentic-kit transfer commit"] == "primitive"
    assert surfaces["agentic-kit work start"] == "orchestrator"
    assert surfaces["agentic-kit work finish"] == "orchestrator"
    assert surfaces["agentic-kit docs lifecycle sweep"] == "orchestrator"
    assert surfaces["agentic-kit artifact-gc"] == "orchestrator"
    assert surfaces["agentic-kit chat session-start"] == "orchestrator"
    assert surfaces["agentic-kit evidence commit-paths"] == "primitive"
    assert surfaces["agentic-kit evidence finalize-log"] == "primitive"
    assert surfaces["agentic-kit transfer publish-last-report"] == "primitive"
    assert by_name["agentic-kit handoff post-merge-refresh-status"]["safety"] == "READ_ONLY"
    assert by_name["agentic-kit transfer post-merge-check"]["safety"] == "READ_ONLY"
    assert [
        command["qualified_name"]
        for command in data["commands"]
        if command["safety"] == "DESTRUCTIVE" and command["surface"] == "diagnostic"
    ] == []


def test_surface_contract_documents_compatibility_boundary() -> None:
    contract = Path("docs/governance/COMMAND_REFERENCE_REGISTRY_CONTRACT.md").read_text(
        encoding="utf-8"
    )

    assert SURFACE_VALUES == {"orchestrator", "diagnostic", "primitive"}
    assert "Command surface contract" in contract
    assert "Surface classification is separate from command safety" in contract
    assert "Surface classification is intent-oriented" in contract
    assert "`diagnostic` must not be inferred from `READ_ONLY`" in contract
    assert "does not by itself change the compatibility or deprecation contract" in contract
    assert "primitive does not mean unstable" in contract


def test_audit_detects_missing_safety(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    data["commands"][0].pop("safety")
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "SAFETY_INVALID" for finding in audit.findings)


def test_audit_detects_missing_surface(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    data["commands"][0].pop("surface")
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "SURFACE_INVALID" for finding in audit.findings)


def test_audit_detects_invalid_surface(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    data["commands"][0]["surface"] = "internal"
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "SURFACE_INVALID" for finding in audit.findings)


def test_audit_detects_manifest_sha_mismatch(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    data["meta"]["manifest_sha"] = "not-current"
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "MANIFEST_SHA_MISMATCH" for finding in audit.findings)


def test_audit_detects_markdown_drift(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    _write_manifest(tmp_path, data)
    (tmp_path / MD_PATH).write_text("stale\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "MD_DRIFT" for finding in audit.findings)


def test_audit_detects_replaces_raw_shape(tmp_path: Path, monkeypatch) -> None:
    data = copy.deepcopy(build_reference_from_app(_fixture_app()))
    data["commands"][0]["replaces_raw"] = [""]
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "REPLACES_RAW_INVALID" for finding in audit.findings)
