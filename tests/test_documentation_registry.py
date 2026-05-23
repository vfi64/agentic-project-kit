from __future__ import annotations

from pathlib import Path
import shutil

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


def _copy_repo_subset(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for relative in (
        "README.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "sentinel.yaml",
        "docs/DOCUMENTATION_COVERAGE.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml",
        "docs/STATUS.md",
        "docs/TEST_GATES.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/architecture/ARCHITECTURE_CONTRACT.md",
        "docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md",
        "docs/releases/VERIFIED_RELEASES.md",
        "docs/reports/terminal/v041-final-main-verify-after-pr689.log",
        "docs/reports/terminal/v041-handoff-after-pr690.log",
    ):
        source = ROOT / relative
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return project


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
    project = _copy_repo_subset(tmp_path)
    registry_path = project / REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["documents"].append(
        {
            "path": "docs/missing-from-registry-test.md",
            "class": "governance/system",
            "owner": "maintainers",
        }
    )
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    errors = check_docs(project)

    assert (
        f"{REGISTRY_PATH}: registered document does not exist: "
        "docs/missing-from-registry-test.md"
    ) in errors


def test_documentation_registry_guard_reports_duplicate_paths(tmp_path: Path) -> None:
    project = _copy_repo_subset(tmp_path)
    registry_path = project / REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["documents"].append(dict(registry["documents"][0]))
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    errors = check_documentation_registry(project)

    assert (
        f"{REGISTRY_PATH}: duplicate document path "
        "'docs/DOCUMENTATION_REGISTRY.yaml'"
    ) in errors


def test_documentation_registry_guard_reports_missing_class_rule_field(tmp_path: Path) -> None:
    project = _copy_repo_subset(tmp_path)
    registry_path = project / REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    del registry["class_rules"]["planning"]["freshness"]
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    errors = check_documentation_registry(project)

    assert f"{REGISTRY_PATH}: 'planning' missing class rule field 'freshness'" in errors


def test_docs_audit_cli_runs_with_documentation_registry() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-audit"])
    assert result.exit_code == 0
    assert "Documentation system audit" in result.output
