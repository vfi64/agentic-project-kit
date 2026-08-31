from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.checks import check_docs
from agentic_project_kit.cli import app
from agentic_project_kit.documentation_registry import (
    DOCUMENT_CLASSES,
    OPTIONAL_DOCUMENT_FIELDS,
    REGISTRY_PATH,
    SCOPE_PATH,
    REQUIRED_CLASS_RULE_FIELDS,
    append_documentation_registry_entry_text,
    build_doc_registry_scope_decision_rows,
    build_unregistered_document_candidates_report,
    build_documentation_registry_summary,
    check_documentation_registry,
    find_unregistered_document_candidates,
    load_documentation_registry,
    render_doc_registry_scope_decision_table,
    register_documentation_registry_entry,
)
from agentic_project_kit.documentation_system_audit import build_documentation_system_audit

ROOT = Path(__file__).resolve().parents[1]


def _class_rules() -> dict[str, dict[str, str]]:
    return {
        class_name: {field: f"{class_name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS}
        for class_name in DOCUMENT_CLASSES
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    _write(project / "sentinel.yaml", "documents: []\n")
    _write(project / "CHANGELOG.md", "# Changelog\n")
    _write(
        project / "docs/DOCUMENTATION_COVERAGE.yaml",
        "rules:\n"
        "  - id: minimal\n"
        "    documents:\n"
        "      - path: docs/STATUS.md\n"
        "        terms:\n"
        "          - '## Current Goal'\n",
    )
    _write(project / "docs/STATUS.md", "## Current Goal\n\nRegistry test.\n\n## Next Safe Step\n")
    _write(project / "docs/TEST_GATES.md", "## Gate Matrix\n\n## Outcome Reporting\n")
    _write(
        project / "docs/handoff/CURRENT_HANDOFF.md",
        "# Current Handoff\n\n"
        "## Current\n\n"
        ".agentic/compiled_agent_context.yaml\n"
        "FINAL_SUMMARY_CONTRACT.md\n"
        "CHAT_COMMUNICATION_CONTRACT.md\n"
        "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md\n\n"
        "## Next\n",
    )
    _write(
        project / "docs/architecture/ARCHITECTURE_CONTRACT.md",
        "## 1. Executive Summary\n\n"
        "## 2. How to Use This Document\n\n"
        "## 4. Decision Rules\n\n"
        "## 7. Architectural Contract\n\n"
        "## 17. Acceptance Criteria for Future Work\n",
    )
    _write_registry(project)
    return project


def _write_registry(project: Path) -> None:
    registry = {
        "version": 1,
        "class_rules": _class_rules(),
        "documents": [
            {
                "path": "docs/STATUS.md",
                "class": "planning",
                "owner": "maintainers",
            },
            {
                "path": "docs/DOCUMENTATION_REGISTRY.yaml",
                "class": "governance/system",
                "owner": "maintainers",
            }
        ],
    }
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _write_scope(
    project: Path,
    *,
    required_files: list[str] | None = None,
    required_paths: list[str] | None = None,
    exempt_paths: list[dict[str, str]] | None = None,
) -> None:
    scope = {
        "schema_version": 1,
        "required_files": required_files or [],
        "required_paths": required_paths or [],
        "exempt_paths": exempt_paths or [],
    }
    _write(project / SCOPE_PATH, yaml.safe_dump(scope, sort_keys=False))
    registry = _read_registry(project)
    documents = registry["documents"]
    assert isinstance(documents, list)
    if not any(
        isinstance(document, dict) and document.get("path") == SCOPE_PATH.as_posix()
        for document in documents
    ):
        documents.append(
            {
                "path": SCOPE_PATH.as_posix(),
                "class": "governance/system",
                "owner": "maintainers",
            }
        )
        _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _write_scope_decision(project: Path, table: str) -> None:
    _write(
        project / "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md",
        "# Documentation Registry Scope Decision Template\n\n"
        "Status: decided\n"
        "Decision status: decided 2026-07-08\n"
        "Review policy: required\n\n"
        f"{table}\n\n"
        "Notes:\n"
        "- This template is evidence for a maintainer decision.\n",
    )


def _read_registry(project: Path) -> dict[str, object]:
    registry = yaml.safe_load((project / REGISTRY_PATH).read_text(encoding="utf-8"))
    assert isinstance(registry, dict)
    return registry


def _repo_documents() -> dict[str, dict[str, object]]:
    registry = load_documentation_registry(ROOT)
    documents = registry["documents"]
    assert isinstance(documents, list)
    result: dict[str, dict[str, object]] = {}
    for document in documents:
        assert isinstance(document, dict)
        path = document["path"]
        assert isinstance(path, str)
        result[path] = document
    return result


def test_documentation_registry_declares_all_required_classes_and_fields() -> None:
    registry = load_documentation_registry(ROOT)
    assert registry["version"] == 1
    assert set(registry["schema"]["optional_document_fields"]) == set(OPTIONAL_DOCUMENT_FIELDS)
    assert set(registry["class_rules"]) == set(DOCUMENT_CLASSES)
    for class_name in DOCUMENT_CLASSES:
        rules = registry["class_rules"][class_name]
        for field in REQUIRED_CLASS_RULE_FIELDS:
            assert rules[field]


def test_documentation_registry_guard_passes_for_repo_baseline() -> None:
    assert check_documentation_registry(ROOT) == []


def test_documentation_registry_classifies_operational_and_artifact_documents() -> None:
    documents = _repo_documents()
    expected = {
        "docs/WORKFLOW_OUTPUT_CYCLE.md": "operational/automation",
        "docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md": "operational/automation",
        "docs/workflow/COMMUNICATION_ARTIFACT_GC.md": "operational/automation",
        ".agentic/communication_artifacts.yaml": "operational/automation",
        "docs/reports/terminal/LATEST_TERMINAL_LOG.txt": "generated artifact",
    }
    for path, document_class in expected.items():
        assert documents[path]["class"] == document_class


def test_documentation_registry_summary_counts_registered_classes() -> None:
    summary = build_documentation_registry_summary(ROOT)
    class_counts = summary["class_counts"]
    assert isinstance(class_counts, dict)
    assert summary["document_count"] >= 17
    assert class_counts["operational/automation"] >= 4
    assert class_counts["generated artifact"] >= 1
    assert summary["broad_migration_allowed"] is False


def test_check_docs_includes_documentation_registry_guard(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    registry = _read_registry(project)
    documents = registry["documents"]
    assert isinstance(documents, list)
    documents.append(
        {
            "path": "docs/missing-from-registry-test.md",
            "class": "governance/system",
            "owner": "maintainers",
        }
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_docs(project)

    assert (
        f"{REGISTRY_PATH}: registered document does not exist: "
        "docs/missing-from-registry-test.md"
    ) in errors


def test_check_docs_includes_scope_decision_reconcile_guard(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write_scope_decision(
        project,
        "\n".join(
            [
                "| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |",
                "|---|---:|---:|---:|---|",
                "| docs/ | 99 | 0 | 99 | required |",
            ]
        ),
    )

    errors = check_docs(project)

    assert any(
        error.startswith(
            "documentation registry reconcile WARN scope_decision_table_stale: "
            "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md:"
        )
        for error in errors
    )


def test_documentation_registry_guard_reports_duplicate_paths(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    registry = _read_registry(project)
    documents = registry["documents"]
    assert isinstance(documents, list)
    documents.append(dict(documents[0]))
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert f"{REGISTRY_PATH}: duplicate document path 'docs/STATUS.md'" in errors


def test_documentation_registry_guard_reports_missing_class_rule_field(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    registry = _read_registry(project)
    class_rules = registry["class_rules"]
    assert isinstance(class_rules, dict)
    planning_rules = class_rules["planning"]
    assert isinstance(planning_rules, dict)
    del planning_rules["freshness"]
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert f"{REGISTRY_PATH}: 'planning' missing class rule field 'freshness'" in errors


def test_documentation_registry_accepts_optional_lifecycle_fields(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    registry = _read_registry(project)
    documents = registry["documents"]
    assert isinstance(documents, list)
    documents[0]["review_after"] = "release:>=0.4.13"
    documents[0]["deferred_until"] = "2026-12-31"
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    assert check_documentation_registry(project) == []


def _valid_projection_contract(path: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "target_identity": path,
        "primary_document_form": "full",
        "renderer_identifier": "dpa.test.renderer",
        "renderer_interface_version": "1",
        "renderer_semantic_version": "1.0.0",
        "canonical_sources": ["docs/STATUS.md"],
        "configuration": {"mode": "fixture"},
        "target_semantics": "complete-document",
        "target_semantics_version": "1",
        "lifecycle_policy": "dpa-fixture-lifecycle",
        "freshness_policy": "dpa-fixture-freshness",
        "evidence_policy": "dpa-fixture-evidence",
        "fingerprint_algorithm": "sha256",
        "input_domain_version": "1",
        "migration_compatibility_version": "1",
    }


def _valid_partition_contract() -> dict[str, object]:
    return {
        "contract_id": "partition:docs/hybrid.md",
        "schema_version": 1,
        "regions": [
            {"identity": "summary", "owner_class": "manual"},
            {"identity": "projection", "owner_class": "lifecycle"},
        ],
        "boundary_representation": "html-comments",
        "boundary_ownership": "lifecycle",
        "encoding": "utf-8",
        "normalization": "lf",
        "line_endings": "lf",
        "ordering_constraints": "declared-order",
        "malformed_boundary_behavior": "fail-closed",
        "byte_ownership": {"all_bytes_explained": True},
        "partition_fingerprint_algorithm": "sha256",
        "input_domain": "complete-target",
        "compatibility_version": "1",
    }


def _append_document(registry: dict[str, object], entry: dict[str, object]) -> None:
    documents = registry["documents"]
    assert isinstance(documents, list)
    documents.append(entry)


def test_documentation_registry_accepts_dpa_projection_contract(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/projected.md", "# Projected\n")
    registry = _read_registry(project)
    _append_document(
        registry,
        {
            "path": "docs/projected.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": _valid_projection_contract("docs/projected.md"),
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    assert check_documentation_registry(project) == []


def test_documentation_registry_accepts_dpa_partition_and_region_projection(
    tmp_path: Path,
) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/hybrid.md", "# Hybrid\n")
    _write(project / "docs/projection.md", "# Projection\n")
    registry = _read_registry(project)
    _append_document(
        registry,
        {
            "path": "docs/hybrid.md",
            "class": "architecture",
            "owner": "maintainers",
            "partition_contract": _valid_partition_contract(),
        },
    )
    projection = _valid_projection_contract("docs/projection.md")
    projection.update(
        {
            "primary_document_form": "hybrid",
            "target_semantics": "registered-region",
            "parent_document_identity": "docs/hybrid.md",
            "region_identity": "projection",
            "parent_partition_contract_identity": "partition:docs/hybrid.md",
            "projected_payload_target_semantics": "region-payload",
        }
    )
    _append_document(
        registry,
        {
            "path": "docs/projection.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    assert check_documentation_registry(project) == []


def test_documentation_registry_rejects_unknown_dpa_projection_schema(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/projected.md", "# Projected\n")
    registry = _read_registry(project)
    projection = _valid_projection_contract("docs/projected.md")
    projection["schema_version"] = 99
    _append_document(
        registry,
        {
            "path": "docs/projected.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("projection_contract schema_version must be 1" in error for error in errors)


def test_documentation_registry_rejects_unknown_dpa_projection_field(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/projected.md", "# Projected\n")
    registry = _read_registry(project)
    projection = _valid_projection_contract("docs/projected.md")
    projection["surprise"] = "nope"
    _append_document(
        registry,
        {
            "path": "docs/projected.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("projection_contract has unknown field 'surprise'" in error for error in errors)


def test_documentation_registry_rejects_missing_dpa_projection_field(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/projected.md", "# Projected\n")
    registry = _read_registry(project)
    projection = _valid_projection_contract("docs/projected.md")
    del projection["renderer_identifier"]
    _append_document(
        registry,
        {
            "path": "docs/projected.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("projection_contract missing field 'renderer_identifier'" in error for error in errors)


def test_documentation_registry_rejects_dangling_region_reference(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/projection.md", "# Projection\n")
    registry = _read_registry(project)
    projection = _valid_projection_contract("docs/projection.md")
    projection.update(
        {
            "target_semantics": "registered-region",
            "parent_document_identity": "docs/missing-parent.md",
            "region_identity": "projection",
            "parent_partition_contract_identity": "partition:docs/missing-parent.md",
            "projected_payload_target_semantics": "region-payload",
        }
    )
    _append_document(
        registry,
        {
            "path": "docs/projection.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("parent_document_identity is dangling" in error for error in errors)


def test_documentation_registry_rejects_inconsistent_region_reference(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/hybrid.md", "# Hybrid\n")
    _write(project / "docs/projection.md", "# Projection\n")
    registry = _read_registry(project)
    _append_document(
        registry,
        {
            "path": "docs/hybrid.md",
            "class": "architecture",
            "owner": "maintainers",
            "partition_contract": _valid_partition_contract(),
        },
    )
    projection = _valid_projection_contract("docs/projection.md")
    projection.update(
        {
            "target_semantics": "registered-region",
            "parent_document_identity": "docs/hybrid.md",
            "region_identity": "missing-region",
            "parent_partition_contract_identity": "partition:docs/hybrid.md",
            "projected_payload_target_semantics": "region-payload",
        }
    )
    _append_document(
        registry,
        {
            "path": "docs/projection.md",
            "class": "architecture",
            "owner": "maintainers",
            "projection_contract": projection,
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("is not declared by parent partition_contract" in error for error in errors)


def test_documentation_registry_rejects_unsupported_dpa_target_partition_combination(
    tmp_path: Path,
) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/hybrid.md", "# Hybrid\n")
    registry = _read_registry(project)
    _append_document(
        registry,
        {
            "path": "docs/hybrid.md",
            "class": "architecture",
            "owner": "maintainers",
            "partition_contract": _valid_partition_contract(),
            "projection_contract": _valid_projection_contract("docs/hybrid.md"),
        },
    )
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("complete-document projection_contract is inconsistent" in error for error in errors)


def test_documentation_registry_rejects_invalid_optional_lifecycle_fields(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    registry = _read_registry(project)
    documents = registry["documents"]
    assert isinstance(documents, list)
    documents[0]["review_after"] = "after next release"
    documents[0]["deferred_until"] = "31-12-2026"
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))

    errors = check_documentation_registry(project)

    assert any("field 'review_after' must be a non-empty date:, release:, or direction: string" in error for error in errors)
    assert any("field 'deferred_until' must be an ISO date string" in error for error in errors)


def test_docs_registry_cli_reports_summary() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-registry"])
    assert result.exit_code == 0
    assert "Documentation registry summary" in result.output
    assert "operational/automation" in result.output
    assert "broad_migration_allowed: False" in result.output


def test_docs_registry_cli_writes_json_report(tmp_path: Path) -> None:
    report_path = tmp_path / "registry-summary.json"
    runner = CliRunner()
    result = runner.invoke(app, ["docs-registry", "--report", str(report_path)])

    assert result.exit_code == 0
    assert "Documentation registry summary" in result.output
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["registry_path"] == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert payload["broad_migration_allowed"] is False
    assert payload["class_counts"]["operational/automation"] >= 4
    assert payload["owner_counts"]["maintainers"] >= 1
    assert payload["registration_policy"]["status"] == "reviewed_register_command_available"
    assert payload["registration_policy"]["mutation_allowed"] is True
    assert payload["registration_policy"]["allowed_command"] == "agentic-kit doc-registry register"
    assert "unregistered_candidate_count" in payload


def test_documentation_registry_lists_unregistered_candidates_without_mutating(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write(tmp_path / "docs" / "new-plan.md", "# New plan\n")
    _write(tmp_path / "docs" / "reports" / "terminal" / "generated.md", "# Generated\n")

    candidates = find_unregistered_document_candidates(tmp_path)
    summary = build_documentation_registry_summary(tmp_path)

    assert "docs/new-plan.md" in candidates
    assert "docs/reports/terminal/generated.md" not in candidates
    assert "docs/new-plan.md" in summary["unregistered_candidates"]
    assert summary["registration_policy"]["mutation_allowed"] is True


def test_docs_register_adds_entry_for_valid_path_and_class(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/new-plan.md", "# New plan\n")

    result = register_documentation_registry_entry(
        project,
        document_path="docs/new-plan.md",
        document_class="planning",
        owner="maintainers",
    )

    registry = _read_registry(project)
    assert result["result_status"] == "PASS"
    assert result["written"] is True
    assert registry["documents"][-1] == {
        "path": "docs/new-plan.md",
        "class": "planning",
        "owner": "maintainers",
    }
    assert result["scope_decision_update"]["status"] == "SKIP"
    assert check_documentation_registry(project) == []


def test_docs_register_rejects_unknown_class(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/new-plan.md", "# New plan\n")
    before = (project / REGISTRY_PATH).read_text(encoding="utf-8")

    result = register_documentation_registry_entry(
        project,
        document_path="docs/new-plan.md",
        document_class="unknown",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_UNKNOWN_CLASS"
    assert "planning" in result["allowed_classes"]
    assert (project / REGISTRY_PATH).read_text(encoding="utf-8") == before


def test_docs_register_rejects_duplicate_path(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    before = (project / REGISTRY_PATH).read_text(encoding="utf-8")

    result = register_documentation_registry_entry(
        project,
        document_path="docs/STATUS.md",
        document_class="planning",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_DUPLICATE_PATH"
    assert (project / REGISTRY_PATH).read_text(encoding="utf-8") == before


def test_docs_register_rejects_missing_path(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    before = (project / REGISTRY_PATH).read_text(encoding="utf-8")

    result = register_documentation_registry_entry(
        project,
        document_path="docs/missing.md",
        document_class="planning",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_PATH_NOT_FOUND"
    assert (project / REGISTRY_PATH).read_text(encoding="utf-8") == before


def test_docs_register_preserves_existing_entries_and_schema(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/new-plan.md", "# New plan\n")
    before = _read_registry(project)

    register_documentation_registry_entry(
        project,
        document_path="docs/new-plan.md",
        document_class="planning",
    )

    after = _read_registry(project)
    assert after["version"] == before["version"]
    assert after["class_rules"] == before["class_rules"]
    assert after["documents"][:-1] == before["documents"]


def test_docs_register_entry_append_does_not_reserialize_registry_text() -> None:
    before = (
        "version: 1\n"
        "purpose: >-\n"
        "  Keep folded scalar formatting.\n"
        "documents:\n"
        "- path: docs/STATUS.md\n"
        "  class: planning\n"
        "  owner: maintainers\n"
    )

    after = append_documentation_registry_entry_text(
        before,
        path="docs/new-plan.md",
        document_class="planning",
        owner="maintainers",
    )

    assert after.startswith(before)
    assert after.endswith(
        "- path: docs/new-plan.md\n"
        "  class: planning\n"
        "  owner: maintainers\n"
    )

    indented = before.replace("- path:", "  - path:").replace("  class:", "    class:")
    indented = indented.replace("  owner:", "    owner:")
    with_indented_entry = append_documentation_registry_entry_text(
        indented,
        path="docs/other-plan.md",
        document_class="planning",
        owner="maintainers",
    )
    assert with_indented_entry.endswith(
        "  - path: docs/other-plan.md\n"
        "    class: planning\n"
        "    owner: maintainers\n"
    )


def test_docs_register_updates_scope_decision_counts(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/planning/new-plan.md", "# New plan\n")
    _write_scope_decision(
        project,
        "\n".join(
            [
                "| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |",
                "|---|---:|---:|---:|---|",
                "| docs/planning/ | 1 | 0 | 1 | required |",
            ]
        ),
    )

    result = register_documentation_registry_entry(
        project,
        document_path="docs/planning/new-plan.md",
        document_class="planning",
    )

    decision = (
        project / "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md"
    ).read_text(encoding="utf-8")
    assert result["result_status"] == "PASS"
    assert result["scope_decision_update"]["status"] == "PASS"
    assert result["scope_decision_update"]["written"] is True
    assert "| docs/planning/ | 1 | 1 | 0 | required |" in decision


def test_docs_register_fails_closed_on_malformed_scope_decision_table(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/new-plan.md", "# New plan\n")
    _write(
        project / "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md",
        "# Documentation Registry Scope Decision Template\n\n"
        "| docs path | md files | registered | unregistered |\n"
        "|---|---:|---:|---:|\n"
        "| docs/ | 3 | 1 | 2 |\n",
    )
    before = (project / REGISTRY_PATH).read_text(encoding="utf-8")

    result = register_documentation_registry_entry(
        project,
        document_path="docs/new-plan.md",
        document_class="planning",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_SCOPE_DECISION_PROJECTION"
    assert result["written"] is False
    assert (project / REGISTRY_PATH).read_text(encoding="utf-8") == before


def test_docs_check_unregistered_lists_as_warn(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write(tmp_path / "docs" / "new-plan.md", "# New plan\n")

    report = build_unregistered_document_candidates_report(tmp_path)

    assert report["result_status"] == "WARN"
    assert report["candidate_count"] == 1
    assert report["candidates"] == ["docs/new-plan.md"]


def test_scope_file_absent_keeps_current_warn_behavior(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write(tmp_path / "docs" / "new-plan.md", "# New plan\n")

    report = build_unregistered_document_candidates_report(tmp_path)

    assert report["result_status"] == "WARN"
    assert report["scope_present"] is False
    assert report["candidate_count"] == 1
    assert report["candidates"] == ["docs/new-plan.md"]
    assert report["exempted_count"] == 0
    assert report["scope_violation_count"] == 0


def test_required_path_violations_listed_separately(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write_scope(tmp_path, required_paths=["docs/required/"])
    _write(tmp_path / "docs" / "required" / "missing.md", "# Missing\n")
    _write(tmp_path / "docs" / "outside.md", "# Outside\n")

    report = build_unregistered_document_candidates_report(tmp_path)

    assert report["result_status"] == "WARN"
    assert report["candidates"] == ["docs/outside.md", "docs/required/missing.md"]
    assert report["scope_violations"] == ["docs/required/missing.md"]
    assert report["scope_violation_count"] == 1


def test_required_file_violations_do_not_require_parent_path(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write(tmp_path / "docs" / "STATUS.md", "## Current Goal\n")
    _write_scope(tmp_path, required_files=["docs/planning/PROJECT_DIRECTION.yaml"])
    _write(tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.yaml", "schema_version: 1\n")
    _write(tmp_path / "docs" / "planning" / "scratch.md", "# Scratch\n")

    report = build_unregistered_document_candidates_report(tmp_path, strict_scope=True)

    assert report["result_status"] == "FAIL"
    assert report["scope_violations"] == ["docs/planning/PROJECT_DIRECTION.yaml"]
    assert "docs/planning/scratch.md" in report["candidates"]

    register_documentation_registry_entry(
        tmp_path,
        document_path="docs/planning/PROJECT_DIRECTION.yaml",
        document_class="planning",
    )

    clean_report = build_unregistered_document_candidates_report(tmp_path, strict_scope=True)

    assert clean_report["scope_violations"] == []
    assert "docs/planning/scratch.md" in clean_report["candidates"]


def test_strict_scope_fails_on_violation_and_passes_when_clean(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write_scope(tmp_path, required_paths=["docs/required/"])
    _write(tmp_path / "docs" / "required" / "missing.md", "# Missing\n")
    runner = CliRunner()

    failed = runner.invoke(
        app,
        [
            "doc-registry",
            "check-unregistered",
            "--root",
            str(tmp_path),
            "--strict-scope",
            "--json",
        ],
    )

    assert failed.exit_code == 1
    failed_payload = json.loads(failed.output)
    assert failed_payload["result_status"] == "FAIL"
    assert failed_payload["scope_violations"] == ["docs/required/missing.md"]

    clean_project = tmp_path / "clean-project"
    clean_project.mkdir()
    _write_registry(clean_project)
    _write(clean_project / "docs" / "STATUS.md", "## Current Goal\n")
    _write(clean_project / "docs" / "required" / "registered.md", "# Registered\n")
    register_documentation_registry_entry(
        clean_project,
        document_path="docs/required/registered.md",
        document_class="planning",
    )
    _write_scope(clean_project, required_paths=["docs/required/"])

    passed = runner.invoke(
        app,
        [
            "doc-registry",
            "check-unregistered",
            "--root",
            str(clean_project),
            "--strict-scope",
            "--json",
        ],
    )

    assert passed.exit_code == 0
    passed_payload = json.loads(passed.output)
    assert passed_payload["result_status"] == "PASS"
    assert passed_payload["scope_violations"] == []


def test_exempt_paths_filtered_with_counter(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write_scope(
        tmp_path,
        exempt_paths=[
            {
                "path": "docs/examples/",
                "reason": "Example documents are intentionally outside registry scope.",
            }
        ],
    )
    _write(tmp_path / "docs" / "examples" / "sample.md", "# Sample\n")
    _write(tmp_path / "docs" / "active.md", "# Active\n")

    report = build_unregistered_document_candidates_report(tmp_path)

    assert report["result_status"] == "WARN"
    assert report["candidate_count"] == 1
    assert report["candidates"] == ["docs/active.md"]
    assert report["exempted_count"] == 1


def test_decision_template_counts_match_filesystem() -> None:
    rows = {
        str(row["docs_path"]): row
        for row in build_doc_registry_scope_decision_rows(ROOT)
    }
    decision = (ROOT / "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md").read_text(
        encoding="utf-8"
    )

    table_rows = [
        line
        for line in decision.splitlines()
        if line.startswith("| docs/") and not line.startswith("| docs path ")
    ]
    parsed: dict[str, dict[str, int | str]] = {}
    for line in table_rows:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        parsed[cells[0]] = {
            "docs_path": cells[0],
            "md_files": int(cells[1]),
            "registered": int(cells[2]),
            "unregistered": int(cells[3]),
        }

    assert parsed == rows


def test_doc_registry_register_cli_writes_valid_entry(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write(project / "docs/new-plan.md", "# New plan\n")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "doc-registry",
            "register",
            "--root",
            str(project),
            "--path",
            "docs/new-plan.md",
            "--class",
            "planning",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["result_status"] in {"PASS", "WARN"}
    assert _read_registry(project)["documents"][-1]["path"] == "docs/new-plan.md"


def test_doc_registry_check_unregistered_cli_warns_without_failing(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    _write(tmp_path / "docs" / "new-plan.md", "# New plan\n")
    runner = CliRunner()

    result = runner.invoke(app, ["doc-registry", "check-unregistered", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["result_status"] == "WARN"
    assert payload["candidates"] == ["docs/new-plan.md"]


def test_docs_audit_cli_runs_with_documentation_registry() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-audit"])
    assert result.exit_code == 0
    assert "Documentation system audit" in result.output
    assert "Dokumentationsregistry" in result.output
    assert "class:operational/automation" in result.output


def test_documentation_system_audit_includes_registry_dimension() -> None:
    report = build_documentation_system_audit(ROOT)
    dimensions = {dimension.name: dimension for dimension in report.dimensions}

    registry_dimension = dimensions["Dokumentationsregistry"]

    assert registry_dimension.ok
    assert any(finding == "registry=docs/DOCUMENTATION_REGISTRY.yaml" for finding in registry_dimension.findings)
    assert any(finding.startswith("documents=") for finding in registry_dimension.findings)
    assert any(finding.startswith("class:operational/automation=") for finding in registry_dimension.findings)


def test_doc_registry_reconcile_json_reports_clean_state() -> None:
    result = CliRunner().invoke(app, ["doc-registry", "reconcile", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_registry_reconcile_report"
    assert payload["result_status"] in {"PASS", "WARN"}
    assert payload["mode"] == "dry-run"
    assert payload["registry_path"] == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert payload["scope_path"] == "docs/DOC_REGISTRY_SCOPE.yaml"
    assert payload["scope_decision_path"] == "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md"
    assert payload["strict_scope_violation_count"] == 0
    assert isinstance(payload["scope_decision_table_stale"], bool)
    assert payload["rendered_scope_decision_table"].startswith("| docs path | md files |")


def test_doc_registry_reconcile_execute_refreshes_scope_decision_table(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    _write_scope_decision(
        project,
        "\n".join(
            [
                "| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |",
                "|---|---:|---:|---:|---|",
                "| docs/ | 99 | 0 | 99 | required |",
            ]
        ),
    )

    result = CliRunner().invoke(
        app,
        [
            "doc-registry",
            "reconcile",
            "--root",
            str(project),
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    decision = (
        project / "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md"
    ).read_text(encoding="utf-8")
    expected_table = render_doc_registry_scope_decision_table(
        [dict(row) for row in build_doc_registry_scope_decision_rows(project)],
        proposed_by_path={"docs/": "required"},
    )
    assert payload["result_status"] == "PASS"
    assert payload["mode"] == "execute"
    assert payload["scope_decision_table_stale"] is False
    assert payload["scope_decision_update"]["written"] is True
    assert expected_table in decision
