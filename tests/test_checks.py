import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.checks import (
    build_check_context,
    check_changelog_quality,
    check_all,
    check_docs,
    check_document_quality,
    check_documentation_coverage,
    check_state_gate_docs,
    check_todo,
)


def test_check_docs_reports_missing_section(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "## Purpose"
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Title\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    errors = check_docs(tmp_path)

    assert errors
    assert "missing required section" in errors[0]


def test_check_docs_accepts_state_gate_docs_without_sentinel(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    assert check_docs(tmp_path) == []


def test_check_docs_accepts_manifest_workspace_state_without_selfhosting_docs(tmp_path: Path):
    _write_manifest_workspace(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")

    assert check_docs(tmp_path) == []


def test_check_context_reports_manifest_workspace_gate_semantics(tmp_path: Path):
    _write_manifest_workspace(tmp_path)

    context = build_check_context(tmp_path)

    assert context.mode == "external_manifest_workspace"
    assert context.external_manifest_workspace is True
    assert context.gate_family == "workspace_state"
    assert context.check_renders_statuses is False
    assert context.skip_status_renderer == "agentic-kit doctor"
    assert ".agentic/state/status.md" in context.gate_documents


def test_check_docs_json_reports_manifest_workspace_gate_semantics(tmp_path: Path):
    _write_manifest_workspace(tmp_path)

    result = CliRunner().invoke(app, ["check-docs", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["kind"] == "agentic_project_check_result"
    assert payload["command"] == "check-docs"
    assert payload["status"] == "PASS"
    assert payload["context"]["mode"] == "external_manifest_workspace"
    assert payload["context"]["external_manifest_workspace"] is True
    assert payload["context"]["check_renders_statuses"] is False
    assert payload["context"]["skip_status_renderer"] == "agentic-kit doctor"


def test_check_context_option_reports_manifest_workspace_gate_semantics(tmp_path: Path):
    _write_manifest_workspace(tmp_path)

    result = CliRunner().invoke(app, ["check", "--root", str(tmp_path), "--context"])

    assert result.exit_code == 0
    assert "CHECK_CONTEXT" in result.output
    assert "MODE=external_manifest_workspace" in result.output
    assert "EXTERNAL_MANIFEST_WORKSPACE=true" in result.output
    assert "CHECK_RENDERS_STATUSES=false" in result.output
    assert "SKIP_STATUS_RENDERER=agentic-kit doctor" in result.output
    assert "Agentic project check passed" in result.output


def test_check_docs_keeps_selfhosting_gate_when_manifest_is_present(tmp_path: Path):
    _write_manifest_workspace(
        tmp_path,
        path_overrides={"documentation_registry_file": "docs/DOCUMENTATION_REGISTRY.yaml"},
    )
    _write_valid_state_gate_docs(tmp_path)
    _write_documentation_registry(tmp_path)
    (tmp_path / "src/agentic_project_kit").mkdir(parents=True)
    (tmp_path / "docs/reference").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'agentic-project-kit'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")

    assert check_docs(tmp_path) == []


def test_check_all_accepts_manifest_workspace_without_sentinel_todo(tmp_path: Path):
    _write_manifest_workspace(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")

    assert check_all(tmp_path) == []


def test_manifest_workspace_invalid_config_reports_check_errors(tmp_path: Path):
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/config.yaml").write_text("kit_schema_version: [unterminated\n", encoding="utf-8")

    doc_errors = check_docs(tmp_path)
    all_errors = check_all(tmp_path)

    assert any(error.startswith("Invalid workspace manifest: .agentic/config.yaml: invalid YAML") for error in doc_errors)
    assert any(error.startswith("Invalid workspace manifest: .agentic/config.yaml: invalid YAML") for error in all_errors)


def test_check_docs_reports_unresolved_placeholder_markers(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "# Demo"
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n\nTODO: finish this.\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    errors = check_docs(tmp_path)

    assert "README.md: unresolved placeholder marker 'TODO'" in errors


def test_check_docs_accepts_documented_todo_workflow_text(tmp_path: Path):
    errors = check_document_quality("README.md", "# Demo\n\nTODO workflow is documented.\n")

    assert errors == []


def test_check_docs_can_disable_quality_checks_per_document(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "# Demo"
    quality_checks: false
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n\nTODO: accepted fixture text.\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    assert check_docs(tmp_path) == []


def test_check_document_quality_reports_placeholder_markers():
    errors = check_document_quality("README.md", "# Demo\n\nFIXME: later\n")

    assert errors == ["README.md: unresolved placeholder marker 'FIXME'"]


def test_changelog_quality_accepts_recent_substantive_release_entry(tmp_path: Path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v0.4.0 - 2026-05-20\n\n"
        "Zenodo v0.4.0 DOI: 10.5281/zenodo.20348382\n\n"
        "- Hardened terminal safety by scoping Ruff to Python sources and blocking risky generated shell quoting.\n"
        "- Closed the bounded read-only GUI MVP while keeping destructive actions disabled.\n"
        "- Recorded successor handoff evidence and release governance contracts for future chats.\n",
        encoding="utf-8",
    )

    assert check_changelog_quality(tmp_path) == []


def test_changelog_quality_ignores_historical_generic_entries_before_cutoff(tmp_path: Path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v0.3.35 - 2026-05-20\n\n"
        "- Prepare release metadata for v0.3.35.\n",
        encoding="utf-8",
    )

    assert check_changelog_quality(tmp_path) == []


def test_changelog_quality_reports_recent_metadata_only_release_entry(tmp_path: Path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v0.3.36 - 2026-05-21\n\n"
        "Zenodo v0.3.36 DOI: 10.5281/zenodo.20329180\n\n"
        "- Prepare release metadata for v0.3.36.\n",
        encoding="utf-8",
    )

    errors = check_changelog_quality(tmp_path)

    assert "CHANGELOG.md: v0.3.36 has no substantive release bullet beyond generic metadata" in errors
    assert any(error.startswith("CHANGELOG.md: v0.3.36 lacks enough release-quality categories") for error in errors)


def test_changelog_quality_reports_missing_recent_date_and_zenodo_state(tmp_path: Path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v0.4.1\n\n"
        "- Added a tested GUI view-model contract while keeping destructive actions disabled.\n",
        encoding="utf-8",
    )

    errors = check_changelog_quality(tmp_path)

    assert "CHANGELOG.md: v0.4.1 missing release date in heading" in errors
    assert "CHANGELOG.md: v0.4.1 missing Zenodo DOI or pending verification marker" in errors


def test_changelog_quality_is_called_by_check_docs(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## v0.3.36 - 2026-05-21\n\n- Prepare release metadata for v0.3.36.\n",
        encoding="utf-8",
    )
    _write_valid_state_gate_docs(tmp_path)

    errors = check_docs(tmp_path)

    assert "CHANGELOG.md: v0.3.36 missing Zenodo DOI or pending verification marker" in errors


def test_check_todo_accepts_valid_items(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
todo:
  path: .agentic/todo.yaml
''',
        encoding="utf-8",
    )
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/todo.yaml").write_text(
        '''
items:
  - id: BOOT-001
    title: Choose license
    owner: human
    priority: high
    status: open
    evidence_required: LICENSE reviewed
''',
        encoding="utf-8",
    )

    assert check_todo(tmp_path) == []


def test_check_state_gate_docs_accepts_valid_docs(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)

    assert check_state_gate_docs(tmp_path) == []


def test_check_state_gate_docs_reports_missing_file(tmp_path: Path):
    (tmp_path / "docs/handoff").mkdir(parents=True)
    (tmp_path / "docs/STATUS.md").write_text(
        "# Project Status\n\n## Current State\n\n## Current Goal\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/TEST_GATES.md").write_text(
        "# Test Gates\n\n## Gate Matrix\n\n## Outcome Reporting\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        "# Current Handoff\n\n## Current Repository State\n\n## Source of Truth\n\n## Next Safe Step\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert "Missing state gate document: docs/architecture/ARCHITECTURE_CONTRACT.md" in errors
    assert "Missing state gate document: docs/DOCUMENTATION_COVERAGE.yaml" in errors


def test_check_state_gate_docs_reports_missing_architecture_contract_section(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)
    contract_path = tmp_path / "docs/architecture/ARCHITECTURE_CONTRACT.md"
    contract_path.write_text(
        "# Architecture Contract and Roadmap\n\n## 1. Executive Summary\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert (
        "docs/architecture/ARCHITECTURE_CONTRACT.md: missing state gate section "
        "'## 7. Architectural Contract'"
    ) in errors


def test_check_state_gate_docs_reports_stale_handoff_marker(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)
    handoff_path = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    handoff_path.write_text(
        handoff_path.read_text(encoding="utf-8")
        + "\nRun the local gate, inspect the diff, then commit the documentation-state update.\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert errors == [
        "docs/handoff/CURRENT_HANDOFF.md: stale handoff marker "
        "'Run the local gate, inspect the diff, then commit the documentation-state update'"
    ]


def test_check_documentation_coverage_accepts_valid_matrix(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")
    _write_valid_coverage_matrix(tmp_path)

    assert check_documentation_coverage(tmp_path) == []


def test_check_documentation_coverage_reports_missing_term(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    _write_valid_coverage_matrix(tmp_path)

    errors = check_documentation_coverage(tmp_path)

    assert errors == [
        "documentation coverage demo-rule: README.md missing term 'required-term'",
    ]


def test_check_documentation_coverage_reports_missing_matrix(tmp_path: Path):
    errors = check_documentation_coverage(tmp_path)

    assert errors == ["Missing state gate document: docs/DOCUMENTATION_COVERAGE.yaml"]


def _write_valid_state_gate_docs(project_root: Path) -> None:
    (project_root / "docs/handoff").mkdir(parents=True)
    (project_root / "docs/architecture").mkdir(parents=True)
    (project_root / "docs/STATUS.md").write_text(
        "# Project Status\n\n## Current State\n\n## Current Goal\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (project_root / "docs/TEST_GATES.md").write_text(
        "# Test Gates\n\n## Gate Matrix\n\n## Standard Local Gate\n\n## Maintenance Rule\n\n## Outcome Reporting\n",
        encoding="utf-8",
    )
    (project_root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        "# Current Handoff\n\n## Current Repository State\n\n## Source of Truth\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (project_root / "docs/architecture/ARCHITECTURE_CONTRACT.md").write_text(
        "# Architecture Contract and Roadmap\n\n"
        "## 1. Executive Summary\n\n"
        "## 2. How to Use This Document\n\n"
        "## 4. Decision Rules\n\n"
        "## 7. Architectural Contract\n\n"
        "## 17. Acceptance Criteria for Future Work\n",
        encoding="utf-8",
    )
    _write_valid_coverage_matrix(project_root)


def _write_valid_coverage_matrix(project_root: Path) -> None:
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "docs/DOCUMENTATION_COVERAGE.yaml").write_text(
        '''
version: 1
rules:
  - id: demo-rule
    documents:
      - path: README.md
        terms:
          - required-term
''',
        encoding="utf-8",
    )


def _write_manifest_workspace(project_root: Path, *, path_overrides: dict[str, str] | None = None) -> None:
    (project_root / ".agentic/state/handoff").mkdir(parents=True, exist_ok=True)
    (project_root / ".agentic/registries").mkdir(parents=True, exist_ok=True)
    manifest = """
kit_schema_version: 1
project:
  name: external-demo
  type: python
profile: python-default
"""
    if path_overrides:
        manifest += "paths:\n"
        for key, value in path_overrides.items():
            manifest += f"  {key}: {value}\n"
    (project_root / ".agentic/config.yaml").write_text(
        manifest,
        encoding="utf-8",
    )
    (project_root / ".agentic/state/status.md").write_text(
        "# Workspace Status\n\nProject: external-demo\nCurrent state: initialized workspace.\n",
        encoding="utf-8",
    )
    (project_root / ".agentic/state/handoff/README.md").write_text(
        "# Workspace Handoff\n\nValidated handoff packages belong here.\n",
        encoding="utf-8",
    )
    (project_root / ".agentic/registries/documentation.yaml").write_text("version: 1\n", encoding="utf-8")
    (project_root / ".agentic/registries/rules.yaml").write_text("version: 1\n", encoding="utf-8")


def _write_documentation_registry(project_root: Path) -> None:
    import yaml

    from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REQUIRED_CLASS_RULE_FIELDS

    registry = {
        "version": 1,
        "class_rules": {
            class_name: {field: f"{class_name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS}
            for class_name in DOCUMENT_CLASSES
        },
        "documents": [
            {
                "path": "README.md",
                "class": "user-facing description",
                "owner": "maintainers",
            },
            {
                "path": "docs/DOCUMENTATION_REGISTRY.yaml",
                "class": "governance/system",
                "owner": "maintainers",
            },
        ],
    }
    path = project_root / "docs/DOCUMENTATION_REGISTRY.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
