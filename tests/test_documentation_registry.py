from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.checks import check_docs
from agentic_project_kit.cli import app
from agentic_project_kit.documentation_registry import (
    DOCUMENT_CLASSES,
    REGISTRY_PATH,
    REQUIRED_CLASS_RULE_FIELDS,
    check_documentation_registry,
    load_documentation_registry,
)

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
            }
        ],
    }
    _write(project / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _read_registry(project: Path) -> dict[str, object]:
    registry = yaml.safe_load((project / REGISTRY_PATH).read_text(encoding="utf-8"))
    assert isinstance(registry, dict)
    return registry


def test_documentation_registry_declares_all_required_classes_and_fields() -> None:
    registry = load_documentation_registry(ROOT)
    assert registry["version"] == 1
    assert set(registry["class_rules"]) == set(DOCUMENT_CLASSES)
    for class_name in DOCUMENT_CLASSES:
        rules = registry["class_rules"][class_name]
        for field in REQUIRED_CLASS_RULE_FIELDS:
            assert rules[field]


def test_documentation_registry_guard_passes_for_repo_baseline() -> None:
    assert check_documentation_registry(ROOT) == []


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


def test_docs_audit_cli_runs_with_documentation_registry() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-audit"])
    assert result.exit_code == 0
    assert "Documentation system audit" in result.output
