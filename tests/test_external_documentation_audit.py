"""KIT-GF-035: real CLI boundaries in disposable adopting workspaces."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report
from agentic_project_kit.documentation_system_audit import build_documentation_system_audit
from agentic_project_kit.release_metadata_authority_gate import evaluate_release_metadata_authority_gate
from agentic_project_kit.release_prepare import prepare_release_state


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    write(tmp_path / ".agentic/config.yaml", "kit_schema_version: 2\nprofile: generic\npublication: none\n"
          "hygiene:\n  doc_lifecycle: warn\nmodules:\n  transfer: false\n")
    write(tmp_path / "pyproject.toml", '[project]\nname = "external-product"\nversion = "0.1.0"\n')
    # Adopting workspaces have this projection too; it never implies self-hosting.
    write(tmp_path / "docs/reference/agentic-kit-commands.json", '{"commands": []}\n')
    write(tmp_path / ".agentic/registries/documentation.yaml", "schema_version: 1\ndocuments: []\n")
    write(tmp_path / "docs/planning/PLAN.md", "# Plan\n\nStatus: active\n\n## Work\n\nReview policy: in body only\n")
    return tmp_path


def audit(root: Path) -> dict:
    result = CliRunner().invoke(app, ["docs-audit", "--root", str(root), "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == (0 if payload["ok"] else 1), result.output
    return payload


def registry(root: Path, documents: list[dict], **extra) -> None:
    write(root / ".agentic/registries/documentation.yaml", yaml.safe_dump(
        {"schema_version": 1, "documents": documents, **extra}))


def test_external_warn_audit_checks_own_documents_without_kit_files(workspace: Path) -> None:
    report = audit(workspace)
    assert report["ok"] and report["scope"] == "external"
    assert len(report["dimensions"]) == 7
    assert any("missing-review-policy" in w for d in report["dimensions"] for w in d["warnings"])
    assert not any(d["findings"] for d in report["dimensions"])
    text = CliRunner().invoke(app, ["docs-audit", "--root", str(workspace)])
    assert text.exit_code == 0 and "Overall: PASS" in text.stdout
    assert "FINAL_SUMMARY_CONTRACT" not in text.stdout


def test_external_lifecycle_warn_is_nonblocking_json(workspace: Path) -> None:
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(workspace), "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0 and payload["ok"]
    assert payload["findings"] and {f["severity"] for f in payload["findings"]} == {"WARN"}


@pytest.mark.parametrize("explicit", [True, False])
def test_strict_lifecycle_still_blocks_missing_headers(workspace: Path, explicit: bool) -> None:
    if not explicit:
        path = workspace / ".agentic/config.yaml"
        path.write_text(path.read_text().replace("doc_lifecycle: warn", "doc_lifecycle: strict"))
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(workspace), "--json",
                                    *(["--strict"] if explicit else [])])
    assert result.exit_code == 1
    assert not json.loads(result.stdout)["ok"]
    if not explicit:
        assert not audit(workspace)["ok"]


def test_off_mode_suppresses_lifecycle_findings(workspace: Path) -> None:
    path = workspace / ".agentic/config.yaml"
    path.write_text(path.read_text().replace("doc_lifecycle: warn", 'doc_lifecycle: "off"'))
    assert build_doc_lifecycle_report(workspace).findings == ()
    assert audit(workspace)["ok"]


def test_declared_required_documents_and_sections_remain_blockers(workspace: Path) -> None:
    write(workspace / "sentinel.yaml", "documents:\n  - path: docs/guide.md\n    required_sections: ['## Usage']\n")
    payload = audit(workspace)
    assert not payload["ok"] and "docs/guide.md" in str(payload)
    write(workspace / "docs/guide.md", "# Guide\n")
    assert not audit(workspace)["ok"]
    write(workspace / "docs/guide.md", "# Guide\n\n## Usage\n")
    assert audit(workspace)["ok"]


@pytest.mark.parametrize("scope_key", ["required_files", "required_paths"])
def test_declared_registry_scope_is_required(workspace: Path, scope_key: str) -> None:
    value = "docs/guide.md" if scope_key == "required_files" else "docs/guides"
    guide = value if scope_key == "required_files" else "docs/guides/guide.md"
    write(workspace / "docs/DOC_REGISTRY_SCOPE.yaml", f"schema_version: 1\n{scope_key}: [{value}]\n")
    assert not audit(workspace)["ok"]
    write(workspace / guide, "# Guide\n")
    payload = audit(workspace)
    assert not payload["ok"] and "unregistered" in str(payload)
    registry(workspace, [{"path": guide, "class": "user-facing description", "owner": "team"}])
    assert audit(workspace)["ok"]


def test_version_mesh_uses_external_package_and_extra_anchors(workspace: Path) -> None:
    manifest = workspace / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text() + "release:\n  version_anchors:\n    - kind: source_constant\n"
                        "      path: app/version.py\n      name: APP_VERSION\n")
    write(workspace / "src/external_product/__init__.py", '__version__ = "0.1.0"\n')
    write(workspace / "app/version.py", 'APP_VERSION = "0.0.9"\n')
    payload = audit(workspace)
    assert not payload["ok"] and "app/version.py" in str(payload)
    write(workspace / "app/version.py", 'APP_VERSION = "0.1.0"\n')
    assert audit(workspace)["ok"]


def test_non_python_workspace_has_no_python_or_kit_document_requirement(workspace: Path) -> None:
    (workspace / "pyproject.toml").unlink()
    assert audit(workspace)["ok"]


def test_registry_uses_declared_classes_and_namespace_lifecycle(workspace: Path) -> None:
    write(workspace / "docs/guide.md", "# Guide\n\nStatus: active\n")
    registry(workspace, [{"path": "docs/guide.md", "class": "product-guide", "owner": "team",
                           "status": "superseded"}], class_rules={"product-guide": {}})
    report = build_doc_lifecycle_report(workspace)
    assert "docs/guide.md" in {d.path for d in report.documents}
    assert any(f.code == "HEADER_REGISTRY_MISMATCH" for f in report.findings)
    assert audit(workspace)["ok"]
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(workspace), "--strict", "--json"])
    assert result.exit_code == 1 and "HEADER_REGISTRY_MISMATCH" in result.stdout
    (workspace / "docs/guide.md").unlink()
    assert not audit(workspace)["ok"]


def test_registry_class_typos_and_duplicates_fail(workspace: Path) -> None:
    write(workspace / "docs/guide.md", "# Guide\n")
    entry = {"path": "docs/guide.md", "class": "plannning", "owner": "team"}
    registry(workspace, [entry, entry])
    payload = audit(workspace)
    assert not payload["ok"]
    assert "undeclared class" in str(payload) and "duplicate registered path" in str(payload)


@pytest.mark.parametrize("managed", [True, False])
def test_declared_canonical_facts_preserve_block_and_review_boundaries(workspace: Path, managed: bool) -> None:
    write(workspace / "docs/guide.md", "# Guide\n")
    registry(workspace, [], canonical_facts=[{"id": "release", "value": "Current product",
             "managed_paths" if managed else "review_paths": ["docs/guide.md"]}])
    payload = audit(workspace)
    assert payload["ok"] is not managed
    assert "canonical fact" in str(payload)


def test_handoff_is_checked_only_with_transfer_and_allows_fresh_state(workspace: Path) -> None:
    manifest = workspace / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text().replace("transfer: false", "transfer: true"))
    assert audit(workspace)["ok"]  # legitimate no-previous-handoff
    write(workspace / ".agentic/state/handoff/handoff_state.yaml", "schema_version: 1\n")
    assert not audit(workspace)["ok"]
    manifest.write_text(manifest.read_text().replace("transfer: true", "transfer: false"))
    assert audit(workspace)["ok"]


def test_partial_successor_package_blocks_when_transfer_is_enabled(workspace: Path) -> None:
    manifest = workspace / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text().replace("transfer: false", "transfer: true"))
    write(workspace / ".agentic/state/handoff/packages/latest/successor_context.yaml", "kind: successor_context\n")
    assert not audit(workspace)["ok"]


@pytest.mark.parametrize("missing", ["successor_context.yaml", "source_manifest.json", "execution_contract.json",
                                      "successor_prompt.md", "validation_report.json"])
def test_stored_pass_cannot_hide_incomplete_package(workspace: Path, missing: str) -> None:
    manifest = workspace / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text().replace("transfer: false", "transfer: true"))
    package = workspace / ".agentic/state/handoff/packages/latest"
    for name in ("successor_context.yaml", "source_manifest.json", "execution_contract.json",
                 "successor_prompt.md", "validation_report.json"):
        if name != missing:
            write(package / name, '{"repo": {"head": "abc", "head_short": "abc"}, "result_status": "PASS"}')
    payload = audit(workspace)
    assert not payload["ok"] and f"missing {missing}" in str(payload)


@pytest.mark.parametrize("bad", ["documents: wrong", "documents: []\nclass_rules: wrong"])
def test_malformed_registry_blocks_with_one_json_result(workspace: Path, bad: str) -> None:
    write(workspace / ".agentic/registries/documentation.yaml", "schema_version: 1\n" + bad)
    assert not audit(workspace)["ok"]


def test_document_paths_cannot_escape_workspace(workspace: Path) -> None:
    write(workspace / "sentinel.yaml", "documents:\n  - path: ../outside.md\n")
    payload = audit(workspace)
    assert not payload["ok"] and "inside the workspace" in str(payload)


@pytest.mark.parametrize("custom_root", [False, True])
def test_release_authority_discovers_workspace_preparation_evidence(workspace: Path, monkeypatch,
                                                                   custom_root: bool) -> None:
    if custom_root:
        manifest = workspace / ".agentic/config.yaml"
        manifest.write_text(manifest.read_text() + "paths:\n  reports_root: local-evidence/reports\n")
    result = prepare_release_state(workspace, version="0.1.1", date="2026-10-09",
                                   summary_lines=["Fix the external product."], dry_run=False)
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(human_workflows, "_changed_paths_against", lambda ref: list(result.changed_paths))
    step = human_workflows._write_release_prepare_report_step(
        version="0.1.1", release_date="2026-10-09", from_tag="", to_ref="main",
        summary_lines_path=workspace / ".agentic/tmp/summary.json", prior_steps=[])
    assert step["ok"]
    evidence = workspace / str(step["stdout"]).strip()
    gate = evaluate_release_metadata_authority_gate(workspace, version="0.1.1", changed_paths=["pyproject.toml"])
    assert gate.ok and evidence.as_posix() in gate.evidence_paths
    stale = evaluate_release_metadata_authority_gate(workspace, version="0.1.2", changed_paths=["pyproject.toml"])
    assert not stale.ok


def test_self_hosted_audit_still_requires_kit_document_set(tmp_path: Path) -> None:
    write(tmp_path / "src/agentic_project_kit/__init__.py", '__version__ = "1.0.21"\n')
    write(tmp_path / "docs/reference/agentic-kit-commands.json", "{}\n")
    write(tmp_path / "pyproject.toml", '[project]\nversion = "1.0.21"\n')
    result = build_documentation_system_audit(tmp_path)
    assert not result.ok and result.scope == "kit"
