from __future__ import annotations

import copy
import json
from pathlib import Path

from typer import Typer

from agentic_project_kit.command_manifest import (
    JSON_PATH,
    MD_PATH,
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


def test_audit_detects_missing_safety(tmp_path: Path, monkeypatch) -> None:
    data = build_reference_from_app(_fixture_app())
    data["commands"][0].pop("safety")
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    _write_manifest(tmp_path, data)
    monkeypatch.chdir(tmp_path)

    audit = evaluate_command_manifest(tmp_path)

    assert not audit.ok
    assert any(finding.code == "SAFETY_INVALID" for finding in audit.findings)


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
